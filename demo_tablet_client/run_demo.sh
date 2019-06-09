#!/bin/bash

# Merely a convenience script. Copy a recent version of camcops to this directory.
# It's to allow a demo to be run whilst the main copy is broken for development!

THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export LD_LIBRARY_PATH=/home/rudolf/dev/qt_local_build/openssl_linux_x86_64_build/openssl-1.1.0g
$THISDIR/camcops
