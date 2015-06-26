/**
 * Ti.Paint Module
 * Copyright (c) 2010-2013 by Appcelerator, Inc. All Rights Reserved.
 * Please see the LICENSE included with this distribution for details.
 */

// RNC // package ti.modules.titanium.paint;
package org.camcops.androidtipaint; // RNC

import org.appcelerator.kroll.common.Log; // RNC

import org.appcelerator.kroll.annotations.Kroll;
import org.appcelerator.kroll.common.AsyncResult;
import org.appcelerator.kroll.common.TiMessenger;
import org.appcelerator.kroll.KrollDict;
import org.appcelerator.titanium.proxy.TiViewProxy;
import org.appcelerator.titanium.view.TiUIView;

import android.app.Activity;

@Kroll.proxy(creatableInModule = PaintModule.class)
public class PaintViewProxy extends TiViewProxy {
	private UIPaintView paintView;
    private static final String LCAT = "PaintViewProxy"; // RNC

	public PaintViewProxy() {
		super();
	}

	@Override
	public TiUIView createView(Activity activity) {
		paintView = new UIPaintView(this);
		return paintView;
	}

	@Kroll.setProperty
	@Kroll.method
	public void setStrokeWidth(Float width) {
		paintView.setStrokeWidth(width);
	}

	@Kroll.setProperty
	@Kroll.method
	public void setStrokeColor(String color) {
		paintView.setStrokeColor(color);
	}

	@Kroll.setProperty
	@Kroll.method
	public void setStrokeAlpha(int alpha) {
		paintView.setStrokeAlpha(alpha);
	}

	@Kroll.setProperty
	@Kroll.method
	public void setEraseMode(Boolean toggle) {
		paintView.setEraseMode(toggle);
	}

	@Kroll.setProperty
	@Kroll.method
	public void setReadOnly(Boolean state) {
		paintView.setReadOnly(state);
	}

	@Kroll.setProperty
	@Kroll.method
	public void setImage(String imagePath) {
		// RNC // paintView.setImage(imagePath);
        // RNC:
		if (paintView != null) {
            Log.d(LCAT, "setImage: paintView != null");
            paintView.setImage(imagePath);
		}
        else {
            Log.d(LCAT, "setImage: paintView == null; ignoring setImage request");
        }
	}
    
    @Kroll.getProperty
    @Kroll.method
    public Boolean getDirty() {
        return paintView.getDirty();
    }
    
    @Kroll.getProperty
    @Kroll.method
    public KrollDict getImage() {
        return paintView.getImage();
    }

	@Kroll.method
	public void clear() {
		if (paintView != null) {
            paintView.clear();
		}
	}
    
    // Kroll runOnUIThread appears to have been deprecated: https://jira.appcelerator.org/browse/TIMOB-6589
    // Previously (e.g. ImageViewProxy.java): @Kroll.setProperty(runOnUiThread=true) @Kroll.method(runOnUiThread=true)

}
