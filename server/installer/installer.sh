#!/bin/bash


# server/installer/installer.sh

# ===============================================================================

#     Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
#     Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

#     This file is part of CamCOPS.

#     CamCOPS is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     CamCOPS is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

# ===============================================================================

# Installs CamCOPS running under Docker with demonstration databases.
# Do as little as possible in this script.
# Do as much as possible in installer.py.

set -eux -o pipefail

# - Prerequisites for Windows:
#   - Install WSL2
#   - Install Docker Desktop for Windows
#   - Enable WSL2 in Docker Desktop
#
# - Prerequisites for Ubuntu:
#     sudo apt-get update
#     sudo apt -y install python3-virtualenv python3-venv
#
# - Prerequisites for RHEL:

# When called with no arguments, the installation process is as in docker.rst
# With the -d (development) option, the installer runs on the local copy of the
# source code.

INSTALLER_ARGS=()
PRODUCTION=1
RECREATE_VIRTUALENV=0

usage() {
    cat <<EOF
    Usage: $(basename $0) [options]

    -d Development. Run installer on local copy of code instead of
       downloading from GitHub.
    -h Display this help message.
    -n Recreate the installer virtual environment.
    -u Upgrade existing CamCOPS installation.
EOF
}


while getopts 'dhnu' OPT; do
  case "$OPT" in
    d)
        PRODUCTION=0
        ;;
    h)
        usage
        exit 0
        ;;
    n)
        RECREATE_VIRTUALENV=1
        ;;
    u)
        INSTALLER_ARGS+=(--update)
        RECREATE_VIRTUALENV=1
        ;;
    *)
        usage
        exit 1
        ;;
  esac
done

INSTALLER_ARGS+=("install")

# -----------------------------------------------------------------------------
# Directories
# -----------------------------------------------------------------------------
CAMCOPS_INSTALLER_VENV=${HOME}/.virtualenvs/camcops_installer

if [ ${PRODUCTION} -eq 1 ]; then
    CAMCOPS_HOME=${HOME}/camcops
    INSTALLER_HOME=${CAMCOPS_HOME}/server/installer
else
    INSTALLER_HOME="$( cd "$( dirname "$0" )" && pwd )"
fi

# -----------------------------------------------------------------------------
# System Python to use
# -----------------------------------------------------------------------------

CAMCOPS_INSTALLER_PYTHON=${CAMCOPS_INSTALLER_PYTHON:-python3}

# -----------------------------------------------------------------------------
# Fetching CamCOPS and boostrap the installer
# -----------------------------------------------------------------------------

if [ ${PRODUCTION} -eq 1 ]; then
    CAMCOPS_GITHUB_REPOSITORY=https://github.com/ucam-department-of-psychiatry/camcops
    CAMCOPS_TAR_FILE=camcops_server.tar.gz

    # This doesn't work with GitHub generated assets for some reason so we rely
    # on the "release" GitHub action (.github/workflows/release.yml) to create
    # and upload the tar file so that it can be accessed as "latest".
    CAMCOPS_DOWNLOAD_URL=${CAMCOPS_GITHUB_REPOSITORY}/releases/latest/download/${CAMCOPS_TAR_FILE}

    if [ -d "${CAMCOPS_HOME}" ]; then
        mv "${CAMCOPS_HOME}" "${CAMCOPS_HOME}.renamed.$(date +%Y%m%d%H%M%S)"
    fi

    # Make directories
    mkdir -p "${CAMCOPS_HOME}"

    # Fetch and unpack CamCOPS
    cd "${CAMCOPS_HOME}"
    curl -L --retry 10 --fail "${CAMCOPS_DOWNLOAD_URL}"  --output "${CAMCOPS_TAR_FILE}"
    tar xzf "${CAMCOPS_TAR_FILE}" --strip-components=1
fi


# Create virtual environment
if [ ${RECREATE_VIRTUALENV} -eq 1 ]; then
    rm -rf "${CAMCOPS_INSTALLER_VENV}"
fi

if [ ! -d "${CAMCOPS_INSTALLER_VENV}" ]; then
    "${CAMCOPS_INSTALLER_PYTHON}" -m venv "${CAMCOPS_INSTALLER_VENV}"
fi

# Activate virtual environment
source "${CAMCOPS_INSTALLER_VENV}/bin/activate"

# Check virtual environment
PYTHON_VERSION_OK=$(python -c 'import sys; print(sys.version_info.major >=3 and sys.version_info.minor >= 10)')
if [ "${PYTHON_VERSION_OK}" == "False" ]; then
    python --version
    echo "You need at least Python 3.10 to run the installer."
    exit 1
fi

# Install a few packages
python -m pip install -U pip setuptools
python -m pip install -r "${INSTALLER_HOME}/installer_requirements.txt"

# Run the Python installer
python "${INSTALLER_HOME}/installer.py" ${INSTALLER_ARGS[*]}
