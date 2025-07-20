#!/bin/bash
set -euo pipefail
echo "Building client..."
echo "CAMCOPS_QT6_BASE_DIR=${CAMCOPS_QT6_BASE_DIR}"
cd "${GITHUB_WORKSPACE}"

QMAKE=${CAMCOPS_QT6_BASE_DIR}/qt_linux_x86_64_install/bin/qmake
${QMAKE} -query

BUILD_DIR=${GITHUB_WORKSPACE}/build-camcops-Linux_Qt6_5
mkdir "${BUILD_DIR}"
cd "${BUILD_DIR}"

${QMAKE} ../tablet_qt
make
