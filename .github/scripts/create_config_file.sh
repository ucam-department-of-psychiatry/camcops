#!/usr/bin/env bash
set -euxo pipefail

# Because of -u above, this will abort the script if CAMCOPS_CONFIG_FILE is
# undefined_
echo "Writing configuration to ${CAMCOPS_CONFIG_FILE}"
camcops_server demo_camcops_config | sed 's/YYY_USERNAME_REPLACE_ME/camcops/g' | sed 's/ZZZ_PASSWORD_REPLACE_ME/camcops/g' > "${CAMCOPS_CONFIG_FILE}"
