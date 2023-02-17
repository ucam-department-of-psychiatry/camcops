#!/usr/bin/env bash

set -eux -o pipefail

python3 -m venv ${HOME}/venv
source ${HOME}/venv/bin/activate
python -VV
python -m site
python -m pip install -U pip
echo dumping pre-installed packages
python -m pip freeze
echo installing pip packages
python -m pip install -e server/.
