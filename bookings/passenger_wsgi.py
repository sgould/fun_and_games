#!/usr/bin/env python3
"""WSGI application for the booking calendar: serves the static frontend,
a small JSON API backed by SQLite, and password-based session auth.

Deployable under Passenger (cPanel "Setup Python App") since it exposes a
plain `application(environ, start_response)` callable, or locally via
server.py for development.
"""

import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import sqlite3
import time
from http.cookies import SimpleCookie

STATIC_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(STATIC_DIR, 'bookings.db')
VALID_STATUSES = {'school', 'public', 'available'}
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

SESSION_COOKIE = 'session'
SESSION_LIFETIME = 7 * 24 * 3600  # 7 days
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60
PBKDF2_ITERATIONS = 260000

_STATUS_LINES = {
    200: '200 OK',
    302: '302 Found',
    400: '400 Bad Request',
    401: '401 Unauthorized',
    404: '404 Not Found',
    429: '429 Too Many Requests',
    500: '500 Internal Server Error',
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS designations (
            date TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'free',
            comment TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            expires_at INTEGER NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            ip TEXT PRIMARY KEY,
            count INTEGER NOT NULL,
            locked_until INTEGER NOT NULL DEFAULT 0
        )
    ''')
    return conn


# ---- password hashing ----

def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f'pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}'


def verify_password(password, stored):
    try:
        _scheme, iterations, salt, hash_hex = stored.split('$')
        iterations = int(iterations)
    except (ValueError, AttributeError):
        return False
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), iterations)
    return hmac.compare_digest(digest.hex(), hash_hex)


# ---- session / auth helpers ----

def get_cookie_token(environ):
    raw = environ.get('HTTP_COOKIE')
    if not raw:
        return None
    cookie = SimpleCookie()
    cookie.load(raw)
    morsel = cookie.get(SESSION_COOKIE)
    return morsel.value if morsel else None


def is_authenticated(conn, environ):
    token = get_cookie_token(environ)
    if not token:
        return False
    row = conn.execute('SELECT expires_at FROM sessions WHERE token = ?', (token,)).fetchone()
    return bool(row) and row[0] >= int(time.time())


def create_session(conn):
    token = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + SESSION_LIFETIME
    conn.execute('INSERT INTO sessions (token, expires_at) VALUES (?, ?)', (token, expires_at))
    conn.execute('DELETE FROM sessions WHERE expires_at < ?', (int(time.time()),))
    return token, expires_at


def is_https(environ):
    return environ.get('wsgi.url_scheme') == 'https' or environ.get('HTTP_X_FORWARDED_PROTO') == 'https'


def session_cookie_header(environ, token, max_age):
    parts = [f'{SESSION_COOKIE}={token}', 'Path=/', 'HttpOnly', 'SameSite=Lax', f'Max-Age={max_age}']
    if is_https(environ):
        parts.append('Secure')
    return '; '.join(parts)


def clear_cookie_header(environ):
    parts = [f'{SESSION_COOKIE}=', 'Path=/', 'HttpOnly', 'SameSite=Lax', 'Max-Age=0']
    if is_https(environ):
        parts.append('Secure')
    return '; '.join(parts)


def client_ip(environ):
    forwarded = environ.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return environ.get('REMOTE_ADDR', 'unknown')


def check_lockout(conn, ip):
    now = int(time.time())
    row = conn.execute('SELECT locked_until FROM login_attempts WHERE ip = ?', (ip,)).fetchone()
    if row and row[0] > now:
        return row[0] - now
    return 0


def record_failed_attempt(conn, ip):
    now = int(time.time())
    row = conn.execute('SELECT count FROM login_attempts WHERE ip = ?', (ip,)).fetchone()
    count = (row[0] if row else 0) + 1
    locked_until = now + LOCKOUT_SECONDS if count >= MAX_LOGIN_ATTEMPTS else 0
    conn.execute(
        'INSERT INTO login_attempts (ip, count, locked_until) VALUES (?, ?, ?) '
        'ON CONFLICT(ip) DO UPDATE SET count = excluded.count, locked_until = excluded.locked_until',
        (ip, count, locked_until),
    )


def clear_attempts(conn, ip):
    conn.execute('DELETE FROM login_attempts WHERE ip = ?', (ip,))


# ---- response helpers ----

def _status_line(code):
    return _STATUS_LINES.get(code, f'{code} Error')


def json_response(start_response, obj, status=200, headers=None):
    body = json.dumps(obj).encode('utf-8')
    hdrs = [('Content-Type', 'application/json'), ('Content-Length', str(len(body)))]
    if headers:
        hdrs.extend(headers)
    start_response(_status_line(status), hdrs)
    return [body]


def file_response(start_response, path, headers=None):
    with open(path, 'rb') as f:
        body = f.read()
    content_type, _ = mimetypes.guess_type(path)
    hdrs = [('Content-Type', content_type or 'application/octet-stream'), ('Content-Length', str(len(body)))]
    if headers:
        hdrs.extend(headers)
    start_response(_status_line(200), hdrs)
    return [body]


def redirect_response(start_response, location):
    start_response('302 Found', [('Location', location), ('Content-Length', '0')])
    return [b'']


def serve_static(start_response, filename, headers=None):
    path = os.path.join(STATIC_DIR, filename)
    if not os.path.isfile(path):
        return json_response(start_response, {'error': 'not found'}, 404)
    return file_response(start_response, path, headers=headers)


def read_json_body(environ):
    try:
        length = int(environ.get('CONTENT_LENGTH', 0) or 0)
    except ValueError:
        length = 0
    raw = environ['wsgi.input'].read(length) if length else b''
    return json.loads(raw or b'{}')


def valid_dates(dates):
    return isinstance(dates, list) and dates and all(
        isinstance(d, str) and DATE_RE.match(d) for d in dates
    )


# ---- route handlers ----

def handle_login(environ, start_response, conn):
    ip = client_ip(environ)
    remaining = check_lockout(conn, ip)
    if remaining > 0:
        return json_response(start_response, {'error': f'Too many attempts. Try again in {remaining}s.'}, 429)

    try:
        payload = read_json_body(environ)
        password = payload['password']
    except (KeyError, ValueError, TypeError):
        return json_response(start_response, {'error': 'invalid payload'}, 400)

    row = conn.execute("SELECT value FROM settings WHERE key = 'password_hash'").fetchone()
    if not row:
        return json_response(start_response, {'error': 'no password has been set on the server'}, 500)

    if not isinstance(password, str) or not verify_password(password, row[0]):
        record_failed_attempt(conn, ip)
        conn.commit()
        return json_response(start_response, {'error': 'incorrect password'}, 401)

    clear_attempts(conn, ip)
    token, expires_at = create_session(conn)
    conn.commit()
    cookie_header = session_cookie_header(environ, token, SESSION_LIFETIME)
    return json_response(start_response, {'ok': True}, 200, headers=[('Set-Cookie', cookie_header)])


def handle_logout(environ, start_response, conn):
    token = get_cookie_token(environ)
    if token:
        conn.execute('DELETE FROM sessions WHERE token = ?', (token,))
        conn.commit()
    return json_response(start_response, {'ok': True}, 200, headers=[('Set-Cookie', clear_cookie_header(environ))])


def handle_get_days(start_response, conn):
    rows = conn.execute('SELECT date, status, comment FROM designations').fetchall()
    return json_response(start_response, {
        date: {'status': status, 'comment': comment}
        for date, status, comment in rows
    })


def handle_set_status(environ, start_response, conn):
    try:
        payload = read_json_body(environ)
        dates = payload['dates']
        status = payload['status']
    except (KeyError, ValueError, TypeError):
        return json_response(start_response, {'error': 'invalid payload'}, 400)

    if not valid_dates(dates):
        return json_response(start_response, {'error': 'dates must be a non-empty list of YYYY-MM-DD strings'}, 400)
    if status != 'free' and status not in VALID_STATUSES:
        return json_response(start_response, {'error': 'invalid status'}, 400)

    for d in dates:
        if status == 'free':
            row = conn.execute('SELECT comment FROM designations WHERE date = ?', (d,)).fetchone()
            if row and row[0]:
                conn.execute('UPDATE designations SET status = ? WHERE date = ?', ('free', d))
            else:
                conn.execute('DELETE FROM designations WHERE date = ?', (d,))
        else:
            conn.execute(
                'INSERT INTO designations (date, status) VALUES (?, ?) '
                'ON CONFLICT(date) DO UPDATE SET status = excluded.status',
                (d, status),
            )
    conn.commit()
    return json_response(start_response, {'ok': True})


def handle_set_comment(environ, start_response, conn):
    try:
        payload = read_json_body(environ)
        dates = payload['dates']
        comment = payload.get('comment', '')
    except (KeyError, ValueError, TypeError):
        return json_response(start_response, {'error': 'invalid payload'}, 400)

    if not valid_dates(dates) or not isinstance(comment, str):
        return json_response(start_response, {'error': 'invalid payload'}, 400)

    comment = comment.strip() or None

    for d in dates:
        row = conn.execute('SELECT status FROM designations WHERE date = ?', (d,)).fetchone()
        status = row[0] if row else 'free'
        if comment is None and status == 'free':
            conn.execute('DELETE FROM designations WHERE date = ?', (d,))
        else:
            conn.execute(
                'INSERT INTO designations (date, status, comment) VALUES (?, ?, ?) '
                'ON CONFLICT(date) DO UPDATE SET comment = excluded.comment',
                (d, status, comment),
            )
    conn.commit()
    return json_response(start_response, {'ok': True})


def application(environ, start_response):
    path = environ.get('PATH_INFO') or '/'
    method = environ.get('REQUEST_METHOD', 'GET')

    conn = get_db()
    try:
        if path == '/login.html' and method == 'GET':
            return serve_static(start_response, 'login.html')

        if path == '/api/login' and method == 'POST':
            return handle_login(environ, start_response, conn)

        if path == '/api/logout' and method == 'POST':
            return handle_logout(environ, start_response, conn)

        authed = is_authenticated(conn, environ)

        if path in ('/', '/index.html') and method == 'GET':
            if not authed:
                return redirect_response(start_response, '/login.html')
            return serve_static(start_response, 'index.html')

        if path == '/api/days' and method == 'GET':
            if not authed:
                return json_response(start_response, {'error': 'unauthorized'}, 401)
            return handle_get_days(start_response, conn)

        if path == '/api/days' and method == 'POST':
            if not authed:
                return json_response(start_response, {'error': 'unauthorized'}, 401)
            return handle_set_status(environ, start_response, conn)

        if path == '/api/comment' and method == 'POST':
            if not authed:
                return json_response(start_response, {'error': 'unauthorized'}, 401)
            return handle_set_comment(environ, start_response, conn)

        return json_response(start_response, {'error': 'not found'}, 404)
    finally:
        conn.close()
