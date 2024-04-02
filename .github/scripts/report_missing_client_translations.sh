#!/usr/bin/env bash

# Run from .github/workflows/report-missing-client-translations.yml

set -euxo pipefail

ls ${QT_ROOT_DIR}
export QT_BIN_DIR=${QT_ROOT_DIR}/gcc_64/bin
ls ${QT_BIN_DIR}
export LCONVERT=${QT_BIN_DIR}/lconvert
export LRELEASE=${QT_BIN_DIR}/lrelease
export LUPDATE=${QT_BIN_DIR}/lupdate

PYTHON=${HOME}/venv/bin/python
${PYTHON} ${GITHUB_WORKSPACE}/tablet_qt/tools/build_client_translations.py all
${PYTHON} ${GITHUB_WORKSPACE}/tablet_qt/tools/build_client_translations.py missing
