#!/bin/bash
set -e

TOOLDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
PACKAGEDIR=${TOOLDIR}/../packagebuild

# PACKAGE=$(ls -t ${PACKAGEDIR}/camcops*.deb | head -1)
# ... NB takes most recent by file date; "ls -t" sorts by modification time.
# BUT linter warning:
# ... "Use find instead of ls to better handle non-alphanumeric filenames."
# https://unix.stackexchange.com/questions/29899/how-can-i-use-find-and-sort-the-results-by-mtime
PACKAGE=$(find "${PACKAGEDIR}" -name "camcops*.deb" -printf "%T+\t%p\n" | sort | tail -1 | awk 'BEGIN { FS = "\t" }; { print $2 }')
# - The "%T" prints the file's last modification time. "%T+" gives date and
#   time separated by "+". The \t gives a tab; %p is the full path.
# - The sort gives ascending order, so "tail -1" takes the last.
# - The awk command removes the date and prints the filename.

echo "REMOVING OLD CAMCOPS PACKAGE, IF INSTALLED"
sudo apt-get --yes remove camcops camcops-server || echo "camcops-server package wasn't installed"
echo "INSTALLING CAMCOPS PACKAGE: $PACKAGE"
sudo gdebi --non-interactive "${PACKAGE}"  # install package and dependencies
