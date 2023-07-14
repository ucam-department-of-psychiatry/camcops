#!/bin/bash
set -euxo pipefail
export CAMCOPS_QT6_BASE_DIR=${RUNNER_WORKSPACE}
cd ${CAMCOPS_QT6_BASE_DIR}
mkdir -p eigen
cd eigen
EIGEN_VERSION=3.4.0
wget --retry-on-http-error=429 --waitretry=300 --tries=20 https://gitlab.com/libeigen/eigen/-/archive/${EIGEN_VERSION}/eigen-${EIGEN_VERSION}.tar.gz
tar xzf eigen-${EIGEN_VERSION}.tar.gz
cd ${GITHUB_WORKSPACE}/tablet_qt/tests
qmake
make
export QT_DEBUG_PLUGINS=1

find . -path '*/bin/*' -type f -exec {} \;
