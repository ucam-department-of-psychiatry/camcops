#!/bin/bash

# Install cppclean with "pip install cppclean"; see https://pypi.python.org/pypi/cppclean

THISDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
BASEDIR=$THISDIR/..

find $BASEDIR -type f -name "*.cpp" -exec cppclean -i "$BASEDIR" {} \;
