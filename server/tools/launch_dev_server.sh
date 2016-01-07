#!/bin/bash

gunicorn camcops:application \
    --env CAMCOPS_CONFIG_FILE=/etc/camcops/camcops_py3_test.conf \
    --workers 2 \
    --bind=127.0.0.1:8000
