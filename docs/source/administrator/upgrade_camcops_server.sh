#!/usr/bin/env bash
# upgrade_camcops_server.sh
#
# Upgrade a CamCOPS server installation under Linux.

# =============================================================================
# Bash settings
# =============================================================================

# Exit on error
set -e

# Use case-insensitive regular expressions (=~ syntax)
shopt -s nocasematch

# =============================================================================
# Choose a version here. See https://github.com/RudolfCardinal/camcops/releases
# =============================================================================

LATEST_VERSION=$(camcops_print_latest_github_version)
CAMCOPS_VERSION=${LATEST_VERSION}
echo "Chosen CamCOPS version: ${CAMCOPS_VERSION}"

# =============================================================================
# Check the user means it
# =============================================================================

read -p "WILL DOWNLOAD/INSTALL CAMCOPS VERSION ${CAMCOPS_VERSION}; OK? " -n 1 -r
if [[ ! ${REPLY} =~ ^[Yy]$ ]]
then
    exit 1
fi
echo

# =============================================================================
# Calculate filenames and URLS
# =============================================================================

# Filenames:
CAMCOPS_SERVER_DEB=camcops-server_${CAMCOPS_VERSION}-1_all.deb
CAMCOPS_SERVER_RPM=camcops-server_${CAMCOPS_VERSION}-2.noarch.rpm
# CAMCOPS_CLIENT_WINDOWS=camcops_${CAMCOPS_VERSION}_windows.exe

# URLs:
GITHUB_URL=https://github.com/RudolfCardinal/camcops
DOWNLOAD_URL=${GITHUB_URL}/releases/download/v${CAMCOPS_VERSION}
URL_SERVER_DEB=${DOWNLOAD_URL}/${CAMCOPS_SERVER_DEB}
URL_SERVER_RPM=${DOWNLOAD_URL}/${CAMCOPS_SERVER_RPM}
# URL_CLIENT_WINDOWS=${DOWNLOAD_URL}/${CAMCOPS_CLIENT_WINDOWS}

# =============================================================================
# Detect OS; download, remove old installation, and install new
# =============================================================================
# ... https://askubuntu.com/questions/459402/how-to-know-if-the-running-platform-is-ubuntu-or-centos-with-help-of-a-bash-scri
# ... https://unix.stackexchange.com/questions/132480/case-insensitive-substring-search-in-a-shell-script
# ... https://stackoverflow.com/questions/229551/how-to-check-if-a-string-contains-a-substring-in-bash

PLATFORM=$(python -m platform)
# ... works for Python 2 and up
echo "Platform: ${PLATFORM}"
# Regular expressions for different operating systems:
DEBIAN_RE="Debian|Ubuntu"
CENTOS_RE="CentOS"

if [[ $PLATFORM =~ $DEBIAN_RE ]]; then

    echo "Detected Debian Linux"
    wget "${URL_SERVER_DEB}" -O "${CAMCOPS_SERVER_DEB}"
    sudo apt-get --yes remove camcops-server
    sudo gdebi --non-interactive "${CAMCOPS_SERVER_DEB}"

elif [[ $PLATFORM =~ $CENTOS_RE ]]; then

    echo "Detected CentOS Linux"
    wget "${URL_SERVER_RPM}" -O "${CAMCOPS_SERVER_RPM}"
    sudo yum --assumeyes remove camcops-server
    sudo yum --assumeyes --verbose --rpmverbosity=DEBUG install "${CAMCOPS_SERVER_RPM}"

else

    echo "Unknown operating system!"
    exit 1

fi
