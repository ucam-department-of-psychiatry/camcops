#!/usr/bin/env python
# camcops_server/tools/launch_gunicorn_server.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
===============================================================================
"""

import argparse
import logging
import os
import subprocess

from camcops_server.cc_modules.cc_constants import ENVVAR_CONFIG_FILE
from camcops_server.cc_modules.cc_logger import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
HOME_DIR = os.path.expanduser('~')
DEFAULT_MATPLOTLIB_DIR = os.path.join(HOME_DIR, '.matplotlib')


def start_server(opts) -> None:
    cmdargs = [
        'gunicorn',
        'camcops_server.camcops:application',
        '--env', 'CAMCOPS_CONFIG_FILE={}'.format(opts.config),
        '--env', 'CAMCOPS_DEBUG_TO_HTTP_CLIENT=True',
        '--env', 'MPLCONFIGDIR={}'.format(opts.matplotlib),
        '--workers', '1',
        '--reload',
        '--bind={host}:{port}'.format(host=opts.host, port=opts.port),
    ]
    if opts.ssl_certificate and opts.ssl_private_key:
        cmdargs.extend([
            '--certfile', opts.ssl_certificate,
            '--keyfile', opts.ssl_private_key,
        ])
    subprocess.call(cmdargs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--host', type=str, default="127.0.0.1",
        help="hostname to listen on (default: 127.0.0.1)")
    parser.add_argument(
        '--port', type=int, default=8088,
        help="port to listen on (default: 8088)")
    parser.add_argument(
        '--matplotlib', type=str, default=DEFAULT_MATPLOTLIB_DIR,
        help="Matplotlib directory (default: {})".format(
            DEFAULT_MATPLOTLIB_DIR))
    parser.add_argument(
        '--ssl_certificate', type=str,
        help="SSL certificate file, for HTTPS")
    parser.add_argument(
        '--ssl_private_key', type=str,
        help="SSL key file, for HTTPS")
    parser.add_argument(
        '--config', type=str,
        default=os.environ.get(ENVVAR_CONFIG_FILE, ''),
        help="CamCOPS config file")
    opts = parser.parse_args()

    rootlogger = logging.getLogger()
    rootlogger.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)

    # Start the webserver
    log.info('starting server with options {}', opts)
    start_server(opts)


if __name__ == '__main__':
    main()
