#!/usr/bin/env bash

# https://stackoverflow.com/questions/75536771/github-runner-out-of-disk-space-after-building-docker-image
set -eux -o pipefail

sudo docker rmi $(docker image ls -aq) >/dev/null 2>&1 || true
sudo rm -rf \
     /usr/share/dotnet /usr/local/lib/android /opt/ghc \
     /usr/local/share/powershell /usr/share/swift /usr/local/.ghcup \
     /usr/lib/jvm || true
echo "some directories deleted"
sudo apt install aptitude -y >/dev/null 2>&1
sudo aptitude purge aria2 ansible azure-cli shellcheck rpm xorriso zsync \
     esl-erlang firefox gfortran-8 gfortran-9 google-chrome-stable \
     google-cloud-sdk imagemagick \
     libmagickcore-dev libmagickwand-dev libmagic-dev ant ant-optional kubectl \
     mercurial apt-transport-https mono-complete libmysqlclient \
     unixodbc-dev yarn chrpath libssl-dev libxft-dev \
     snmp pollinate libpq-dev postgresql-client powershell ruby-full \
     sphinxsearch subversion mongodb-org azure-cli microsoft-edge-stable \
     -y -f >/dev/null 2>&1
sudo aptitude purge google-cloud-sdk -f -y >/dev/null 2>&1
sudo aptitude purge microsoft-edge-stable -f -y >/dev/null 2>&1 || true
sudo apt purge microsoft-edge-stable -f -y >/dev/null 2>&1 || true
sudo aptitude purge '~n ^mysql' -f -y >/dev/null 2>&1
sudo aptitude purge '~n ^php' -f -y >/dev/null 2>&1
sudo aptitude purge '~n ^dotnet' -f -y >/dev/null 2>&1
sudo apt-get autoremove -y >/dev/null 2>&1
sudo apt-get autoclean -y >/dev/null 2>&1
echo "some packages purged"

# Avoid pipefail by capturing output
big_packages=($(sudo dpkg-query -Wf '${Installed-Size}\t${Package}\n' | sort -nr))
echo ${big_packages[@]:0:20}
df . -h
usr_dirs=($(sudo du /usr/ -hx -d 4 --threshold=1G | sort -hr))
echo $(usr_dirs[@]:0:20}

sudo rm -rf ${GITHUB_WORKSPACE}/.git
