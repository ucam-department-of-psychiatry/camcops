#!/bin/bash
set -e

TOOLDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

echo "MAKING LINUX PACKAGES"
"${TOOLDIR}/MAKE_LINUX_PACKAGES.py" --verbose
echo "REINSTALLING DEBIAN PACKAGE"
"${TOOLDIR}/REINSTALL_DEBIAN_PACKAGE.sh"
