// FullscreenViewProxy.java

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
import org.appcelerator.kroll.KrollProxy;
import org.appcelerator.kroll.annotations.Kroll;
import org.appcelerator.titanium.TiC;
import org.appcelerator.titanium.util.Log;
import org.appcelerator.titanium.util.TiConfig;
import org.appcelerator.titanium.util.TiConvert;
import org.appcelerator.titanium.proxy.TiViewProxy;
import org.appcelerator.titanium.view.TiCompositeLayout;
import org.appcelerator.titanium.view.TiCompositeLayout.LayoutArrangement;
import org.appcelerator.titanium.view.TiUIView;

import android.app.Activity;

// This proxy can be created by calling Androiduitools.createFullscreenView({message: "hello world"})
@Kroll.proxy(creatableInModule=AndroiduitoolsModule.class)
public class FullscreenViewProxy extends TiViewProxy
{
	// Standard Debugging variables
	private static final String LCAT = "FullscreenViewProxy";
	private static final boolean DBG = true; // if(DBG) should be handled at compile time: http://stackoverflow.com/questions/1813853/ifdef-ifndef-in-java
	
	// Constructor
	public FullscreenViewProxy()
	{
		super();
	}

	@Override
	public TiUIView createView(Activity activity)
	{
		TiUIView view = new FullscreenView(this);
		view.getLayoutParams().autoFillsHeight = true;
		view.getLayoutParams().autoFillsWidth = true;
		return view;
	}

	// Handle creation options
	@Override
	public void handleCreationDict(KrollDict options)
	{
		super.handleCreationDict(options);
		
		if (options.containsKey("timeoutMs")) 
		{
			if (DBG) Log.d(LCAT, "FullscreenView created with timeoutMs: " + options.get("timeoutMs"));
			setTimeoutMs( options.getInt("timeoutMs").intValue() ); // ... convert Integer to int
		}
	}
	
	// Internals
	private FullscreenView getFullscreenView()
	{
		return (FullscreenView) getOrCreateView();
	}
	
	/* The events we actually see are "click" and (mostly) "load"
	@Override
	public boolean fireEvent(String eventName, Object data) {
		if (DBG) Log.d(LCAT,  "EVENT!!! - " + eventName);
		if (eventName.equals(TiC.EVENT_OPEN)) 
		{
			if (DBG) Log.d(LCAT,  "OPEN EVENT!!!");
		}
		else if (eventName.equals(TiC.EVENT_CLOSE)) 
		{
			if (DBG) Log.d(LCAT,  "CLOSE EVENT!!!");
		}

		return super.fireEvent(eventName, data);
	}
	*/

	// Methods
	@Kroll.getProperty @Kroll.method
	public int getTimeoutMs()
	{
		FullscreenView fv = getFullscreenView();
        return fv.getTimeoutMs();
	}

	@Kroll.setProperty @Kroll.method
	public void setTimeoutMs(int timeoutMs)
	{
	    if (DBG) Log.d(LCAT, "Setting timeoutMs to: " + timeoutMs);
	    FullscreenView fv = getFullscreenView();
	    fv.setTimeoutMs(timeoutMs);
	}

	@Kroll.method
	public void goFullscreen()
	{
		if (DBG) Log.d(LCAT, "goFullscreen()");
		FullscreenView fv = getFullscreenView();
		fv.goFullscreen();
	}
	
}
