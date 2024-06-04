#!/bin/bash
set -euxo pipefail
export CAMCOPS_QT6_BASE_DIR=${RUNNER_WORKSPACE}
cd ${GITHUB_WORKSPACE}
mkdir build-qt6-tests
cd build-qt6-tests
qmake ../tablet_qt/tests
make
export QT_DEBUG_PLUGINS=1

find . -path '*/bin/*' -type f -exec {} \;
