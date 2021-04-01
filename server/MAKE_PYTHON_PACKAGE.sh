#!/bin/bash
# MAKE_PYTHON_PACKAGE.sh

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

python "${THIS_DIR}/setup.py" sdist
