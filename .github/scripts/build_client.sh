#!/bin/bash
set -euxo pipefail
export CAMCOPS_QT6_BASE_DIR=${RUNNER_WORKSPACE}

cd ${CAMCOPS_QT6_BASE_DIR}
mkdir -p eigen
cd eigen
EIGEN_VERSION_FILE=${GITHUB_WORKSPACE}/tablet_qt/eigen_version.txt
EIGEN_VERSION=$(<$EIGEN_VERSION_FILE)
wget --retry-on-http-error=429 --waitretry=300 --tries=20 https://gitlab.com/libeigen/eigen/-/archive/${EIGEN_VERSION}/eigen-${EIGEN_VERSION}.tar.gz
tar xzf eigen-${EIGEN_VERSION}.tar.gz

# See also tablet_qt/tools/build_qt.py build_openssl()
OPENSSL_VERSION_FILE=${GITHUB_WORKSPACE}/tablet_qt/openssl_version.txt
OPENSSL_VERSION=$(<$OPENSSL_VERSION_FILE)
cd ${CAMCOPS_QT6_BASE_DIR}
OPENSSL_DIR=${CAMCOPS_QT6_BASE_DIR}/openssl_linux_x86_64/openssl-${OPENSSL_VERSION}
mkdir -p ${OPENSSL_DIR}
cd ${OPENSSL_DIR}
wget --retry-on-http-error=429 --waitretry=300 --tries=20 https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz
tar xzf openssl-${OPENSSL_VERSION}.tar.gz
cd openssl-${OPENSSL_VERSION}

perl Configure linux-x86_64 --prefix=/ shared no-ssl3 no-shared
make

BUILD_DIR=${GITHUB_WORKSPACE}/build-camcops-Linux_Qt6_5
mkdir ${BUILD_DIR}
cd ${BUILD_DIR}
qmake ../tablet_qt
make
