#!/usr/bin/env python3
"""Set (or change) the booking calendar's login password.

Run this from the app directory, e.g. via cPanel Terminal or SSH on the
production server, or locally for development:

    python3 set_password.py
"""

import getpass
import sys

from passenger_wsgi import get_db, hash_password


def main():
    password = getpass.getpass('New password: ')
    confirm = getpass.getpass('Confirm password: ')
    if password != confirm:
        print('Passwords do not match.', file=sys.stderr)
        sys.exit(1)
    if len(password) < 8:
        print('Password must be at least 8 characters.', file=sys.stderr)
        sys.exit(1)

    conn = get_db()
    conn.execute(
        'INSERT INTO settings (key, value) VALUES (?, ?) '
        'ON CONFLICT(key) DO UPDATE SET value = excluded.value',
        ('password_hash', hash_password(password)),
    )
    conn.commit()
    conn.close()
    print('Password updated.')


if __name__ == '__main__':
    main()
