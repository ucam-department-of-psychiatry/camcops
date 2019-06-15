// bugtest_table_searchbar_android_dock_undock_crash.js

/*jslint node: true */
"use strict";
/*global Titanium */

var rowdata = [
    {title: "row_0"},
    {title: "row_1"},
    {title: "row_2"}
];
var win = Titanium.UI.createWindow({ backgroundColor: '#FFFFFF' });
var table = Titanium.UI.createTableView({
    data: rowdata,
    search: Titanium.UI.createSearchBar({
        top: 0,
        left: 0,
        height: 45,
        showCancel: false
    })
});

win.add(table);
win.open();

/*

NOW:
    use an Android tablet with a physical keyboard, e.g. Asus Eee Pad Transformer Prime
    run the app, so you're looking at a table with a searchbar
    dock or undock the tablet
    crash with this error:
        Wrong state class, expecting View State but received class android.widget.AbsListView$SavedState instead. This usually happens when two views of different type have the same id in the same hierarchy. This view's id is id/0x65. Make sure other views do not use the same id.

TO SEE THE OUTPUT:

    prep the tablet undocked
    adb logcat ("... waiting for device")
    plug it in - adb will then capture the crash

HOST COMPUTER:

Test date: 9 Nov 2013
Host platform: Mac OS X 10.8.5
Titanium Studio, build: 3.1.3.201309132423
Asus Transformer Prime TF201, Android 4.1.1

LIKELY RELATED BUGS:

    https://jira.appcelerator.org/browse/TC-803

FULL ERROR:

D/Window  ( 4204): Checkpoint: postWindowCreated()
W/ResourceType( 4204): No package identifier when getting name for resource number 0x00000065
D/AndroidRuntime( 4204): Shutting down VM
W/dalvikvm( 4204): threadid=1: thread exiting with uncaught exception (group=0x410a9300)
E/TiApplication( 4204): (main) [76112,76112] Sending event: exception on thread: main msg:java.lang.RuntimeException: Unable to start activity ComponentInfo{com.rudolfcardinal.camcops/org.appcelerator.titanium.TiActivity}: java.lang.IllegalArgumentException: Wrong state class, expecting View State but received class android.widget.AbsListView$SavedState instead. This usually happens when two views of different type have the same id in the same hierarchy. This view's id is id/0x65. Make sure other views do not use the same id.; Titanium 3.1.2,2013/08/14 12:46,5ceaff8
E/TiApplication( 4204): java.lang.RuntimeException: Unable to start activity ComponentInfo{com.rudolfcardinal.camcops/org.appcelerator.titanium.TiActivity}: java.lang.IllegalArgumentException: Wrong state class, expecting View State but received class android.widget.AbsListView$SavedState instead. This usually happens when two views of different type have the same id in the same hierarchy. This view's id is id/0x65. Make sure other views do not use the same id.
E/TiApplication( 4204):     at android.app.ActivityThread.performLaunchActivity(ActivityThread.java:2059)
E/TiApplication( 4204):     at android.app.ActivityThread.handleLaunchActivity(ActivityThread.java:2084)
E/TiApplication( 4204):     at android.app.ActivityThread.handleRelaunchActivity(ActivityThread.java:3512)
E/TiApplication( 4204):     at android.app.ActivityThread.access$700(ActivityThread.java:130)
E/TiApplication( 4204):     at android.app.ActivityThread$H.handleMessage(ActivityThread.java:1201)
E/TiApplication( 4204):     at android.os.Handler.dispatchMessage(Handler.java:99)
E/TiApplication( 4204):     at android.os.Looper.loop(Looper.java:137)
E/TiApplication( 4204):     at android.app.ActivityThread.main(ActivityThread.java:4745)
E/TiApplication( 4204):     at java.lang.reflect.Method.invokeNative(Native Method)
E/TiApplication( 4204):     at java.lang.reflect.Method.invoke(Method.java:511)
E/TiApplication( 4204):     at com.android.internal.os.ZygoteInit$MethodAndArgsCaller.run(ZygoteInit.java:786)
E/TiApplication( 4204):     at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:553)
E/TiApplication( 4204):     at dalvik.system.NativeStart.main(Native Method)
E/TiApplication( 4204): Caused by: java.lang.IllegalArgumentException: Wrong state class, expecting View State but received class android.widget.AbsListView$SavedState instead. This usually happens when two views of different type have the same id in the same hierarchy. This view's id is id/0x65. Make sure other views do not use the same id.
E/TiApplication( 4204):     at android.view.View.onRestoreInstanceState(View.java:11934)
E/TiApplication( 4204):     at android.view.View.dispatchRestoreInstanceState(View.java:11910)
E/TiApplication( 4204):     at android.view.ViewGroup.dispatchRestoreInstanceState(ViewGroup.java:2590)
E/TiApplication( 4204):     at android.view.ViewGroup.dispatchRestoreInstanceState(ViewGroup.java:2590)
E/TiApplication( 4204):     at android.view.ViewGroup.dispatchRestoreInstanceState(ViewGroup.java:2590)
E/TiApplication( 4204):     at android.view.ViewGroup.dispatchRestoreInstanceState(ViewGroup.java:2590)
E/TiApplication( 4204):     at android.view.ViewGroup.dispatchRestoreInstanceState(ViewGroup.java:2590)
E/TiApplication( 4204):     at android.view.ViewGroup.dispatchRestoreInstanceState(ViewGroup.java:2590)
E/TiApplication( 4204):     at android.view.View.restoreHierarchyState(View.java:11888)
E/TiApplication( 4204):     at com.android.internal.policy.impl.PhoneWindow.restoreHierarchyState(PhoneWindow.java:1608)
E/TiApplication( 4204):     at android.app.Activity.onRestoreInstanceState(Activity.java:928)
E/TiApplication( 4204):     at org.appcelerator.titanium.TiBaseActivity.onRestoreInstanceState(TiBaseActivity.java:1197)
E/TiApplication( 4204):     at android.app.Activity.performRestoreInstanceState(Activity.java:900)
E/TiApplication( 4204):     at android.app.Instrumentation.callActivityOnRestoreInstanceState(Instrumentation.java:1130)
E/TiApplication( 4204):     at android.app.ActivityThread.performLaunchActivity(ActivityThread.java:2037)
E/TiApplication( 4204):     ... 12 more
E/AndroidRuntime( 4204): FATAL EXCEPTION: main
E/AndroidRuntime( 4204): java.lang.RuntimeException: Unable to start activity ComponentInfo{com.rudolfcardinal.camcops/org.appcelerator.titanium.TiActivity}: java.lang.IllegalArgumentException: Wrong state class, expecting View State but received class android.widget.AbsListView$SavedState instead. This usually happens when two views of different type have the same id in the same hierarchy. This view's id is id/0x65. Make sure other views do not use the same id.
E/AndroidRuntime( 4204):    at android.app.ActivityThread.performLaunchActivity(ActivityThread.java:2059)
E/AndroidRuntime( 4204):    at android.app.ActivityThread.handleLaunchActivity(ActivityThread.java:2084)
E/AndroidRuntime( 4204):    at android.app.ActivityThread.handleRelaunchActivity(ActivityThread.java:3512)
E/AndroidRuntime( 4204):    at android.app.ActivityThread.access$700(ActivityThread.java:130)
E/AndroidRuntime( 4204):    at android.app.ActivityThread$H.handleMessage(ActivityThread.java:1201)
E/AndroidRuntime( 4204):    at android.os.Handler.dispatchMessage(Handler.java:99)
E/AndroidRuntime( 4204):    at android.os.Looper.loop(Looper.java:137)
E/AndroidRuntime( 4204):    at android.app.ActivityThread.main(ActivityThread.java:4745)
E/AndroidRuntime( 4204):    at java.lang.reflect.Method.invokeNative(Native Method)
E/AndroidRuntime( 4204):    at java.lang.reflect.Method.invoke(Method.java:511)
E/AndroidRuntime( 4204):    at com.android.internal.os.ZygoteInit$MethodAndArgsCaller.run(ZygoteInit.java:786)
E/AndroidRuntime( 4204):    at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:553)
E/AndroidRuntime( 4204):    at dalvik.system.NativeStart.main(Native Method)
E/AndroidRuntime( 4204): Caused by: java.lang.IllegalArgumentException: Wrong state class, expecting View State but received class android.widget.AbsListView$SavedState instead. This usually happens when two views of different type have the same id in the same hierarchy. This view's id is id/0x65. Make sure other views do not use the same id.
E/AndroidRuntime( 4204):    at android.view.View.onRestoreInstanceState(View.java:11934)
E/AndroidRuntime( 4204):    at android.view.View.dispatchRestoreInstanceState(View.java:11910)
E/AndroidRuntime( 4204):    at android.view.ViewGroup.dispatchRestoreInstanceState(ViewGroup.java:2590)
E/AndroidRuntime( 4204):    at android.view.ViewGroup.dispatchRestoreInstanceState(ViewGroup.java:2590)
E/AndroidRuntime( 4204):    at android.view.ViewGroup.dispatchRestoreInstanceState(ViewGroup.java:2590)
E/AndroidRuntime( 4204):    at android.view.ViewGroup.dispatchRestoreInstanceState(ViewGroup.java:2590)
E/AndroidRuntime( 4204):    at android.view.ViewGroup.dispatchRestoreInstanceState(ViewGroup.java:2590)
E/AndroidRuntime( 4204):    at android.view.ViewGroup.dispatchRestoreInstanceState(ViewGroup.java:2590)
E/AndroidRuntime( 4204):    at android.view.View.restoreHierarchyState(View.java:11888)
E/AndroidRuntime( 4204):    at com.android.internal.policy.impl.PhoneWindow.restoreHierarchyState(PhoneWindow.java:1608)
E/AndroidRuntime( 4204):    at android.app.Activity.onRestoreInstanceState(Activity.java:928)
E/AndroidRuntime( 4204):    at org.appcelerator.titanium.TiBaseActivity.onRestoreInstanceState(TiBaseActivity.java:1197)
E/AndroidRuntime( 4204):    at android.app.Activity.performRestoreInstanceState(Activity.java:900)
E/AndroidRuntime( 4204):    at android.app.Instrumentation.callActivityOnRestoreInstanceState(Instrumentation.java:1130)
E/AndroidRuntime( 4204):    at android.app.ActivityThread.performLaunchActivity(ActivityThread.java:2037)
E/AndroidRuntime( 4204):    ... 12 more
W/ActivityManager(  420):   Force finishing activity com.rudolfcardinal.camcops/org.appcelerator.titanium.TiActivity

*/