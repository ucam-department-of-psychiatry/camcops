#!/usr/bin/env bash
set -euxo pipefail

export CAMCOPS_CONFIG_FILE="${HOME}/camcops.cfg"
camcops_server demo_camcops_config | sed 's/YYY_USERNAME_REPLACE_ME/camcops/g' | sed 's/ZZZ_PASSWORD_REPLACE_ME/camcops/g' > "${CAMCOPS_CONFIG_FILE}"
