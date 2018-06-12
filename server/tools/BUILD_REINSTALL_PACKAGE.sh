#!/bin/bash
set -e

TOOLDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

echo "MAKING PACKAGE"
${TOOLDIR}/MAKE_PACKAGE.py
echo "REINSTALLING PACKAGE"
${TOOLDIR}/REINSTALL_PACKAGE.sh
