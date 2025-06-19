#!/usr/bin/env bash

# Run from .github/workflows/report-missing-client-translations.yml

set -euo pipefail

usage() {
    echo "Usage: $0 <camcops_dir> <qt_bin_dir>"
    exit 1
}

if [ "$#" -lt 2 ]; then
    usage
fi

CAMCOPS_DIR=$1
QT_BIN_DIR=$2

PYTHON=${HOME}/venv/bin/python

export PATH=${PATH}:${QT_BIN_DIR}

which lconvert
which lrelease
which lupdate

${PYTHON} "${CAMCOPS_DIR}/tablet_qt/tools/build_client_translations.py" all
${PYTHON} "${CAMCOPS_DIR}/tablet_qt/tools/build_client_translations.py" missing
