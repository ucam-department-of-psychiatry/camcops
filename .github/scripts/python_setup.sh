#!/usr/bin/env bash

set -euo pipefail

python3 -m venv ${HOME}/venv
PYTHON=${HOME}/venv/bin/python
${PYTHON} -VV
${PYTHON} -m site
${PYTHON} -m pip install -U pip setuptools
echo dumping pre-installed packages
${PYTHON} -m pip freeze
echo installing pip packages
${PYTHON} -m pip install -e server/.
