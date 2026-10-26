"""Serve the cube scanner on localhost and open it in the browser.

Browsers only allow webcam access and ES modules from a real origin, so the
page has to be served rather than opened as a file. localhost counts as secure.
"""
import functools
import http.server
import pathlib
import threading
import webbrowser

PORT = 8765
ROOT = pathlib.Path(__file__).parent

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
url = f"http://localhost:{PORT}/"
print(f"Serving {ROOT} at {url}  (Ctrl+C to stop)")
threading.Timer(0.5, webbrowser.open, args=[url]).start()
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
