#!/bin/bash

THIS_SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

cd "$THIS_SCRIPT_DIR/.."

gunicorn camcops:application \
    --env CAMCOPS_CONFIG_FILE=/etc/camcops/camcops_py3_test.conf \
    --env CAMCOPS_DEBUG_TO_HTTP_CLIENT=True \
    --env MPLCONFIGDIR=$HOME/.matplotlib \
    --workers 1 \
    --reload \
    --bind=127.0.0.1:8000
