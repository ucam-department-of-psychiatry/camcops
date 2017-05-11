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

# For SQLCipher (see its README.md):
# http://stackoverflow.com/questions/16244040/is-the-qt-defines-doing-the-same-thing-as-define-in-c
DEFINES += SQLITE_HAS_CODEC
DEFINES += SQLITE_TEMP_STORE=2

MOBILITY =

# PKGCONFIG += openssl
# ... http://stackoverflow.com/questions/14681012/how-to-include-openssl-in-a-qt-project
# ... but no effect? Not mentioned in variable reference (above).
LIBS += -lssl
# ... not working either? Doesn't complain, but ldd still shows that system libssl.so is in use

LIBS += /home/rudolf/dev/qt_local_build/src/sqlcipher/sqlite3.o  # *** nasty hard-coding

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

INCLUDEPATH += "/home/rudolf/dev/qt_local_build/openssl_linux_build/openssl-1.0.2h/include"  # *** nasty hard-coding

# For SQLCipher (to find sqlcipher/sqlite3.h):
INCLUDEPATH += "/home/rudolf/dev/qt_local_build/src"  # *** nasty hard-coding

# =============================================================================
# Resources and source files
# =============================================================================

RESOURCES += \
    camcops.qrc

SOURCES += main.cpp \
    common/camcopsapp.cpp \
    common/camcopsversion.cpp \
    common/cssconst.cpp \
    common/dbconstants.cpp \
    common/globals.cpp \
    common/platform.cpp \
    common/random.cpp \
    common/uiconstants.cpp \
    common/varconst.cpp \
    common/version.cpp \
    crypto/cryptofunc.cpp \
    crypto/secureqbytearray.cpp \
    crypto/secureqstring.cpp \
    db/databaseobject.cpp \
    db/dbfunc.cpp \
    db/dbnestabletransaction.cpp \
    db/dbtransaction.cpp \
    db/dumpsql.cpp \
    db/field.cpp \
    db/fieldcreationplan.cpp \
    db/fieldref.cpp \
    dbobjects/blob.cpp \
    dbobjects/extrastring.cpp \
    dbobjects/patient.cpp \
    dbobjects/patientsorter.cpp \
    dbobjects/storedvar.cpp \
    db/sqlargs.cpp \
    db/sqlitepragmainfofield.cpp \
    diagnosis/diagnosissortfiltermodel.cpp \
    diagnosis/diagnosticcode.cpp \
    diagnosis/diagnosticcodeset.cpp \
    diagnosis/flatproxymodel.cpp \
    diagnosis/icd10.cpp \
    diagnosis/icd9cm.cpp \
    dialogs/logbox.cpp \
    dialogs/logmessagebox.cpp \
    dialogs/nvpchoicedialog.cpp \
    dialogs/pagepickerdialog.cpp \
    dialogs/passwordchangedialog.cpp \
    dialogs/passwordentrydialog.cpp \
    dialogs/progressbox.cpp \
    dialogs/scrollmessagebox.cpp \
    dialogs/waitbox.cpp \
    lib/convert.cpp \
    lib/debugfunc.cpp \
    lib/filefunc.cpp \
    lib/idpolicy.cpp \
    lib/imagefunc.cpp \
    lib/layoutdumper.cpp \
    lib/mathfunc.cpp \
    lib/networkmanager.cpp \
    lib/numericfunc.cpp \
    lib/sizehelpers.cpp \
    lib/slowguiguard.cpp \
    lib/slownonguifunctioncaller.cpp \
    lib/stringfunc.cpp \
    lib/threadworker.cpp \
    lib/uifunc.cpp \
    menu/addictionmenu.cpp \
    menu/affectivemenu.cpp \
    menu/alltasksmenu.cpp \
    menu/anonymousmenu.cpp \
    menu/catatoniaepsemenu.cpp \
    menu/choosepatientmenu.cpp \
    menu/clinicalmenu.cpp \
    menu/clinicalsetsmenu.cpp \
    menu/cognitivemenu.cpp \
    menu/executivemenu.cpp \
    menu/globalmenu.cpp \
    menu/helpmenu.cpp \
    menulib/choosepatientmenuitem.cpp \
    menulib/htmlinfowindow.cpp \
    menulib/htmlmenuitem.cpp \
    menulib/menuheader.cpp \
    menulib/menuitem.cpp \
    menulib/menuwindow.cpp \
    menulib/taskmenuitem.cpp \
    menu/mainmenu.cpp \
    menu/patientsummarymenu.cpp \
    menu/personalitymenu.cpp \
    menu/psychosismenu.cpp \
    menu/researchmenu.cpp \
    menu/researchsetsmenu.cpp \
    menu/setmenucpftaffective1.cpp \
    menu/setmenudeakin1.cpp \
    menu/setmenufromlp.cpp \
    menu/setmenuobrien1.cpp \
    menu/settingsmenu.cpp \
    menu/singletaskmenu.cpp \
    menu/testmenu.cpp \
    menu/whiskermenu.cpp \
    menu/widgettestmenu.cpp \
    qobjects/focuswatcher.cpp \
    qobjects/keypresswatcher.cpp \
    qobjects/shootabug.cpp \
    qobjects/showwatcher.cpp \
    qobjects/strictdoublevalidator.cpp \
    qobjects/strictint64validator.cpp \
    qobjects/strictintvalidator.cpp \
    qobjects/strictuint64validator.cpp \
    questionnairelib/commonoptions.cpp \
    questionnairelib/mcqfunc.cpp \
    questionnairelib/mcqgridsubtitle.cpp \
    questionnairelib/namevalueoptions.cpp \
    questionnairelib/namevaluepair.cpp \
    questionnairelib/pagepickeritem.cpp \
    questionnairelib/quaudioplayer.cpp \
    questionnairelib/quboolean.cpp \
    questionnairelib/qubutton.cpp \
    questionnairelib/qucanvas.cpp \
    questionnairelib/qucountdown.cpp \
    questionnairelib/qudatetime.cpp \
    questionnairelib/qudiagnosticcode.cpp \
    questionnairelib/quelement.cpp \
    questionnairelib/questionnaire.cpp \
    questionnairelib/questionnairefunc.cpp \
    questionnairelib/questionnaireheader.cpp \
    questionnairelib/questionwithonefield.cpp \
    questionnairelib/questionwithtwofields.cpp \
    questionnairelib/quflowcontainer.cpp \
    questionnairelib/qugridcell.cpp \
    questionnairelib/qugridcontainer.cpp \
    questionnairelib/quheading.cpp \
    questionnairelib/quhorizontalcontainer.cpp \
    questionnairelib/quhorizontalline.cpp \
    questionnairelib/quimage.cpp \
    questionnairelib/qulineedit.cpp \
    questionnairelib/qulineeditdouble.cpp \
    questionnairelib/qulineeditinteger.cpp \
    questionnairelib/qulineeditlonglong.cpp \
    questionnairelib/qulineeditulonglong.cpp \
    questionnairelib/qumcq.cpp \
    questionnairelib/qumcqgrid.cpp \
    questionnairelib/qumcqgriddouble.cpp \
    questionnairelib/qumcqgriddoublesignaller.cpp \
    questionnairelib/qumcqgridsignaller.cpp \
    questionnairelib/qumcqgridsingleboolean.cpp \
    questionnairelib/qumcqgridsinglebooleansignaller.cpp \
    questionnairelib/qumultipleresponse.cpp \
    questionnairelib/qupage.cpp \
    questionnairelib/quphoto.cpp \
    questionnairelib/qupickerinline.cpp \
    questionnairelib/qupickerpopup.cpp \
    questionnairelib/quslider.cpp \
    questionnairelib/quspacer.cpp \
    questionnairelib/quspinboxdouble.cpp \
    questionnairelib/quspinboxinteger.cpp \
    questionnairelib/qutext.cpp \
    questionnairelib/qutextedit.cpp \
    questionnairelib/quthermometer.cpp \
    questionnairelib/quthermometeritem.cpp \
    questionnairelib/quverticalcontainer.cpp \
    tasklib/inittasks.cpp \
    tasklib/task.cpp \
    tasklib/taskfactory.cpp \
    tasklib/taskproxy.cpp \
    tasklib/taskregistrar.cpp \
    tasklib/tasksorter.cpp \
    tasks/ace3.cpp \
    tasks/demoquestionnaire.cpp \
    tasks/phq9.cpp \
    widgets/basewidget.cpp \
    widgets/booleanwidget.cpp \
    widgets/boxlayouthfw.cpp \
    widgets/camera.cpp \
    widgets/canvaswidget.cpp \
    widgets/clickablelabelnowrap.cpp \
    widgets/clickablelabelwordwrapwide.cpp \
    widgets/diagnosticcodeselector.cpp \
    widgets/flowlayouthfw.cpp \
    widgets/gridlayouthfw.cpp \
    widgets/growingtextedit.cpp \
    widgets/hboxlayouthfw.cpp \
    widgets/heightforwidthlistwidget.cpp \
    widgets/horizontalline.cpp \
    widgets/imagebutton.cpp \
    widgets/labelwordwrapwide.cpp \
    widgets/margins.cpp \
    widgets/openablewidget.cpp \
    widgets/qtlayouthelpers.cpp \
    widgets/spacer.cpp \
    widgets/tickslider.cpp \
    widgets/vboxlayouthfw.cpp \
    widgets/verticalline.cpp \
    widgets/verticalscrollarea.cpp \
    common/textconst.cpp \
    lib/flagguard.cpp \
    lib/reentrydepthguard.cpp \
    common/widgetconst.cpp \
    lib/nhs.cpp \
    tasks/aims.cpp \
    tasks/audit.cpp \
    tasks/auditc.cpp \
    tasks/badls.cpp \
    tasks/bdi.cpp \
    tasks/bmi.cpp \
    tasks/bprs.cpp \
    tasks/bprse.cpp \
    tasks/cage.cpp \
    tasks/cape42.cpp \
    tasks/caps.cpp \
    tasks/cbir.cpp \
    tasks/cecaq3.cpp \
    tasks/cgi.cpp \
    tasks/cgii.cpp \
    tasks/cgisch.cpp \
    tasks/ciwa.cpp \
    tasks/contactlog.cpp \
    tasks/copebrief.cpp \
    tasks/cpftlpsdischarge.cpp \
    tasks/cpftlpsreferral.cpp \
    tasks/cpftlpsresetresponseclock.cpp \
    tasks/dad.cpp \
    tasks/dast.cpp \
    tasks/demqol.cpp \
    tasks/demqolproxy.cpp \
    tasks/diagnosisicd9cm.cpp \
    tasks/diagnosistaskbase.cpp \
    tasks/diagnosisitembase.cpp \
    db/ancillaryfunc.cpp \
    tasks/diagnosisicd9cmitem.cpp \
    tasks/diagnosisicd10.cpp \
    tasks/diagnosisicd10item.cpp \
    tasks/deakin1healthreview.cpp \
    tasks/gmcpq.cpp \
    tasks/distressthermometer.cpp \
    tasks/fast.cpp \
    qobjects/comparers.cpp \
    tasks/fft.cpp \
    tasks/frs.cpp \
    tasks/gad7.cpp \
    tasks/gaf.cpp \
    tasks/gds15.cpp \
    tasks/hads.cpp \
    tasks/hama.cpp \
    tasks/hamd.cpp \
    tasks/hamd7.cpp \
    tasks/honos.cpp \
    tasks/honos65.cpp \
    tasks/honosca.cpp \
    tasks/icd10depressive.cpp \
    common/appstrings.cpp \
    tasks/icd10manic.cpp \
    widgets/flickcharm.cpp \
    tasks/icd10mixed.cpp \
    tasks/icd10schizophrenia.cpp \
    tasks/icd10schizotypal.cpp \
    tasks/icd10specpd.cpp \
    tasks/iesr.cpp \
    tasks/ifs.cpp \
    tasks/irac.cpp \
    tasks/mast.cpp \
    tasks/mdsupdrs.cpp \
    lib/roman.cpp \
    tasks/moca.cpp \
    lib/datetime.cpp \
    widgets/fixedareahfwtestwidget.cpp \
    widgets/verticalscrollareaviewport.cpp \
    db/sqlcipherdriver.cpp \
    db/sqlcachedresult.cpp \
    db/sqlcipherresult.cpp \
    db/sqlcipherhelpers.cpp \
    db/whichdb.cpp \
    tasks/nart.cpp \
    tasks/npiq.cpp \
    tasks/panss.cpp \
    tasks/patientsatisfaction.cpp \
    tasks/referrersatisfactiongen.cpp \
    tasks/referrersatisfactionspec.cpp \
    tasks/satisfactioncommon.cpp \
    tasks/pclcommon.cpp \
    tasks/pclc.cpp \
    tasks/pclm.cpp \
    tasks/pcls.cpp \
    tasks/phq15.cpp \
    tasks/pdss.cpp \
    tasks/progressnote.cpp \
    tasks/hadsrespondent.cpp \
    tasks/photo.cpp \
    widgets/aspectratiopixmap.cpp \
    tasks/photosequence.cpp \
    tasks/photosequencephoto.cpp \
    tasks/pswq.cpp \
    tasks/psychiatricclerking.cpp \
    tasks/qolbasic.cpp \
    tasks/rand36.cpp \
    tasks/slums.cpp \
    tasks/smast.cpp \
    tasks/swemwbs.cpp \
    tasks/wemwbs.cpp \
    tasks/wsas.cpp

HEADERS  += \
    common/aliases_camcops.h \
    common/aliases_qt.h \
    common/camcopsapp.h \
    common/camcopsversion.h \
    common/cssconst.h \
    common/dbconstants.h \
    common/globals.h \
    common/gui_defines.h \
    common/layouts.h \
    common/platform.h \
    common/random.h \
    common/uiconstants.h \
    common/varconst.h \
    common/version.h \
    crypto/cryptofunc.h \
    crypto/secureqbytearray.h \
    crypto/secureqstring.h \
    crypto/zallocator.h \
    db/databaseobject.h \
    db/dbfunc.h \
    db/dbnestabletransaction.h \
    db/dbtransaction.h \
    db/dumpsql.h \
    db/fieldcreationplan.h \
    db/field.h \
    db/fieldref.h \
    dbobjects/blob.h \
    dbobjects/extrastring.h \
    dbobjects/patient.h \
    dbobjects/patientsorter.h \
    dbobjects/storedvar.h \
    db/sqlargs.h \
    db/sqlitepragmainfofield.h \
    diagnosis/diagnosissortfiltermodel.h \
    diagnosis/diagnosticcode.h \
    diagnosis/diagnosticcodeset.h \
    diagnosis/flatproxymodel.h \
    diagnosis/icd10.h \
    diagnosis/icd9cm.h \
    dialogs/logbox.h \
    dialogs/logmessagebox.h \
    dialogs/nvpchoicedialog.h \
    dialogs/pagepickerdialog.h \
    dialogs/passwordchangedialog.h \
    dialogs/passwordentrydialog.h \
    dialogs/progressbox.h \
    dialogs/scrollmessagebox.h \
    dialogs/waitbox.h \
    lib/cloneable.h \
    lib/convert.h \
    lib/debugfunc.h \
    lib/filefunc.h \
    lib/idpolicy.h \
    lib/imagefunc.h \
    lib/layoutdumper.h \
    lib/mathfunc.h \
    lib/networkmanager.h \
    lib/numericfunc.h \
    lib/sizehelpers.h \
    lib/slowguiguard.h \
    lib/slownonguifunctioncaller.h \
    lib/stringfunc.h \
    lib/threadworker.h \
    lib/uifunc.h \
    menu/addictionmenu.h \
    menu/affectivemenu.h \
    menu/alltasksmenu.h \
    menu/anonymousmenu.h \
    menu/catatoniaepsemenu.h \
    menu/choosepatientmenu.h \
    menu/clinicalmenu.h \
    menu/clinicalsetsmenu.h \
    menu/cognitivemenu.h \
    menu/executivemenu.h \
    menu/globalmenu.h \
    menu/helpmenu.h \
    menulib/choosepatientmenuitem.h \
    menulib/htmlinfowindow.h \
    menulib/htmlmenuitem.h \
    menulib/menuheader.h \
    menulib/menuitem.h \
    menulib/menuproxy.h \
    menulib/menuwindow.h \
    menulib/taskmenuitem.h \
    menu/mainmenu.h \
    menu/patientsummarymenu.h \
    menu/personalitymenu.h \
    menu/psychosismenu.h \
    menu/researchmenu.h \
    menu/researchsetsmenu.h \
    menu/setmenucpftaffective1.h \
    menu/setmenudeakin1.h \
    menu/setmenufromlp.h \
    menu/setmenuobrien1.h \
    menu/settingsmenu.h \
    menu/singletaskmenu.h \
    menu/testmenu.h \
    menu/whiskermenu.h \
    menu/widgettestmenu.h \
    qobjects/focuswatcher.h \
    qobjects/keypresswatcher.h \
    qobjects/shootabug.h \
    qobjects/showwatcher.h \
    qobjects/strictdoublevalidator.h \
    qobjects/strictint64validator.h \
    qobjects/strictintvalidator.h \
    qobjects/strictuint64validator.h \
    questionnairelib/commonoptions.h \
    questionnairelib/mcqfunc.h \
    questionnairelib/mcqgridsubtitle.h \
    questionnairelib/namevalueoptions.h \
    questionnairelib/namevaluepair.h \
    questionnairelib/pagepickeritem.h \
    questionnairelib/quaudioplayer.h \
    questionnairelib/quboolean.h \
    questionnairelib/qubutton.h \
    questionnairelib/qucanvas.h \
    questionnairelib/qucountdown.h \
    questionnairelib/qudatetime.h \
    questionnairelib/qudiagnosticcode.h \
    questionnairelib/quelement.h \
    questionnairelib/questionnairefunc.h \
    questionnairelib/questionnaire.h \
    questionnairelib/questionnaireheader.h \
    questionnairelib/questionwithonefield.h \
    questionnairelib/questionwithtwofields.h \
    questionnairelib/quflowcontainer.h \
    questionnairelib/qugridcell.h \
    questionnairelib/qugridcontainer.h \
    questionnairelib/quheading.h \
    questionnairelib/quhorizontalcontainer.h \
    questionnairelib/quhorizontalline.h \
    questionnairelib/quimage.h \
    questionnairelib/qulineeditdouble.h \
    questionnairelib/qulineedit.h \
    questionnairelib/qulineeditinteger.h \
    questionnairelib/qulineeditlonglong.h \
    questionnairelib/qulineeditulonglong.h \
    questionnairelib/qumcqgriddouble.h \
    questionnairelib/qumcqgriddoublesignaller.h \
    questionnairelib/qumcqgrid.h \
    questionnairelib/qumcqgridsignaller.h \
    questionnairelib/qumcqgridsingleboolean.h \
    questionnairelib/qumcqgridsinglebooleansignaller.h \
    questionnairelib/qumcq.h \
    questionnairelib/qumultipleresponse.h \
    questionnairelib/qupage.h \
    questionnairelib/quphoto.h \
    questionnairelib/qupickerinline.h \
    questionnairelib/qupickerpopup.h \
    questionnairelib/quslider.h \
    questionnairelib/quspacer.h \
    questionnairelib/quspinboxdouble.h \
    questionnairelib/quspinboxinteger.h \
    questionnairelib/qutextedit.h \
    questionnairelib/qutext.h \
    questionnairelib/quthermometer.h \
    questionnairelib/quthermometeritem.h \
    questionnairelib/quverticalcontainer.h \
    tasklib/inittasks.h \
    tasklib/taskfactory.h \
    tasklib/task.h \
    tasklib/taskproxy.h \
    tasklib/taskregistrar.h \
    tasklib/tasksorter.h \
    tasks/ace3.h \
    tasks/demoquestionnaire.h \
    tasks/phq9.h \
    widgets/basewidget.h \
    widgets/booleanwidget.h \
    widgets/boxlayouthfw.h \
    widgets/camera.h \
    widgets/canvaswidget.h \
    widgets/clickablelabelnowrap.h \
    widgets/clickablelabelwordwrapwide.h \
    widgets/diagnosticcodeselector.h \
    widgets/flowlayouthfw.h \
    widgets/gridlayouthfw.h \
    widgets/growingtextedit.h \
    widgets/hboxlayouthfw.h \
    widgets/heightforwidthlistwidget.h \
    widgets/horizontalline.h \
    widgets/imagebutton.h \
    widgets/labelwordwrapwide.h \
    widgets/margins.h \
    widgets/openablewidget.h \
    widgets/qtlayouthelpers.h \
    widgets/spacer.h \
    widgets/tickslider.h \
    widgets/vboxlayouthfw.h \
    widgets/verticalline.h \
    widgets/verticalscrollarea.h \
    common/textconst.h \
    lib/flagguard.h \
    lib/reentrydepthguard.h \
    common/widgetconst.h \
    lib/nhs.h \
    tasks/aims.h \
    tasks/audit.h \
    tasks/auditc.h \
    tasks/badls.h \
    tasks/bdi.h \
    tasks/bmi.h \
    tasks/bprs.h \
    tasks/bprse.h \
    tasks/cage.h \
    tasks/cape42.h \
    tasks/caps.h \
    tasks/cbir.h \
    tasks/cecaq3.h \
    tasks/cgi.h \
    tasks/cgii.h \
    tasks/cgisch.h \
    tasks/ciwa.h \
    tasks/contactlog.h \
    tasks/copebrief.h \
    tasks/cpftlpsdischarge.h \
    tasks/cpftlpsreferral.h \
    tasks/cpftlpsresetresponseclock.h \
    tasks/dad.h \
    tasks/dast.h \
    tasks/demqol.h \
    tasks/demqolproxy.h \
    tasks/diagnosisicd9cm.h \
    tasks/diagnosistaskbase.h \
    tasks/diagnosisitembase.h \
    db/ancillaryfunc.h \
    tasks/diagnosisicd9cmitem.h \
    tasks/diagnosisicd10.h \
    tasks/diagnosisicd10item.h \
    tasks/deakin1healthreview.h \
    tasks/gmcpq.h \
    tasks/distressthermometer.h \
    tasks/fast.h \
    qobjects/comparers.h \
    tasks/fft.h \
    tasks/frs.h \
    tasks/gad7.h \
    tasks/gaf.h \
    tasks/gds15.h \
    tasks/hads.h \
    tasks/hama.h \
    tasks/hamd.h \
    tasks/hamd7.h \
    tasks/honos.h \
    tasks/honos65.h \
    tasks/honosca.h \
    tasks/icd10depressive.h \
    common/appstrings.h \
    tasks/icd10manic.h \
    widgets/flickcharm.h \
    tasks/icd10mixed.h \
    tasks/icd10schizophrenia.h \
    tasks/icd10schizotypal.h \
    tasks/icd10specpd.h \
    tasks/iesr.h \
    tasks/ifs.h \
    tasks/irac.h \
    tasks/mast.h \
    tasks/mdsupdrs.h \
    lib/roman.h \
    tasks/moca.h \
    lib/datetime.h \
    widgets/fixedareahfwtestwidget.h \
    widgets/verticalscrollareaviewport.h \
    db/sqlcipherdriver.h \
    db/sqlcachedresult.h \
    db/sqlcipherresult.h \
    db/sqlcipherhelpers.h \
    db/whichdb.h \
    tasks/nart.h \
    tasks/npiq.h \
    tasks/panss.h \
    tasks/patientsatisfaction.h \
    tasks/referrersatisfactiongen.h \
    tasks/referrersatisfactionspec.h \
    tasks/satisfactioncommon.h \
    tasks/pclcommon.h \
    tasks/pclc.h \
    tasks/pclm.h \
    tasks/pcls.h \
    tasks/phq15.h \
    tasks/pdss.h \
    tasks/progressnote.h \
    tasks/hadsrespondent.h \
    tasks/photo.h \
    widgets/aspectratiopixmap.h \
    tasks/photosequence.h \
    tasks/photosequencephoto.h \
    tasks/pswq.h \
    tasks/psychiatricclerking.h \
    tasks/qolbasic.h \
    tasks/rand36.h \
    tasks/slums.h \
    tasks/smast.h \
    tasks/swemwbs.h \
    tasks/wemwbs.h \
    tasks/wsas.h


DISTFILES += \
    android/AndroidManifest.xml \
    android/build.gradle \
    android/gradlew \
    android/gradlew.bat \
    android/gradle/wrapper/gradle-wrapper.jar \
    android/gradle/wrapper/gradle-wrapper.properties \
    android/res/drawable-ldpi/icon.png \
    android/res/values/libs.xml \
    images/dt/dt_sel_0.png \
    images/dt/dt_sel_10.png \
    images/dt/dt_sel_1.png \
    images/dt/dt_sel_2.png \
    images/dt/dt_sel_3.png \
    images/dt/dt_sel_4.png \
    images/dt/dt_sel_5.png \
    images/dt/dt_sel_6.png \
    images/dt/dt_sel_7.png \
    images/dt/dt_sel_8.png \
    images/dt/dt_sel_9.png \
    images/dt/dt_unsel_0.png \
    images/dt/dt_unsel_10.png \
    images/dt/dt_unsel_1.png \
    images/dt/dt_unsel_2.png \
    images/dt/dt_unsel_3.png \
    images/dt/dt_unsel_4.png \
    images/dt/dt_unsel_5.png \
    images/dt/dt_unsel_6.png \
    images/dt/dt_unsel_7.png \
    images/dt/dt_unsel_8.png \
    images/dt/dt_unsel_9.png \
    LICENSE.txt \
    notes/coding_conventions.txt \
    notes/known_problems.txt \
    notes/qt_notes.txt \
    notes/to_do.txt \
    stylesheets/camcops.css \
    stylesheets/camcops_menu.css \
    stylesheets/camcops_questionnaire.css \
    stylesheets/camera.css \
    tools/build_qt.py \
    notes/rejected_ideas.txt \
    notes/string_formats.txt \
    notes/layout_notes.txt


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
