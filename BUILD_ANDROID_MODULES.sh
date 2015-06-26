#!/bin/bash
set -e

THISDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TITANIUM_HOME=~/Library/Application\ Support/Titanium

# -- http://docs.appcelerator.com/platform/latest/#!/guide/Android_Module_Quick_Start
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

cd $THISDIR/androidtibugfix
ant clean
ant
unzip -o dist/org.camcops.androidtibugfix-android-1.0.zip -d "$TITANIUM_HOME"

cd $THISDIR/androidtipaint
ant clean
ant
unzip -o dist/org.camcops.androidtipaint-android-1.1.zip -d "$TITANIUM_HOME"

cd $THISDIR/androiduitools
ant clean
ant
unzip -o dist/org.camcops.androiduitools-android-1.0.zip -d "$TITANIUM_HOME"

