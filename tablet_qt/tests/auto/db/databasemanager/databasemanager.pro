CONFIG += testcase
QT += network
QT += sql
QT += testlib
QT += widgets
QT -= gui

TARGET = bin/test_databasemanager

OBJ_EXT = ".o"  # unless otherwise set

linux: !android {
    contains(QT_ARCH, x86_64) {
        CAMCOPS_ARCH_TAG = "linux_x86_64"
    }
}

isEmpty(CAMCOPS_ARCH_TAG) {
    error("Unsupported architecture for Qt tests.")
}

DEFINES += SQLITE_HAS_CODEC
DEFINES += SQLITE_TEMP_STORE=2

SQLCIPHER_DIR = "$${QT_BASE_DIR}/sqlcipher_$${CAMCOPS_ARCH_TAG}"

message("Using SQLCipher from $${SQLCIPHER_DIR}")
INCLUDEPATH += "$${SQLCIPHER_DIR}"  # from which: <sqlcipher/sqlite3.h>
LIBS += "$${SQLCIPHER_DIR}/sqlcipher/sqlite3$${OBJ_EXT}"  # add .o file

SOURCES += \
    testdatabasemanager.cpp \
    $$CAMCOPS_SRC/common/dpi.cpp \
    $$CAMCOPS_SRC/common/textconst.cpp \
    $$CAMCOPS_SRC/common/uiconst.cpp \
    $$CAMCOPS_SRC/db/databasemanager.cpp \
    $$CAMCOPS_SRC/db/databaseworkerthread.cpp \
    $$CAMCOPS_SRC/db/dbfunc.cpp \
    $$CAMCOPS_SRC/db/field.cpp \
    $$CAMCOPS_SRC/db/fieldcreationplan.cpp \
    $$CAMCOPS_SRC/db/queryresult.cpp \
    $$CAMCOPS_SRC/db/sqlargs.cpp \
    $$CAMCOPS_SRC/db/sqlcachedresult.cpp \
    $$CAMCOPS_SRC/db/sqlcipherdriver.cpp \
    $$CAMCOPS_SRC/db/sqlcipherhelpers.cpp \
    $$CAMCOPS_SRC/db/sqlcipherresult.cpp \
    $$CAMCOPS_SRC/db/sqlitepragmainfofield.cpp \
    $$CAMCOPS_SRC/db/threadedqueryrequest.cpp \
    $$CAMCOPS_SRC/db/whereconditions.cpp \
    $$CAMCOPS_SRC/db/whichdb.cpp \
    $$CAMCOPS_SRC/lib/convert.cpp \
    $$CAMCOPS_SRC/lib/customtypes.cpp \
    $$CAMCOPS_SRC/lib/datetime.cpp \
    $$CAMCOPS_SRC/lib/errorfunc.cpp \
    $$CAMCOPS_SRC/lib/filefunc.cpp \
    $$CAMCOPS_SRC/lib/stringfunc.cpp \
    $$CAMCOPS_SRC/lib/version.cpp \
    $$CAMCOPS_SRC/maths/mathfunc.cpp


HEADERS += \
    $$CAMCOPS_SRC/common/dpi.h \
    $$CAMCOPS_SRC/common/textconst.h \
    $$CAMCOPS_SRC/common/uiconst.h \
    $$CAMCOPS_SRC/db/databasemanager.h \
    $$CAMCOPS_SRC/db/databaseworkerthread.h \
    $$CAMCOPS_SRC/db/dbfunc.h \
    $$CAMCOPS_SRC/db/field.h \
    $$CAMCOPS_SRC/db/fieldcreationplan.h \
    $$CAMCOPS_SRC/db/queryresult.h \
    $$CAMCOPS_SRC/db/sqlargs.h \
    $$CAMCOPS_SRC/db/sqlcachedresult.h \
    $$CAMCOPS_SRC/db/sqlcipherdriver.h \
    $$CAMCOPS_SRC/db/sqlcipherhelpers.h \
    $$CAMCOPS_SRC/db/sqlcipherresult.h \
    $$CAMCOPS_SRC/db/sqlitepragmainfofield.h \
    $$CAMCOPS_SRC/db/threadedqueryrequest.h \
    $$CAMCOPS_SRC/db/whereconditions.h \
    $$CAMCOPS_SRC/db/whichdb.h \
    $$CAMCOPS_SRC/lib/convert.h \
    $$CAMCOPS_SRC/lib/customtypes.h \
    $$CAMCOPS_SRC/lib/datetime.h \
    $$CAMCOPS_SRC/lib/errorfunc.h \
    $$CAMCOPS_SRC/lib/filefunc.h \
    $$CAMCOPS_SRC/lib/stringfunc.h \
    $$CAMCOPS_SRC/lib/version.h \
    $$CAMCOPS_SRC/maths/mathfunc.h

INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
