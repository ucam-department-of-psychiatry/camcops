#!/usr/bin/env python3
# tools/update_multiple_databases.py

import argparse
import glob
import os
import subprocess

THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PROJECT_BASE_DIRECTORY = os.path.abspath(os.path.join(THIS_DIRECTORY,
                                                      os.pardir))
DEFAULT_CAMCOPS = os.path.join(PROJECT_BASE_DIRECTORY, 'camcops.py')

DEFAULT_FILESPEC = '/etc/camcops/*'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Upgrade multiple CamCOPS databases")
    parser.add_argument(
        'filespecs', nargs='*', default=[DEFAULT_FILESPEC],
        help="List of CamCOPS config files (wildcards OK); default {}".format(
            DEFAULT_FILESPEC))
    parser.add_argument(
        '--camcops', default=DEFAULT_CAMCOPS,
        help="CamCOPS executable (default: {})".format(DEFAULT_CAMCOPS))
    parser.add_argument(
        '-d', '--dummyrun', action="store_true",
        help="Dummy run (show filenames only)")
    args = parser.parse_args()

    for filespec in args.filespecs:
        for filename in glob.glob(filespec):
            print("Processing: {}".format(filename))
            if args.dummyrun:
                continue
            subprocess.check_call([args.camcops, filename, '--maketables'])
