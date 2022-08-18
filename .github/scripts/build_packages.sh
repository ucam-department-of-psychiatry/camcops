#!/usr/bin/env bash

# Run from .github/workflows/release.yml and push-to-repository.yml

set -eux -o pipefail
sudo apt-get -y install alien fakeroot lintian gdebi
# 429 = Too many requests. Unfortunately wget doesn't read the
# Retry-after header so just wait 5 minutes
wget --retry-on-http-error=429 --waitretry=300 --tries=20 https://downloads.sourceforge.net/project/rpmrebuild/rpmrebuild/2.15/rpmrebuild-2.15-1.noarch.rpm
fakeroot alien --to-deb rpmrebuild-2.15-1.noarch.rpm
sudo dpkg -i rpmrebuild_2.15-2_all.deb
python -m venv ${HOME}/venv
source ${HOME}/venv/bin/activate
python -VV
python -m site
python -m pip install -U pip
echo dumping pre-installed packages
python -m pip freeze
echo installing pip packages
python -m pip install -e server/.
echo building packages
server/tools/MAKE_LINUX_PACKAGES.py
