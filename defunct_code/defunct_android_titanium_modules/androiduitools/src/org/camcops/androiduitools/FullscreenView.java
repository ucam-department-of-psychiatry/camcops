// FullscreenView.java

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

import java.util.Timer;
import java.util.TimerTask;

import org.appcelerator.kroll.KrollDict;
import org.appcelerator.kroll.KrollEventCallback;
import org.appcelerator.titanium.TiC;
import org.appcelerator.titanium.proxy.TiViewProxy;
import org.appcelerator.titanium.util.Log;
import org.appcelerator.titanium.util.TiConvert;
import org.appcelerator.titanium.view.TiCompositeLayout;
import org.appcelerator.titanium.view.TiUIView;
import org.appcelerator.titanium.view.TiCompositeLayout.LayoutArrangement;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.view.View;

public class FullscreenView
	extends TiUIView
	implements View.OnFocusChangeListener, View.OnSystemUiVisibilityChangeListener, View.OnClickListener
{
	private static final String LCAT = "FullscreenView";
	private static final boolean DBG = true; // if(DBG) should be handled at compile time: http://stackoverflow.com/questions/1813853/ifdef-ifndef-in-java
	private int m_timeoutMs = 1000;
	private Timer fullscreenTimer = new Timer();

	//-------------------------------------------------------------------------
	// Private classes
	//-------------------------------------------------------------------------

	// Attempt to capture events by deriving directly from the Android View
	private class FullscreenAndroidView
		extends View
	{
		public FullscreenAndroidView(Context context)
		{
			super(context);
			if (DBG) Log.d(LCAT, "FullscreenAndroidView constructor " + this);
			// setRotation(20); // does nothing
		}
		
		@Override
		protected void onAttachedToWindow()
		{
			super.onAttachedToWindow();
			if (DBG) Log.d(LCAT, "onAttachedToWindow");
		}
		
		@Override
		protected void onDetachedFromWindow()
		{
			super.onDetachedFromWindow();
			if (DBG) Log.d(LCAT, "onDetachedFromWindow");
		}
		
		@Override
		protected void onVisibilityChanged(View changedView, int visibility)
		{
			super.onVisibilityChanged(changedView, visibility);
			if (DBG) Log.d(LCAT, "onVisibilityChanged");
		}
		
		@Override
		protected void onWindowVisibilityChanged(int visibility)
		{
			super.onWindowVisibilityChanged(visibility);
			if (DBG) Log.d(LCAT, "onWindowVisibilityChanged");
		}
		
		@Override
		protected void onDraw(Canvas canvas)
		{
			super.onDraw(canvas);
			if (DBG) Log.d(LCAT, "onDraw");
		}
		
		@Override
		protected void onLayout(boolean changed, int left, int top, int right, int bottom)
		{
			super.onLayout(changed, left, top, right, bottom);
			if (DBG) Log.d(LCAT, "onLayout");
		}
	}
	
	private class CloseCallback implements KrollEventCallback
	{
		@Override
		public void call(Object data) 
		{
			if (DBG) Log.d(LCAT, "FullscreenView: close event received, id=" + nativeView.getId());
			clearTimer();
		}
	}
	
	private class OpenCallback implements KrollEventCallback 
	{
		@Override
		public void call(Object data) 
		{
			if (DBG) Log.d(LCAT, "FullscreenView: open event received, id=" + nativeView.getId());
			AndroiduitoolsModule.hideSystemUi(nativeView);
		}
	}
	
	//-------------------------------------------------------------------------
	// Listeners
	//-------------------------------------------------------------------------

	// OnFocusChangeListener
	@Override
	public void onFocusChange(View v, boolean hasFocus) {
		super.onFocusChange(v, hasFocus);
		if (DBG) Log.d(LCAT, "View id=" + v.getId() + ", onFocusChange, hasFocus=" + hasFocus);
		if (hasFocus) AndroiduitoolsModule.hideSystemUi(v);
	}

	// OnSystemUiVisibilityChangeListener
	@Override
	public void onSystemUiVisibilityChange(int visibility) 
	{
		if (DBG) Log.d(LCAT, "FullscreenView onSystemUiVisibilityChange: visibility = " + visibility + ", id=" + nativeView.getId());
		if (AndroiduitoolsModule.systemUiAlreadyInvisible(visibility))
		{
			if (DBG) Log.d(LCAT, "... already invisible, nothing to do, id=" + nativeView.getId());
			return;
		}
		// Cancel any existing scheduled calls, and set up a new timer. (I don't think a timer is re-usable after cancelling it.)
		clearTimer();
		fullscreenTimer = new Timer();
		fullscreenTimer.schedule(new TimerTask() 
			{
				@Override
				public void run()
				{
					if (nativeView == null) return;
					if (DBG) Log.d(LCAT, "FullscreenView TimerTask run, id=" + nativeView.getId());
					AndroiduitoolsModule.hideSystemUi(nativeView);
				}
			}, m_timeoutMs);
	}

	// OnClickListener
	@Override
	public void onClick(View v)
	{
		if (DBG) Log.d(LCAT, "FullscreenView onClick, id=" + nativeView.getId());
		AndroiduitoolsModule.hideSystemUi(v);
	}

	//-------------------------------------------------------------------------
	// Constructor
	//-------------------------------------------------------------------------

	public FullscreenView(TiViewProxy proxy)
	{
		super(proxy);
		if (DBG) Log.d(LCAT, "FullscreenView constructor");
		
		Activity activity = proxy.getActivity();
		
		View nv = new FullscreenAndroidView(activity);
		setNativeView(nv);
		
		LayoutArrangement arrangement = LayoutArrangement.DEFAULT;
		if (proxy.hasProperty(TiC.PROPERTY_LAYOUT))
		{
			String layoutProperty = TiConvert.toString(proxy.getProperty(TiC.PROPERTY_LAYOUT));
			if (layoutProperty.equals(TiC.LAYOUT_HORIZONTAL)) 
			{
				arrangement = LayoutArrangement.HORIZONTAL;
			}
			else if (layoutProperty.equals(TiC.LAYOUT_VERTICAL)) 
			{
				arrangement = LayoutArrangement.VERTICAL;
			}
		}
		setNativeView(new TiCompositeLayout(activity, arrangement));
		// TiCompositeLayout extends android.view.ViewGroup
		// ... incidentally, bug in it (using LayoutArrangement.DEFAULT even if a LayoutArrangement is passed)?
		// setNativeView() calls doSetClickable(nativeView, ...) calls setOnClickListener(view) calls android.view.View.setOnClickListener

		AndroiduitoolsModule.hideSystemUi(nativeView);
		
		nativeView.setOnClickListener(this);
		// setOnClickListener also makes the view clickable: http://developer.android.com/reference/android/view/View.html#setOnClickListener
		// problems... https://developer.appcelerator.com/question/131031/failed-to-add-onclicklistener-to-native-view-in-android-module
		nativeView.setOnSystemUiVisibilityChangeListener(this);
		nativeView.setOnFocusChangeListener(this);
		proxy.addEventListener(TiC.EVENT_CLOSE, new CloseCallback() );
		proxy.addEventListener(TiC.EVENT_OPEN, new OpenCallback() );
		
	}
	
	//-------------------------------------------------------------------------
	// Ancillary functions
	//-------------------------------------------------------------------------

	public void goFullscreen()
	{
		AndroiduitoolsModule.hideSystemUi(nativeView);
	}
	
	private void clearTimer()
	{
		if (DBG) Log.d(LCAT, "clearTimer, id=" + nativeView.getId());
		fullscreenTimer.cancel();
		fullscreenTimer.purge();
	}
	
	//-------------------------------------------------------------------------
	// Properties
	//-------------------------------------------------------------------------

	@Override
	public void processProperties(KrollDict d)
	{
		super.processProperties(d);
	}
	
	public void setTimeoutMs(int timeoutMs)
	{
	    m_timeoutMs = timeoutMs;
	}
	
	public int getTimeoutMs()
	{
		return m_timeoutMs;
	}
}
