#!/bin/bash

# This isn't quite right, probably better to fix the RPM

set -eux -o pipefail

cd ${HOME}
sudo service supervisord stop
# Because of https://github.com/ucam-department-of-psychiatry/camcops/issues/284
sudo dnf -y remove camcops-server
sudo rm -r /usr/share/camcops

sudo wget https://github.com/ucam-department-of-psychiatry/camcops/releases/download/${TAG}/${RPM}
sudo dnf -y install ${RPM}

sudo service supervisord stop
source /usr/share/camcops/venv/bin/activate
sudo /usr/share/camcops/venv/bin/python -m pip install mysqlclient
sudo camcops_server upgrade_db --config /etc/camcops/camcops.conf
sudo service supervisord start
