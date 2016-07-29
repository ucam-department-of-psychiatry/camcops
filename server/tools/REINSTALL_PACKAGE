#!/bin/bash
set -e

TOOLDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
PACKAGEDIR=${TOOLDIR}/../packagebuild

PACKAGE=`ls -t ${PACKAGEDIR}/camcops*.deb | head -1` # NB takes most recent by file date
echo "REMOVING OLD CAMCOPS PACKAGE, IF INSTALLED"
sudo apt-get --yes remove camcops || echo "Wasn't installed"
echo "INSTALLING CAMCOPS PACKAGE: $PACKAGE"
sudo gdebi --non-interactive ${PACKAGE} # install package and dependencies
