#!/usr/bin/env bash

# Run from .github/workflows/report-missing-server-translations.yml

set -euo pipefail

usage() {
    echo "Usage: $0 <python> <camcops_dir>"
    exit 1
}

if [ "$#" -lt 2 ]; then
    usage
fi

PYTHON=$1
CAMCOPS_DIR=$2

${PYTHON} "${CAMCOPS_DIR}/server/tools/build_server_translations.py" all

${CAMCOPS_DIR}/.github/scripts/check_git_changes.sh
