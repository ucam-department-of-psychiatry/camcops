#!/usr/bin/env bash

# Run from .github/workflows/report-missing-client-translations.yml

set -euxo pipefail

which lconvert

PYTHON=${HOME}/venv/bin/python
${PYTHON} ${GITHUB_WORKSPACE}/tablet_qt/tools/build_client_translations.py all
${PYTHON} ${GITHUB_WORKSPACE}/tablet_qt/tools/build_client_translations.py missing
