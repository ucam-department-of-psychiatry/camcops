CONFIG += testcase
QT += network
QT += svg
QT += svgwidgets
QT += testlib
QT += widgets
QT -= gui

TARGET = bin/test_graphicsfunc

SOURCES += \
    testgraphicsfunc.cpp \
    $$CAMCOPS_SRC/common/cssconst.cpp \
    $$CAMCOPS_SRC/common/dpi.cpp \
    $$CAMCOPS_SRC/common/textconst.cpp \
    $$CAMCOPS_SRC/common/uiconst.cpp \
    $$CAMCOPS_SRC/graphics/buttonconfig.cpp \
    $$CAMCOPS_SRC/graphics/geometry.cpp \
    $$CAMCOPS_SRC/graphics/graphicsfunc.cpp \
    $$CAMCOPS_SRC/graphics/graphicspixmapitemwithopacity.cpp \
    $$CAMCOPS_SRC/graphics/linesegment.cpp \
    $$CAMCOPS_SRC/graphics/paintertranslaterotatecontext.cpp \
    $$CAMCOPS_SRC/lib/convert.cpp \
    $$CAMCOPS_SRC/lib/css.cpp \
    $$CAMCOPS_SRC/lib/customtypes.cpp \
    $$CAMCOPS_SRC/lib/datetime.cpp \
    $$CAMCOPS_SRC/lib/errorfunc.cpp \
    $$CAMCOPS_SRC/lib/filefunc.cpp \
    $$CAMCOPS_SRC/lib/stringfunc.cpp \
    $$CAMCOPS_SRC/lib/timerfunc.cpp \
    $$CAMCOPS_SRC/lib/version.cpp \
    $$CAMCOPS_SRC/lib/widgetfunc.cpp \
    $$CAMCOPS_SRC/maths/mathfunc.cpp \
    $$CAMCOPS_SRC/widgets/adjustablepie.cpp \
    $$CAMCOPS_SRC/widgets/svgwidgetclickable.cpp

HEADERS += \
    $$CAMCOPS_SRC/common/cssconst.h \
    $$CAMCOPS_SRC/common/dpi.h \
    $$CAMCOPS_SRC/common/textconst.h \
    $$CAMCOPS_SRC/common/uiconst.h \
    $$CAMCOPS_SRC/graphics/buttonconfig.h \
    $$CAMCOPS_SRC/graphics/geometry.h \
    $$CAMCOPS_SRC/graphics/graphicsfunc.h \
    $$CAMCOPS_SRC/graphics/graphicspixmapitemwithopacity.h \
    $$CAMCOPS_SRC/graphics/linesegment.h \
    $$CAMCOPS_SRC/graphics/paintertranslaterotatecontext.h \
    $$CAMCOPS_SRC/lib/convert.h \
    $$CAMCOPS_SRC/lib/css.h \
    $$CAMCOPS_SRC/lib/customtypes.h \
    $$CAMCOPS_SRC/lib/datetime.h \
    $$CAMCOPS_SRC/lib/errorfunc.h \
    $$CAMCOPS_SRC/lib/filefunc.h \
    $$CAMCOPS_SRC/lib/stringfunc.h \
    $$CAMCOPS_SRC/lib/timerfunc.h \
    $$CAMCOPS_SRC/lib/version.h \
    $$CAMCOPS_SRC/lib/widgetfunc.h \
    $$CAMCOPS_SRC/maths/mathfunc.h \
    $$CAMCOPS_SRC/widgets/adjustablepie.h \
    $$CAMCOPS_SRC/widgets/svgwidgetclickable.h

INCLUDEPATH += "$${QT_BASE_DIR}/eigen/eigen-$$EIGEN_VERSION"
INCLUDEPATH += $$CAMCOPS_SRC

DEFINES += SRCDIR=\\\"$$PWD/\\\"
