#-------------------------------------------------
#
# Project created by QtCreator 2016-05-30T22:51:39
#
#-------------------------------------------------

# SQLite/Android and OpenSSL/anything requires a custom Qt build.
# ALSO TRY:
#   qmake -query  # for the qmake of the Qt build you're using

# http://doc.qt.io/qt-5/qtmultimedia-index.html
# http://wiki.qt.io/Qt_5.5.0_Multimedia_Backends
# http://doc.qt.io/qt-4.8/qmake-variable-reference.html#qt
# http://doc.qt.io/qt-5/qtmodules.html

QT += core  # included by default; QtCore module
QT += gui  # included by default; QtGui module
QT += widgets  # required to #include <QApplication>
QT += sql  # required to #include <QSqlDatabase>
QT += network  # required to #include <QtNetwork/*>
QT += multimedia  # or: undefined reference to QMedia*::*
QT += multimediawidgets

# http://stackoverflow.com/questions/20351155/how-can-i-enable-ssl-in-qt-windows-application
# http://stackoverflow.com/questions/18663331/how-to-check-the-selected-version-of-qt-in-a-pro-file

TARGET = camcops_tablet
TEMPLATE = app


SOURCES += main.cpp\
    menulib/menu_window.cpp \
    menu/main_menu.cpp \
    lib/uifunc.cpp \
    menulib/menu_item.cpp \
    lib/filefunc.cpp \
    tasklib/taskfactory.cpp \
    tasklib/task.cpp \
    tasks/phq9.cpp \
    lib/databaseobject.cpp \
    lib/netcore.cpp \
    lib/dbfunc.cpp \
    lib/field.cpp \
    lib/datetimefunc.cpp \
    tests/master_test.cpp \
    menu/test_menu.cpp \
    tasklib/inittasks.cpp \
    common/camcops_app.cpp \
    tasklib/taskmainrecord.cpp

HEADERS  += \
    menulib/menu_window.h \
    menu/main_menu.h \
    menulib/menu_item.h \
    common/ui_constants.h \
    lib/uifunc.h \
    lib/filefunc.h \
    tasklib/taskfactory.h \
    tasklib/task.h \
    tasks/phq9.h \
    lib/databaseobject.h \
    lib/netcore.h \
    lib/dbfunc.h \
    lib/field.h \
    lib/datetimefunc.h \
    tests/master_test.h \
    menu/test_menu.h \
    tasklib/inittasks.h \
    common/db_constants.h \
    common/camcops_app.h \
    tasklib/taskmainrecord.h

CONFIG += debug
CONFIG += mobility
CONFIG += c++11
MOBILITY = 

RESOURCES += \
    camcops.qrc

DISTFILES += \
    notes/qt_notes.txt \
    stylesheets/camcops.css \
    stylesheets/camcops_menu.css \
    tools/build_qt.py \
    android/AndroidManifest.xml \
    android/gradle/wrapper/gradle-wrapper.jar \
    android/gradlew \
    android/res/values/libs.xml \
    android/build.gradle \
    android/gradle/wrapper/gradle-wrapper.properties \
    android/gradlew.bat


ANDROID_PACKAGE_SOURCE_DIR = $$PWD/android

#contains(ANDROID_TARGET_ARCH,x86) {
#    ANDROID_EXTRA_LIBS = \
#        $$PWD/../../../../dev/qt_local_build/openssl_android_x86_build/openssl-1.0.2h/libcrypto.so \
#        $$PWD/../../../../dev/qt_local_build/openssl_android_x86_build/openssl-1.0.2h/libssl.so
#}
#contains(ANDROID_TARGET_ARCH,armeabi-v7a) {
#    ANDROID_EXTRA_LIBS = \
#        $$PWD/../../../../dev/qt_local_build/openssl_android_arm_build/openssl-1.0.2h/libcrypto.so \
#        $$PWD/../../../../dev/qt_local_build/openssl_android_arm_build/openssl-1.0.2h/libssl.so
#}
