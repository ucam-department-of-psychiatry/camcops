#!/bin/bash
set -e

THISDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TITANIUM_HOME=~/Library/Application\ Support/Titanium

case $1 in
    clean)
        CLEAN=true
        BUILD=false
        ;;

    build)
        CLEAN=false
        BUILD=true
        ;;

    rebuild)
        CLEAN=true
        BUILD=true
        ;;

    *)
        echo "Usage: $0 clean|build|rebuild"
        exit 1
        ;;
esac

# -- http://docs.appcelerator.com/platform/latest/#!/guide/Android_Module_Quick_Start
# -- http://docs.appcelerator.com/platform/latest/#!/guide/iOS_Module_Quick_Start
#
# * UNNECESSARY: Get wget for OS X
#
#   brew install wget
#
# * Get ant
#
#   -- http://docs.appcelerator.com/platform/latest/#!/guide/Installing_Ant
#   -- http://ant.apache.org/bindownload.cgi
#   -- http://superuser.com/questions/610157/how-do-i-install-ant-on-os-x-mavericks
#
#   brew update
#   brew install ant
#
# * Install python markdown2 module
#
#   sudo pip install markdown2

#==============================================================================
# RNC modules
#==============================================================================
cd $THISDIR/androidtibugfix
if $CLEAN ; then
    ant clean
fi
if $BUILD ; then
    ant
    unzip -o dist/org.camcops.androidtibugfix-android-1.0.zip -d "$TITANIUM_HOME"
fi

cd $THISDIR/androidtipaint
if $CLEAN ; then
    ant clean
fi
if $BUILD ; then
    ant
    unzip -o dist/org.camcops.androidtipaint-android-1.1.zip -d "$TITANIUM_HOME"
fi

cd $THISDIR/androiduitools
if $CLEAN ; then
    ant clean
fi
if $BUILD ; then
    ant
    unzip -o dist/org.camcops.androiduitools-android-1.0.zip -d "$TITANIUM_HOME"
fi

#==============================================================================
# Appcelerator Titanium modules
#==============================================================================

cd $THISDIR/appcelerator_modules/ti.paint/ios
if $BUILD ; then
    python build.py
    unzip -o ti.paint-iphone-1.4.0.zip -d "$TITANIUM_HOME"
fi
# We don't need the Android ti.paint, because we've got our own (above).

cd $THISDIR/appcelerator_modules/ti.imagefactory/ios
if $BUILD ; then
    python build.py
    unzip -o ti.imagefactory-iphone-1.2.0.zip -d "$TITANIUM_HOME"
fi
cd $THISDIR/appcelerator_modules/ti.imagefactory/android
if $CLEAN ; then
    ant clean
fi
if $BUILD ; then
    ant
    unzip -o dist/ti.imagefactory-android-2.2.1.zip -d "$TITANIUM_HOME"
fi
