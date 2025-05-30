#!/bin/bash
set -euxo pipefail
echo "Running C++ tests..."
echo "CAMCOPS_QT6_BASE_DIR=${CAMCOPS_QT6_BASE_DIR}"
cd ${GITHUB_WORKSPACE}
mkdir build-qt6-tests
cd build-qt6-tests
${CAMCOPS_QT6_BASE_DIR}/qt_linux_x86_64_install/bin/qmake -query
${CAMCOPS_QT6_BASE_DIR}/qt_linux_x86_64_install/bin/qmake ../tablet_qt/tests
make
export QT_DEBUG_PLUGINS=1

PYTHON=${HOME}/venv/bin/python
${PYTHON} ${GITHUB_WORKSPACE}/tablet_qt/tools/run_cpp_tests.py --testroot .
