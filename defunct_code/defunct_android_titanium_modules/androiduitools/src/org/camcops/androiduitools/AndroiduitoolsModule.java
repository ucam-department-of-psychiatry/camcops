// AndroiduitoolsModule.java

/*
    Copyright (C) 2012, 2013 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
*/

package org.camcops.androiduitools;

import org.appcelerator.kroll.KrollModule;
import org.appcelerator.kroll.annotations.Kroll;
import org.appcelerator.titanium.TiApplication;
import org.appcelerator.titanium.proxy.TiViewProxy;
import org.appcelerator.titanium.view.TiUIView;
import org.appcelerator.kroll.common.AsyncResult;
import org.appcelerator.kroll.common.Log;
import org.appcelerator.kroll.common.TiConfig;
import org.appcelerator.kroll.common.TiMessenger;

import android.app.Activity;
import android.os.Handler;
import android.os.Message;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import static android.os.Build.VERSION.SDK_INT;

@Kroll.module(name="Androiduitools", id="org.camcops.androiduitools")
public class AndroiduitoolsModule extends KrollModule
{
	// Standard Debugging variables
	private static final String LCAT = "AndroiduitoolsModule";
	// private static final boolean DBG = TiConfig.LOGD; // Whether or not debug logging has been enabled by the Titanium application.
	private static final boolean DBG = true; // if(DBG) should be handled at compile time: http://stackoverflow.com/questions/1813853/ifdef-ifndef-in-java

	private static final int MSG_FULLSCREEN = 50000;
	private static final int MSG_FULLSCREEN_RECURSIVE = 50001;
	
	// You can define constants with @Kroll.constant, for example:
	// @Kroll.constant public static final String EXTERNAL_NAME = value;
	
	public AndroiduitoolsModule()
	{
		super();
	}

	@Kroll.onAppCreate
	public static void onAppCreate(TiApplication app)
	{
		// put module init code that needs to run when the application is created
	}

	// Methods
	
	@Kroll.method
	public void hideSystemUiTitaniumView(Object obj)
	{
		final String LFUNC = "hideSystemUiTitaniumView: ";
		// ActivityIndicatorProxy (extends TiViewProxy) provides TiUIActivityIndicator (extends TiUIView)
		// However, the thing that is returned by all Titanium create*() calls is a PROXY.
		// So the ways to pass it to a function are (a) passing a *Proxy or (b) passing an Object and checking.
		// TiViewProxy provides: public TiUIView getOrCreateView()
		// TiUIView provides: public View getNativeView()
		// TiUIActivityIndicator's constructor makes a LinearLayout and calls setNativeView with it.
		if (obj instanceof TiViewProxy) {
			if (DBG) Log.d(LCAT, LFUNC + 1);
			TiViewProxy tvp = (TiViewProxy) obj; 
			TiUIView tv = tvp.getOrCreateView();
			View v = tv.getNativeView();
			if (DBG) Log.d(LCAT, LFUNC + 2 + "tvp = " + tvp + ", tv = " + tv + ", v = " + v);
			hideSystemUi(v);
			if (DBG) Log.d(LCAT, LFUNC + 3);
		}
		else {
			Log.w(LCAT, "hideSystemUiTitaniumView() ignored. Expected a Titanium view object, got " + obj.getClass().getSimpleName());
		}
	}
	
	@Kroll.method
	public void setFullscreen()
	{
		// Could probably just use: hideSystemUi( TiApplication.getInstance().getCurrentActivity().getWindow().getDecorView() ); 

		final String LFUNC = "setFullscreen: ";
		
		// Get view
		// http://docs.appcelerator.com/titanium/2.1/#!/guide/Android_Module_Development_Guide
		// https://github.com/appcelerator/titanium_mobile/pull/793/files -- but TiApplication.getCurrentInstanceActivity() fails compilation as a deprecated method 
		TiApplication appContext = TiApplication.getInstance();
		if (appContext == null) {
			if (DBG) Log.d(LCAT, LFUNC + "appContext is null");
			return;
		}
		Activity a = appContext.getCurrentActivity();
		if (a == null) {
			if (DBG) Log.d(LCAT, LFUNC + "activity is null");
			return;
		}
		// https://github.com/appcelerator/titanium_mobile/blob/master/android/modules/media/src/java/ti/modules/titanium/media/MediaModule.java
		while (a.getParent() != null) {
			if (DBG) Log.d(LCAT, LFUNC + "moving from activity to its parent");
			a = a.getParent();
		}
		// http://developer.android.com/reference/android/app/Activity.html
		// http://developer.android.com/reference/android/view/Window.html
		// http://developer.android.com/reference/android/view/View.html
		// https://github.com/appcelerator/titanium_mobile/blob/master/android/modules/media/src/java/ti/modules/titanium/media/MediaModule.java
		Window w = a.getWindow();
		if (w == null) {
			if (DBG) Log.d(LCAT, LFUNC + "window is null");
			return;
		}
		while (w.getContainer() != null) {
			if (DBG) Log.d(LCAT, LFUNC + "moving from window to its container");
			w = w.getContainer();
		}
		View v = w.getDecorView();
		if (v == null) {
			if (DBG) Log.d(LCAT, LFUNC + "view is null");
			return;
		}
		
		// Set full-screen mode
		hideSystemUi(v);
		// setViewFullscreenIteratively(v);
	}

	// Internals
	
	private static final Handler statichandler = new Handler(TiMessenger.getMainMessenger().getLooper(), new Handler.Callback() {
		// Titanium adds an extra layer to the Android callbacks, taking over msg.obj.
		final String LFUNC = "Handler.Callback: ";
		@Override
		public boolean handleMessage(Message msg) 
		{
			if (msg.what == MSG_FULLSCREEN) {
				if (DBG) Log.d(LCAT, LFUNC + "MSG_FULLSCREEN received");
				AsyncResult result = (AsyncResult) msg.obj; // Titanium always takes over msg.obj
				View v = (View) result.getArg(); // ... but we can use this way to pass information
				hideSystemUi(v);
				result.setResult(null); // This ends the blocking call
				return true;
			}
			else if (msg.what == MSG_FULLSCREEN_RECURSIVE) {
				if (DBG) Log.d(LCAT, LFUNC + "MSG_FULLSCREEN_RECURSIVE received");
				AsyncResult result = (AsyncResult) msg.obj; // Titanium always takes over msg.obj
				View v = (View) result.getArg(); // ... but we can use this way to pass information
				setViewFullscreenIteratively(v);
				result.setResult(null); // This ends the blocking call
				return true;
			}
			if (DBG) Log.d(LCAT, LFUNC + "unknown message received");
			return false;
		}
	});
	
	// Next function pointless (setting the property on any view is good enough, I think) -
	// source code merely left here as a methods example
	private static void setViewFullscreenIteratively(View v) {
		final String LFUNC = "setViewFullscreenIteratively: ";
		// 0. Ensure View not null
		if (v == null) {
			if (DBG) Log.d(LCAT, LFUNC + "view is null pointer");
			return;
		}
		if (DBG) Log.d(LCAT, LFUNC + "id=" + v.getId());
		// 1. Ensure on UI thread
		if (!TiApplication.isUIThread()) {
			if (DBG) Log.d(LCAT, LFUNC + "not on UI thread: passing request on to UI thread");
			TiMessenger.sendBlockingMainMessage(statichandler.obtainMessage(MSG_FULLSCREEN_RECURSIVE), v);
			return;
		}
		// 2. Set it recursively
		hideSystemUi(v);
		if (v instanceof ViewGroup) {
			final ViewGroup vg = (ViewGroup) v;
			final int childCount = vg.getChildCount();
			for (int i = 0; i < childCount; ++i) {
				setViewFullscreenIteratively( vg.getChildAt(i) );
			}
		}
	}

	// Public and static (so the proxy can use it), but not a Kroll method, so Javascript can't
	public static void hideSystemUi(View v) 
	{
		final String LFUNC = "hideSystemUi (SDK=" + SDK_INT + "): ";
		// if (DBG) Log.d(LCAT, LFUNC + "hideSystemUi 1");
		// 0. Ensure View not null
		if (v == null) {
			if (DBG) Log.d(LCAT, LFUNC + "view is null pointer");
			return;
		}
		// if (DBG) Log.d(LCAT, LFUNC + "hideSystemUi 2");
		if (DBG) Log.d(LCAT, LFUNC + "id=" + v.getId());
		// if (DBG) Log.d(LCAT, LFUNC + "hideSystemUi 3");
		// 1. Ensure on UI thread
		if (!TiApplication.isUIThread()) {
			if (DBG) Log.d(LCAT, LFUNC + "not on UI thread: passing request on to UI thread");
			TiMessenger.sendBlockingMainMessage(statichandler.obtainMessage(MSG_FULLSCREEN), v);
			return;
		}
		// 2. Determine visibility to set
		int newVis;
		if (SDK_INT >= 16) {
			newVis = View.SYSTEM_UI_FLAG_LOW_PROFILE;
			// Consider these flags:
			//		View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
            // 		View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            // 		View.SYSTEM_UI_FLAG_LAYOUT_STABLE
			// 		View.SYSTEM_UI_FLAG_LOW_PROFILE 
			// 		View.SYSTEM_UI_FLAG_FULLSCREEN
            // 		View.SYSTEM_UI_FLAG_HIDE_NAVIGATION;
			// Don't use View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN, or *all* touches are intercepted
			// to make the system UI visible.
			
		}
		else if (SDK_INT >= 14) {
			newVis = View.SYSTEM_UI_FLAG_LOW_PROFILE;
	    }
		else if (SDK_INT >= 11) {
			newVis = View.STATUS_BAR_HIDDEN;
	    }
		else {
			// old SDK
			if (DBG) Log.d(LCAT, LFUNC + "old SDK - unable to do anything");
			return;
		}
		// 3. Set visibility
		if (DBG) Log.d(LCAT, LFUNC + "view width = " + v.getWidth() + ", height = " + v.getHeight() );
		// ... works fine even if height/width zero
		if (DBG) Log.d(LCAT, LFUNC + "BEFORE: getSystemUiVisibility: " + v.getSystemUiVisibility());
		if (DBG) Log.d(LCAT, LFUNC + "setting visibility=" + newVis);
		v.setSystemUiVisibility(0); // trying http://stackoverflow.com/questions/11027193/maintaining-lights-out-mode-view-setsystemuivisibility-across-restarts
		v.setSystemUiVisibility(newVis);
		if (DBG) Log.d(LCAT, LFUNC + "AFTER: getSystemUiVisibility: " + v.getSystemUiVisibility());
	}
	
	public static boolean systemUiAlreadyInvisible(int visibility) 
	{
		if (SDK_INT >= 16) {
			return (visibility & View.SYSTEM_UI_FLAG_LOW_PROFILE) != 0;
		}
		else if (SDK_INT >= 14) {
			return (visibility & View.SYSTEM_UI_FLAG_LOW_PROFILE) != 0;
		}
		else if (SDK_INT >= 11) {
			return (visibility & View.STATUS_BAR_HIDDEN) != 0;
		}
		// if we get here: old SDK
		return true; // nothing we can do about it anyway
	}
	
	private static void disableMenu(Activity a) 
	{
		if (DBG) Log.d(LCAT, "disableMenu: about to call a.invalidateOptionsMenu");
		a.invalidateOptionsMenu();
	}
	
}
