#!/bin/bash

set -eux -o pipefail

cd ${HOME}

sudo wget https://github.com/ucam-department-of-psychiatry/camcops/releases/download/${TAG}/${DEB}
sudo gdebi ${DEB}

sudo service supervisor stop
source /usr/share/camcops/venv/bin/activate
sudo /usr/share/camcops/venv/bin/python -m pip install mysqlclient
sudo camcops_server upgrade_db --config /etc/camcops/camcops.conf
sudo service supervisord start
