#!/bin/bash
# MAKE_PYTHON_PACKAGE.sh

set -euo pipefail

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "${THIS_DIR}"
python -m build
