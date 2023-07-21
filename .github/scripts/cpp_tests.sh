#!/bin/bash
set -euxo pipefail
export CAMCOPS_QT5_BASE_DIR=${RUNNER_WORKSPACE}
cd ${CAMCOPS_QT5_BASE_DIR}
mkdir -p eigen
cd eigen
EIGEN_VERSION=3.3.3
wget --retry-on-http-error=429 --waitretry=300 --tries=20 https://gitlab.com/libeigen/eigen/-/archive/${EIGEN_VERSION}/eigen-${EIGEN_VERSION}.tar.gz
tar xzf eigen-${EIGEN_VERSION}.tar.gz
cd ${GITHUB_WORKSPACE}
mkdir build-qt5-tests
cd build-qt5-tests
qmake ../tablet_qt/tests
make
export QT_DEBUG_PLUGINS=1

find . -path '*/bin/*' -type f -exec {} \;
