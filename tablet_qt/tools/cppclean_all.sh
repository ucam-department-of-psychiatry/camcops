#!/bin/bash

if ! which cppclean >/dev/null; then
    echo 'Install cppclean with "pip install cppclean"; see https://pypi.python.org/pypi/cppclean'
    exit 1
fi

THISDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
BASEDIR=$THISDIR/..

find $BASEDIR -type f -name "*.cpp" -exec cppclean -i "$BASEDIR" {} \;
