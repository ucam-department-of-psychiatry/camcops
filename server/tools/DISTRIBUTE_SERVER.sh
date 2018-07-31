#!/bin/bash

TOOLDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
PACKAGEDIR=${TOOLDIR}/../packagebuild

SERVERDOWNLOADDIR=/srv/www/camcops/download/server

echo "COPYING PACKAGES TO DOWNLOAD AREA"
cp -v ${PACKAGEDIR}/* ${SERVERDOWNLOADDIR}
