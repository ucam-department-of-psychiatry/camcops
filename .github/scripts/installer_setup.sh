#!/usr/bin/env bash

# Run from .github/workflows/installer.yml

set -euxo pipefail

sudo apt-get update -o APT::Update::Error-Mode=any
sudo apt -y install python3-virtualenv python3-venv wait-for-it

sudo mkdir /camcops
sudo chown "$(id -u -n)" /camcops
