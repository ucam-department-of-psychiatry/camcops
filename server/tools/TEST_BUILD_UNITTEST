#!/bin/bash

TOOLDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

TESTCONF=/etc/camcops/camcops_dev.conf

${TOOLDIR}/MAKE_PACKAGE \
    && ${TOOLDIR}/REINSTALL_PACKAGE \
    && sudo camcops_db ${TESTCONF} \
    && sudo camcops -x ${TESTCONF} \
    && sudo camcops -7 ${TESTCONF}
