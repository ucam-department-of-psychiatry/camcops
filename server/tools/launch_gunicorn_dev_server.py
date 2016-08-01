#!/usr/bin/env python

import os
import subprocess

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    args = [
        'gunicorn',
        'camcops_server.camcops:application',
        '--env', 'CAMCOPS_CONFIG_FILE=/etc/camcops/camcops_py3_test.conf',
        '--env', 'CAMCOPS_DEBUG_TO_HTTP_CLIENT=True',
        '--env', 'MPLCONFIGDIR=$HOME/.matplotlib', # TODO: fix!
        '--workers', '1',
        '--reload',
        '--bind=127.0.0.1:8000',
    ]
    subprocess.call(args)

if __name__ == '__main__':
    main()