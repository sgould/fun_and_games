#!/usr/bin/env python3
"""Local development launcher.

Production deployment (e.g. GoDaddy cPanel's "Setup Python App") runs
passenger_wsgi.py directly under Passenger. This script runs the exact
same WSGI app with Python's built-in dev server, for local testing.
"""

import os
from wsgiref.simple_server import make_server

from passenger_wsgi import application


def main():
    port = int(os.environ.get('PORT', 8080))
    print(f'Booking calendar server running at http://localhost:{port}')
    try:
        make_server('0.0.0.0', port, application).serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
