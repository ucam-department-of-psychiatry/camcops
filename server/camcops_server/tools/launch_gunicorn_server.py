#!/usr/bin/env python

import argparse
import logging
import os
import subprocess

log = logging.getLogger(__name__)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
HOME_DIR = os.path.expanduser('~')
DEFAULT_MATPLOTLIB_DIR = os.path.join(HOME_DIR, '.matplotlib')


def start_server(opts) -> None:
    cmdargs = [
        'gunicorn',
        'camcops_server.camcops:application',
        '--env', 'CAMCOPS_CONFIG_FILE=/etc/camcops/camcops_py3_test.conf',
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
    opts = parser.parse_args()

    rootlogger = logging.getLogger()
    rootlogger.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)

    # Start the webserver
    log.info('starting server with options {}'.format(opts))
    start_server(opts)


if __name__ == '__main__':
    main()
