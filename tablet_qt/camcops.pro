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
# QT += webkit  # for QWebView -- no, not used
# QT += webkitwidgets  # for QWebView -- no, not used

# http://stackoverflow.com/questions/20351155/how-can-i-enable-ssl-in-qt-windows-application
# http://stackoverflow.com/questions/18663331/how-to-check-the-selected-version-of-qt-in-a-pro-file

QMAKE_CXXFLAGS += -Werror  # warnings become errors

TARGET = camcops
TEMPLATE = app


SOURCES += main.cpp\
    lib/uifunc.cpp \
    lib/filefunc.cpp \
    tasklib/taskfactory.cpp \
    tasklib/task.cpp \
    tasks/phq9.cpp \
    lib/databaseobject.cpp \
    lib/netcore.cpp \
    lib/dbfunc.cpp \
    lib/field.cpp \
    lib/datetimefunc.cpp \
    tasklib/inittasks.cpp \
    menulib/menuheader.cpp \
    menulib/menuitem.cpp \
    menulib/menuwindow.cpp \
    questionnairelib/namevaluepair.cpp \
    lib/fieldref.cpp \
    menu/mainmenu.cpp \
    menu/testmenu.cpp \
    common/camcopsapp.cpp \
    menu/affectivemenu.cpp \
    common/dbconstants.cpp \
    menu/addictionmenu.cpp \
    menu/anonymousmenu.cpp \
    menu/alltasksmenu.cpp \
    menu/catatoniaepsemenu.cpp \
    menu/clinicalmenu.cpp \
    menu/clinicalsetsmenu.cpp \
    menu/cognitivemenu.cpp \
    menu/executivemenu.cpp \
    menu/globalmenu.cpp \
    menu/helpmenu.cpp \
    menu/personalitymenu.cpp \
    menu/psychosismenu.cpp \
    menu/researchmenu.cpp \
    menu/researchsetsmenu.cpp \
    menu/settingsmenu.cpp \
    menu/whiskermenu.cpp \
    menu/setmenucpftaffective1.cpp \
    menu/setmenudeakin1.cpp \
    menu/setmenufromlp.cpp \
    menu/setmenuobrien1.cpp \
    common/platform.cpp \
    menu/singletaskmenu.cpp \
    menu/patientsummarymenu.cpp \
    questionnairelib/questionnaireheader.cpp \
    tasks/demoquestionnaire.cpp \
    questionnairelib/questionnaire.cpp \
    common/uiconstants.cpp \
    questionnairelib/quelement.cpp \
    questionnairelib/qupage.cpp \
    questionnairelib/qutext.cpp \
    widgets/verticalscrollarea.cpp \
    widgets/labelwordwrapwide.cpp \
    questionnairelib/qubutton.cpp \
    menulib/htmlinfowindow.cpp \
    questionnairelib/qucontainerhorizontal.cpp \
    questionnairelib/quhorizontalline.cpp \
    questionnairelib/quspacer.cpp \
    widgets/spacer.cpp \
    questionnairelib/qucontainervertical.cpp \
    questionnairelib/qucontainertable.cpp \
    questionnairelib/quheading.cpp \
    questionnairelib/quimage.cpp \
    tasklib/tasksorter.cpp \
    widgets/openablewidget.cpp \
    dbobjects/storedvar.cpp \
    questionnairelib/quaudioplayer.cpp \
    questionnairelib/qucountdown.cpp \
    widgets/imagebutton.cpp \
    questionnairelib/quboolean.cpp \
    widgets/clickablelabel.cpp \
    questionnairelib/qumcq.cpp \
    common/random.cpp \
    questionnairelib/questionnairefunc.cpp \
    widgets/flowlayout.cpp \
    widgets/booleanwidget.cpp

HEADERS  += \
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
    tasklib/inittasks.h \
    menulib/menuheader.h \
    menulib/menuitem.h \
    menulib/menuwindow.h \
    questionnairelib/namevaluepair.h \
    lib/fieldref.h \
    menu/testmenu.h \
    menu/mainmenu.h \
    common/camcopsapp.h \
    common/dbconstants.h \
    common/uiconstants.h \
    menulib/menuproxy.h \
    menu/affectivemenu.h \
    menu/addictionmenu.h \
    menu/anonymousmenu.h \
    menu/alltasksmenu.h \
    menu/catatoniaepsemenu.h \
    menu/clinicalmenu.h \
    menu/clinicalsetsmenu.h \
    menu/cognitivemenu.h \
    menu/executivemenu.h \
    menu/globalmenu.h \
    menu/helpmenu.h \
    menu/personalitymenu.h \
    menu/psychosismenu.h \
    menu/researchmenu.h \
    menu/researchsetsmenu.h \
    menu/settingsmenu.h \
    menu/whiskermenu.h \
    menu/setmenucpftaffective1.h \
    menu/setmenudeakin1.h \
    menu/setmenufromlp.h \
    menu/setmenuobrien1.h \
    common/platform.h \
    menu/singletaskmenu.h \
    menu/patientsummarymenu.h \
    questionnairelib/questionnaireheader.h \
    tasks/demoquestionnaire.h \
    questionnairelib/questionnaire.h \
    questionnairelib/quelement.h \
    questionnairelib/qutext.h \
    questionnairelib/qupage.h \
    widgets/verticalscrollarea.h \
    widgets/labelwordwrapwide.h \
    questionnairelib/qubutton.h \
    menulib/htmlinfowindow.h \
    questionnairelib/qucontainerhorizontal.h \
    questionnairelib/quhorizontalline.h \
    questionnairelib/quspacer.h \
    widgets/spacer.h \
    questionnairelib/qucontainervertical.h \
    questionnairelib/qucontainertable.h \
    questionnairelib/quheading.h \
    questionnairelib/quimage.h \
    tasklib/tasksorter.h \
    lib/cloneable.h \
    widgets/openablewidget.h \
    dbobjects/storedvar.h \
    questionnairelib/quaudioplayer.h \
    questionnairelib/qucountdown.h \
    widgets/imagebutton.h \
    questionnairelib/quboolean.h \
    widgets/clickablelabel.h \
    questionnairelib/qumcq.h \
    common/random.h \
    questionnairelib/questionnairefunc.h \
    widgets/flowlayout.h \
    widgets/booleanwidget.h

CONFIG += debug
CONFIG += mobility
CONFIG += c++11
MOBILITY =

RESOURCES += \
    camcops.qrc

DISTFILES += \
    notes/qt_notes.txt \
    stylesheets/camcops.css \
    tools/build_qt.py \
    android/AndroidManifest.xml \
    android/gradle/wrapper/gradle-wrapper.jar \
    android/gradlew \
    android/res/values/libs.xml \
    android/build.gradle \
    android/gradle/wrapper/gradle-wrapper.properties \
    android/gradlew.bat \
    stylesheets/camcops_menu.css \
    stylesheets/camcops_questionnaire.css \
    android/res/drawable-ldpi/icon.png


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
