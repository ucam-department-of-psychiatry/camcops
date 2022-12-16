#!/usr/bin/env bash

# https://wiki.qt.io/Building_Qt_6_from_Git
set -eux -o pipefail
codename=`lsb_release -cs`
echo "deb-src http://archive.ubuntu.com/ubuntu ${codename} universe" | sudo tee -a /etc/apt/sources.list
echo "deb-src http://archive.ubuntu.com/ubuntu ${codename}-updates universe" | sudo tee -a /etc/apt/sources.list
sudo apt-get update
