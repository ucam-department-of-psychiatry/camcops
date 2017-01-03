#-------------------------------------------------
#
# Project created by QtCreator 2016-05-30T22:51:39
#
#-------------------------------------------------

# http://doc.qt.io/qt-5.7/qmake-project-files.html
# http://doc.qt.io/qt-5.7/qmake-variable-reference.html

# =============================================================================
# Parts of Qt
# =============================================================================

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

# =============================================================================
# Overall configuration
# =============================================================================

CONFIG += static  # use a statically linked version of Qt
# CONFIG += debug  # no, use the QtCreator debug/release settings
CONFIG += mobility
CONFIG += c++11
MOBILITY =

# PKGCONFIG += openssl
# ... http://stackoverflow.com/questions/14681012/how-to-include-openssl-in-a-qt-project
# ... but no effect? Not mentioned in variable reference (above).
LIBS += -lssl
# ... not working either? Doesn't complain, but ldd still shows that system libssl.so is in use

# =============================================================================
# Compiler flags
# =============================================================================

QMAKE_CXXFLAGS += -Werror  # warnings become errors

# In release mode, optimize heavily:
QMAKE_CXXFLAGS_RELEASE -= -O
QMAKE_CXXFLAGS_RELEASE -= -O1
QMAKE_CXXFLAGS_RELEASE -= -O2
QMAKE_CXXFLAGS_RELEASE += -O3  # optimize heavily

# =============================================================================
# Build targets
# =============================================================================

TARGET = camcops
TEMPLATE = app

# =============================================================================
# Paths
# =============================================================================

INCLUDEPATH += "/home/rudolf/dev/qt_local_build/openssl_linux_build/openssl-1.0.2h/include"

# =============================================================================
# Resources and source files
# =============================================================================

RESOURCES += \
    camcops.qrc

SOURCES += main.cpp\
    lib/uifunc.cpp \
    lib/filefunc.cpp \
    tasklib/taskfactory.cpp \
    tasklib/task.cpp \
    tasks/phq9.cpp \
    db/databaseobject.cpp \
    db/dbfunc.cpp \
    db/field.cpp \
    lib/datetimefunc.cpp \
    tasklib/inittasks.cpp \
    menulib/menuheader.cpp \
    menulib/menuitem.cpp \
    menulib/menuwindow.cpp \
    questionnairelib/namevaluepair.cpp \
    db/fieldref.cpp \
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
    questionnairelib/quhorizontalline.cpp \
    questionnairelib/quspacer.cpp \
    widgets/spacer.cpp \
    questionnairelib/quheading.cpp \
    questionnairelib/quimage.cpp \
    tasklib/tasksorter.cpp \
    widgets/openablewidget.cpp \
    dbobjects/storedvar.cpp \
    questionnairelib/quaudioplayer.cpp \
    questionnairelib/qucountdown.cpp \
    widgets/imagebutton.cpp \
    questionnairelib/quboolean.cpp \
    questionnairelib/qumcq.cpp \
    common/random.cpp \
    questionnairelib/questionnairefunc.cpp \
    widgets/booleanwidget.cpp \
    questionnairelib/qupickerinline.cpp \
    questionnairelib/namevalueoptions.cpp \
    questionnairelib/qupickerpopup.cpp \
    dialogs/nvpchoicedialog.cpp \
    questionnairelib/quthermometer.cpp \
    questionnairelib/quthermometeritem.cpp \
    questionnairelib/quslider.cpp \
    widgets/tickslider.cpp \
    common/version.cpp \
    questionnairelib/qudatetime.cpp \
    questionnairelib/quspinboxinteger.cpp \
    questionnairelib/quspinboxdouble.cpp \
    questionnairelib/qutextedit.cpp \
    widgets/growingtextedit.cpp \
    questionnairelib/qulineedit.cpp \
    questionnairelib/qulineeditinteger.cpp \
    questionnairelib/qulineeditdouble.cpp \
    qobjects/strictdoublevalidator.cpp \
    qobjects/strictintvalidator.cpp \
    lib/numericfunc.cpp \
    qobjects/focuswatcher.cpp \
    questionnairelib/qugridcell.cpp \
    questionnairelib/qumultipleresponse.cpp \
    questionnairelib/qucanvas.cpp \
    widgets/canvaswidget.cpp \
    questionnairelib/quphoto.cpp \
    questionnairelib/qudiagnosticcode.cpp \
    widgets/camera.cpp \
    widgets/diagnosticcodeselector.cpp \
    widgets/aspectratiopixmaplabel.cpp \
    diagnosis/diagnosticcode.cpp \
    diagnosis/diagnosticcodeset.cpp \
    diagnosis/icd10.cpp \
    diagnosis/icd9cm.cpp \
    lib/imagefunc.cpp \
    diagnosis/flatproxymodel.cpp \
    diagnosis/diagnosissortfiltermodel.cpp \
    dialogs/progressbox.cpp \
    lib/convert.cpp \
    dbobjects/blob.cpp \
    lib/debugfunc.cpp \
    menulib/taskmenuitem.cpp \
    menulib/htmlmenuitem.cpp \
    tasklib/taskproxy.cpp \
    tasklib/taskregistrar.cpp \
    questionnairelib/qumcqgrid.cpp \
    questionnairelib/mcqgridsubtitle.cpp \
    qobjects/shootabug.cpp \
    questionnairelib/qumcqgriddouble.cpp \
    questionnairelib/questionwithtwofields.cpp \
    questionnairelib/questionwithonefield.cpp \
    questionnairelib/mcqfunc.cpp \
    widgets/horizontalline.cpp \
    widgets/verticalline.cpp \
    questionnairelib/qumcqgridsingleboolean.cpp \
    lib/stringfunc.cpp \
    dialogs/waitbox.cpp \
    lib/threadworker.cpp \
    lib/slownonguifunctioncaller.cpp \
    lib/slowguiguard.cpp \
    dbobjects/patient.cpp \
    db/sqlitepragmainfofield.cpp \
    db/fieldcreationplan.cpp \
    db/sqlargs.cpp \
    lib/networkmanager.cpp \
    dialogs/logbox.cpp \
    common/varconst.cpp \
    db/dbtransaction.cpp \
    db/dbnestabletransaction.cpp \
    questionnairelib/commonoptions.cpp \
    crypto/cryptofunc.cpp \
    crypto/secureqstring.cpp \
    crypto/secureqbytearray.cpp \
    dbobjects/extrastring.cpp \
    dialogs/passwordentrydialog.cpp \
    dialogs/passwordchangedialog.cpp \
    common/camcopsversion.cpp \
    dialogs/pagepickerdialog.cpp \
    questionnairelib/pagepickeritem.cpp \
    widgets/clickablelabelwordwrapwide.cpp \
    lib/layoutdumper.cpp \
    qobjects/showwatcher.cpp \
    menu/widgettestmenu.cpp \
    qobjects/keypresswatcher.cpp \
    common/cssconst.cpp \
    questionnairelib/qumcqgridsignaller.cpp \
    questionnairelib/qumcqgriddoublesignaller.cpp \
    questionnairelib/qumcqgridsinglebooleansignaller.cpp \
    menu/choosepatientmenu.cpp \
    menulib/choosepatientmenuitem.cpp \
    qobjects/strictuint64validator.cpp \
    questionnairelib/qulineeditulonglong.cpp \
    questionnairelib/qulineeditlonglong.cpp \
    qobjects/strictint64validator.cpp \
    lib/idpolicy.cpp \
    lib/mathfunc.cpp \
    db/dumpsql.cpp \
    dialogs/scrollmessagebox.cpp \
    dialogs/logmessagebox.cpp \
    dbobjects/patientsorter.cpp \
    tasks/ace3.cpp \
    widgets/heightforwidthlistwidget.cpp \
    widgets/flowlayouthfw.cpp \
    widgets/boxlayouthfw.cpp \
    widgets/qtlayouthelpers.cpp \
    widgets/vboxlayouthfw.cpp \
    widgets/hboxlayouthfw.cpp \
    widgets/basewidget.cpp \
    widgets/clickablelabelnowrap.cpp \
    questionnairelib/quflowcontainer.cpp \
    questionnairelib/qugridcontainer.cpp \
    questionnairelib/quverticalcontainer.cpp \
    questionnairelib/quhorizontalcontainer.cpp

HEADERS  += \
    lib/uifunc.h \
    lib/filefunc.h \
    tasklib/taskfactory.h \
    tasklib/task.h \
    tasks/phq9.h \
    db/databaseobject.h \
    db/dbfunc.h \
    db/field.h \
    lib/datetimefunc.h \
    tasklib/inittasks.h \
    menulib/menuheader.h \
    menulib/menuitem.h \
    menulib/menuwindow.h \
    questionnairelib/namevaluepair.h \
    db/fieldref.h \
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
    questionnairelib/quhorizontalline.h \
    questionnairelib/quspacer.h \
    widgets/spacer.h \
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
    questionnairelib/qumcq.h \
    common/random.h \
    questionnairelib/questionnairefunc.h \
    widgets/booleanwidget.h \
    questionnairelib/qupickerinline.h \
    questionnairelib/namevalueoptions.h \
    questionnairelib/qupickerpopup.h \
    dialogs/nvpchoicedialog.h \
    questionnairelib/quthermometer.h \
    questionnairelib/quthermometeritem.h \
    questionnairelib/quslider.h \
    widgets/tickslider.h \
    common/version.h \
    questionnairelib/qudatetime.h \
    questionnairelib/quspinboxinteger.h \
    questionnairelib/quspinboxdouble.h \
    questionnairelib/qutextedit.h \
    widgets/growingtextedit.h \
    questionnairelib/qulineedit.h \
    questionnairelib/qulineeditinteger.h \
    questionnairelib/qulineeditdouble.h \
    qobjects/strictdoublevalidator.h \
    qobjects/strictintvalidator.h \
    lib/numericfunc.h \
    qobjects/focuswatcher.h \
    questionnairelib/qugridcell.h \
    questionnairelib/qumultipleresponse.h \
    questionnairelib/qucanvas.h \
    widgets/canvaswidget.h \
    questionnairelib/quphoto.h \
    questionnairelib/qudiagnosticcode.h \
    widgets/camera.h \
    widgets/diagnosticcodeselector.h \
    widgets/aspectratiopixmaplabel.h \
    diagnosis/diagnosticcode.h \
    diagnosis/diagnosticcodeset.h \
    diagnosis/icd10.h \
    diagnosis/icd9cm.h \
    lib/imagefunc.h \
    diagnosis/flatproxymodel.h \
    diagnosis/diagnosissortfiltermodel.h \
    dialogs/progressbox.h \
    lib/convert.h \
    dbobjects/blob.h \
    lib/debugfunc.h \
    menulib/taskmenuitem.h \
    menulib/htmlmenuitem.h \
    tasklib/taskproxy.h \
    tasklib/taskregistrar.h \
    questionnairelib/qumcqgrid.h \
    questionnairelib/mcqgridsubtitle.h \
    qobjects/shootabug.h \
    questionnairelib/qumcqgriddouble.h \
    questionnairelib/questionwithtwofields.h \
    questionnairelib/questionwithonefield.h \
    questionnairelib/mcqfunc.h \
    widgets/horizontalline.h \
    widgets/verticalline.h \
    questionnairelib/qumcqgridsingleboolean.h \
    lib/stringfunc.h \
    dialogs/waitbox.h \
    lib/threadworker.h \
    lib/slownonguifunctioncaller.h \
    lib/slowguiguard.h \
    dbobjects/patient.h \
    db/sqlitepragmainfofield.h \
    db/fieldcreationplan.h \
    db/sqlargs.h \
    lib/networkmanager.h \
    dialogs/logbox.h \
    common/varconst.h \
    db/dbtransaction.h \
    db/dbnestabletransaction.h \
    questionnairelib/commonoptions.h \
    crypto/cryptofunc.h \
    crypto/secureqstring.h \
    crypto/secureqbytearray.h \
    crypto/zallocator.h \
    dbobjects/extrastring.h \
    dialogs/passwordentrydialog.h \
    dialogs/passwordchangedialog.h \
    common/camcopsversion.h \
    dialogs/pagepickerdialog.h \
    questionnairelib/pagepickeritem.h \
    widgets/clickablelabelwordwrapwide.h \
    lib/layoutdumper.h \
    qobjects/showwatcher.h \
    menu/widgettestmenu.h \
    qobjects/keypresswatcher.h \
    common/cssconst.h \
    questionnairelib/qumcqgridsignaller.h \
    questionnairelib/qumcqgriddoublesignaller.h \
    questionnairelib/qumcqgridsinglebooleansignaller.h \
    menu/choosepatientmenu.h \
    menulib/choosepatientmenuitem.h \
    qobjects/strictuint64validator.h \
    questionnairelib/qulineeditulonglong.h \
    questionnairelib/qulineeditlonglong.h \
    qobjects/strictint64validator.h \
    lib/idpolicy.h \
    lib/mathfunc.h \
    common/aliases_qt.h \
    common/aliases_camcops.h \
    db/dumpsql.h \
    dialogs/scrollmessagebox.h \
    dialogs/logmessagebox.h \
    dbobjects/patientsorter.h \
    tasks/ace3.h \
    widgets/heightforwidthlistwidget.h \
    widgets/flowlayouthfw.h \
    widgets/boxlayouthfw.h \
    widgets/qtlayouthelpers.h \
    widgets/vboxlayouthfw.h \
    widgets/hboxlayouthfw.h \
    widgets/basewidget.h \
    widgets/clickablelabelnowrap.h \
    common/gui_defines.h \
    questionnairelib/quflowcontainer.h \
    questionnairelib/quhorizontalcontainer.h \
    questionnairelib/quverticalcontainer.h \
    questionnairelib/qugridcontainer.h

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
    android/res/drawable-ldpi/icon.png \
    images/dt/dt_sel_0.png \
    images/dt/dt_sel_1.png \
    images/dt/dt_sel_2.png \
    images/dt/dt_sel_3.png \
    images/dt/dt_sel_4.png \
    images/dt/dt_sel_5.png \
    images/dt/dt_sel_6.png \
    images/dt/dt_sel_7.png \
    images/dt/dt_sel_8.png \
    images/dt/dt_sel_9.png \
    images/dt/dt_sel_10.png \
    images/dt/dt_unsel_0.png \
    images/dt/dt_unsel_1.png \
    images/dt/dt_unsel_2.png \
    images/dt/dt_unsel_3.png \
    images/dt/dt_unsel_4.png \
    images/dt/dt_unsel_5.png \
    images/dt/dt_unsel_6.png \
    images/dt/dt_unsel_7.png \
    images/dt/dt_unsel_8.png \
    images/dt/dt_unsel_9.png \
    images/dt/dt_unsel_10.png \
    stylesheets/camera.css \
    LICENSE.txt

# =============================================================================
# Android-specific options
# =============================================================================

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
