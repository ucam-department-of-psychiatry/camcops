#!/usr/bin/env bash

# Run from .github/workflows/report-missing-client-translations.yml

set -euxo pipefail

export QT6_BASE_DIR=${RUNNER_WORKSPACE}/Qt
ls ${QT6_BASE_DIR}
export QT6_BIN_DIR=${QT6_BASE_DIR}/gcc_64/bin
ls ${QT6_BIN_DIR}
export LCONVERT=${QT6_BIN_DIR}/lconvert
export LRELEASE=${QT6_BIN_DIR}/lrelease
export LUPDATE=${QT6_BIN_DIR}/lupdate

PYTHON=${HOME}/venv/bin/python
${PYTHON} ${GITHUB_WORKSPACE}/tablet_qt/tools/build_client_translations.py all
${PYTHON} ${GITHUB_WORKSPACE}/tablet_qt/tools/build_client_translations.py missing
