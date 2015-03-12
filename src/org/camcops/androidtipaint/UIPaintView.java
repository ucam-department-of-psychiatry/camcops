/**
 * Ti.Paint Module
 * Copyright (c) 2010-2013 by Appcelerator, Inc. All Rights Reserved.
 * Please see the LICENSE included with this distribution for details.
 */

// RNC // package ti.modules.titanium.paint;
package org.camcops.androidtipaint; // RNC

import java.io.ByteArrayOutputStream;

import org.appcelerator.kroll.KrollDict;
import org.appcelerator.kroll.common.AsyncResult;
import org.appcelerator.kroll.common.Log;
import org.appcelerator.kroll.common.TiMessenger;
import org.appcelerator.titanium.TiC;
import org.appcelerator.titanium.proxy.TiViewProxy;
import org.appcelerator.titanium.TiApplication;
import org.appcelerator.titanium.util.TiConvert;
import org.appcelerator.titanium.view.TiDrawableReference;
import org.appcelerator.titanium.util.TiUIHelper;
import org.appcelerator.titanium.view.TiUIView;

import android.content.Context;
import android.graphics.*;
import android.graphics.Bitmap.CompressFormat;
import android.os.Handler;
import android.os.Looper;
import android.os.Message;
import android.view.MotionEvent;
import android.view.View;

public class UIPaintView extends TiUIView implements Handler.Callback // RNC
{
	private static final String LCAT = "UIPaintView";

	public Paint tiPaint;
	public PaintView tiPaintView;
	private KrollDict props;
	private Boolean eraseState = false;
    private Boolean readOnly = false; // RNC
	private int alphaState = 255; // alpha resets on changes, so store
    private Handler mainHandler = new Handler(Looper.getMainLooper(), this);
    private int requestedWidth = 0;
    private int requestedHeight = 0;

	public UIPaintView(TiViewProxy proxy) {
		super(proxy);
        Log.d(LCAT, "UIPaintView constructor");

		props = proxy.getProperties();

		setPaintOptions(); // set initial paint options

        if (props.containsKeyAndNotNull("requestedWidth")) {
            // RNC
            requestedWidth = props.getInt("requestedWidth");
        }
        if (props.containsKeyAndNotNull("requestedHeight")) {
            // RNC
            requestedHeight = props.getInt("requestedHeight");
        }

		setNativeView(tiPaintView = new PaintView(proxy.getActivity(), requestedWidth, requestedHeight));

		if (props.containsKeyAndNotNull("image")) {
            Log.d(LCAT, "UIPaintView constructor: setting initial image");
			tiPaintView.setImage(props.getString("image"));
		}
        readOnly = props.optBoolean("readOnly", false); // RNC
        Log.d(LCAT, "UIPaintView constructor: finished.");
	}

	private void setPaintOptions() {
		tiPaint = new Paint();
		tiPaint.setAntiAlias(true);
		tiPaint.setDither(true);
		tiPaint.setColor((props.containsKeyAndNotNull("strokeColor")) ? TiConvert.toColor(props, "strokeColor") : TiConvert.toColor("black"));
		tiPaint.setStyle(Paint.Style.STROKE);
		tiPaint.setStrokeJoin(Paint.Join.ROUND);
		tiPaint.setStrokeCap(Paint.Cap.ROUND);
		tiPaint.setStrokeWidth((props.containsKeyAndNotNull("strokeWidth")) ? TiConvert.toFloat(props.get("strokeWidth")) : 12);
		tiPaint.setAlpha((props.containsKeyAndNotNull("strokeAlpha")) ? TiConvert.toInt(props.get("strokeAlpha")) : 255);
		alphaState = (props.containsKeyAndNotNull("strokeAlpha")) ? TiConvert.toInt(props.get("strokeAlpha")) : 255;
	}

	public void setStrokeWidth(Float width) {
		Log.d(LCAT, "Changing stroke width.");
		tiPaintView.finalizePaths();
		tiPaint.setStrokeWidth(width);
		tiPaint.setAlpha(alphaState);
	}

	public void setEraseMode(Boolean toggle) {
		eraseState = toggle;
		tiPaintView.finalizePaths();

		if (eraseState) {
			Log.d(LCAT, "Setting Erase Mode to True.");
			tiPaint.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.CLEAR));
		} else {
			Log.d(LCAT, "Setting Erase Mode to False.");
			tiPaint.setXfermode(null);
		}

		tiPaint.setAlpha(alphaState);
	}
    
    public void setReadOnly(Boolean state) {
        readOnly = state;
        tiPaintView.finalizePaths();
    }

	public void setStrokeColor(String color) {
		Log.d(LCAT, "Changing stroke color.");
		tiPaintView.finalizePaths();
		tiPaint.setColor(TiConvert.toColor(color));
		tiPaint.setAlpha(alphaState);
	}

	public void setStrokeAlpha(int alpha) {
		Log.d(LCAT, "Changing stroke alpha.");
		tiPaintView.finalizePaths();
		tiPaint.setAlpha(alpha);
		alphaState = alpha;
	}

	public void setImage(String imagePath) {
		Log.d(LCAT, "Changing image.");
		// RNC // tiPaintView.setImage(imagePath);
        if (!TiApplication.isUIThread()) {
            Log.d(LCAT, "setImage: !TiApplication.isUIThread()");
            TiMessenger.sendBlockingMainMessage(mainHandler.obtainMessage(MSG_SET_IMAGE), imagePath);
        } else {
            Log.d(LCAT, "setImage: TiApplication.isUIThread()");
            tiPaintView.setImage(imagePath);
        }
	}

	public void clear() {
		Log.d(LCAT, "Clearing.");
        if (!TiApplication.isUIThread()) {
            TiMessenger.sendBlockingMainMessage(mainHandler.obtainMessage(MSG_CLEAR));
        } else {
            tiPaintView.clear();
        }
	}
    
    public KrollDict getImage() {
        if (tiPaintView == null) {
            Log.d(LCAT, "getImage: tiPaintView == null");
            return null;
        }
        if (!TiApplication.isUIThread()) {
            Log.d(LCAT, "getImage: !TiApplication.isUIThread()");
            return (KrollDict) TiMessenger.sendBlockingMainMessage(mainHandler.obtainMessage(MSG_GET_IMAGE));
        } else {
            Log.d(LCAT, "getImage: TiApplication.isUIThread()");
            return handleGetImage();
        }
    }
    
    protected KrollDict handleGetImage() {
        // See TIUIHelper.viewToImage
        KrollDict imagedict = new KrollDict();
        int width = tiPaintView.getOutputWidth();
        int height = tiPaintView.getOutputHeight();
        Bitmap bitmap = tiPaintView.getOutputBitmap();
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        if (bitmap.compress(CompressFormat.PNG, 100, bos)) {
            imagedict = TiUIHelper.createDictForImage(width, height, bos.toByteArray());
        }
        bitmap.recycle();
        return imagedict;
    }

    public Boolean getDirty() {
        if (tiPaintView == null) {
            Log.d(LCAT, "getDirty: tiPaintView == null");
            return false;
        }
        if (!TiApplication.isUIThread()) {
            Log.d(LCAT, "getDirty: !TiApplication.isUIThread()");
            return (Boolean) TiMessenger.sendBlockingMainMessage(mainHandler.obtainMessage(MSG_GET_DIRTY));
        } else {
            Log.d(LCAT, "getDirty: TiApplication.isUIThread()");
            return tiPaintView.getDirty();
        }
    }
    
	private static final int MSG_CLEAR = 10001;
    private static final int MSG_SET_IMAGE = 10002;
    private static final int MSG_GET_IMAGE = 10003;
    private static final int MSG_GET_DIRTY = 10004;
    // RNC: see also e.g. https://github.com/appcelerator/titanium_mobile/blob/master/android/titanium/src/java/org/appcelerator/titanium/proxy/MenuProxy.java
    // RNC: ... http://docs.appcelerator.com/module-apidoc/latest/android/org/appcelerator/kroll/common/TiMessenger.html
    // RNC: ... TiViewProxy.java
    // RNC: ... KrollContext.java
    // RNC: ... TiUIImageView.java, ImageViewProxy.java (ESPECIALLY)

	public boolean handleMessage(Message msg)
	{
		switch(msg.what) {

            case MSG_CLEAR: {
                Log.d(LCAT, "handleMessage: MSG_CLEAR");
                AsyncResult result = (AsyncResult) msg.obj;
                tiPaintView.clear();
                result.setResult(null);
                return true;
            }

            case MSG_SET_IMAGE: {
                Log.d(LCAT, "handleMessage: MSG_SET_IMAGE");
                AsyncResult result = (AsyncResult) msg.obj;
                tiPaintView.setImage((String) result.getArg());
                result.setResult(null);
                return true;
            }
            
            case MSG_GET_IMAGE: {
                Log.d(LCAT, "handleMessage: MSG_GET_IMAGE");
				AsyncResult result = (AsyncResult) msg.obj;
				result.setResult(handleGetImage());
				return true;
            }
            
            case MSG_GET_DIRTY: {
                Log.d(LCAT, "handleMessage: MSG_GET_DIRTY");
				AsyncResult result = (AsyncResult) msg.obj;
				result.setResult(tiPaintView.getDirty());
				return true;
            }

            default:
                return false;
        }
	}

	public class PaintView extends View {

		private static final int maxTouchPoints = 20;

		private float[] tiX;
		private float[] tiY;

		private Path[] tiPaths;
		private Bitmap tiBitmap;
		private String tiImage;
		private Canvas tiCanvas;
		private Paint tiBitmapPaint;
        
        private int requested_w = 0; // set by constructor: request from calling framework to override file size
        private int requested_h = 0;
        private int view_w = 0; // current size of our view
        private int view_h = 0;
        private int sourcebitmap_w = 0; // size of our source bitmap
        private int sourcebitmap_h = 0;
        private int active_w = 0; // size of the active area
        private int active_h = 0;
        private int output_w = 0; // size of the returned bitmap
        private int output_h = 0;
        
        private Boolean dirty = false;

		public PaintView(Context c, int requestedWidth, int requestedHeight) {
			super(c);
            requested_w = requestedWidth;
            requested_h = requestedHeight;
			tiBitmapPaint = new Paint(Paint.DITHER_FLAG);
			tiPaths = new Path[maxTouchPoints];
			tiX = new float[maxTouchPoints];
			tiY = new float[maxTouchPoints];
		}

		@Override
		protected void onSizeChanged(int w, int h, int oldw, int oldh) {
			super.onSizeChanged(w, h, oldw, oldh);
            Log.d(LCAT, "onSizeChanged");
            view_w = w;
            view_h = h;
            calculateSizes();
            // We don't return to our source bitmap! This might be a rotate operation; we copy (and potentially rescale) our existing bitmap.
            tiBitmap = Bitmap.createScaledBitmap(tiBitmap.copy(Bitmap.Config.ARGB_8888, true), active_w, active_h, true); // RNC: ensure it's mutable
			tiCanvas = new Canvas(tiBitmap);
		}
        
        protected void calculateSizes() {
            if (sourcebitmap_w > 0 && sourcebitmap_h > 0) {
                // We have a source image.
                // Now, scale bitmap to fit available area sensibly, by setting active_w/active_h
                float scale_w = (float) view_w / sourcebitmap_w;
                float scale_h = (float) view_h / sourcebitmap_h;
                float final_scale = (scale_w < scale_h ? scale_w : scale_h);
                active_w = (int) (final_scale * sourcebitmap_w);
                active_h = (int) (final_scale * sourcebitmap_h);
                output_w = (requested_w > 0 ? requested_w : sourcebitmap_w);
                output_h = (requested_h > 0 ? requested_h : sourcebitmap_h);
            }
            else {
                // No source image. We'll operate in the size available to us.
                active_w = view_w;
                active_h = view_h;
                output_w = (requested_w > 0 ? requested_w : view_w);
                output_h = (requested_h > 0 ? requested_h : view_h);
            }
        }
        
        public int getOutputWidth() {
            return output_w;
        }
        
        public int getOutputHeight() {
            return output_h;
        }

        public Bitmap getOutputBitmap() {
            // Our Canvas has been busy drawing into tiBitmap.
            // Now we want it rescaled to the output size:
            return Bitmap.createScaledBitmap(tiBitmap.copy(Bitmap.Config.ARGB_8888, true), output_w, output_h, true);
        }
        
        public Boolean getDirty() {
            return dirty;
        }
        
		@Override
		protected void onDraw(Canvas canvas) {
			boolean containsBG = props.containsKeyAndNotNull(TiC.PROPERTY_BACKGROUND_COLOR);
			canvas.drawColor(containsBG ? TiConvert.toColor(props, TiC.PROPERTY_BACKGROUND_COLOR) : TiConvert.toColor("transparent"));
			canvas.drawBitmap(tiBitmap, 0, 0, tiBitmapPaint);

			for (int i = 0; i < maxTouchPoints; i++) {
				if (tiPaths[i] != null) {
					canvas.drawPath(tiPaths[i], tiPaint);
				}
			}
		}

		private void touch_start(int id, float x, float y) {
			tiPaths[id] = new Path();
			tiPaths[id].moveTo(x, y);
			tiX[id] = x;
			tiY[id] = y;
		}

		private void touch_move(int id, float x, float y) {
			if (tiPaths[id] == null) {
				tiPaths[id] = new Path();
				tiPaths[id].moveTo(tiX[id], tiY[id]);
			}
			tiPaths[id].quadTo(tiX[id], tiY[id], (x + tiX[id]) / 2, (y + tiY[id]) / 2);
			tiX[id] = x;
			tiY[id] = y;
		}

		@Override
		public boolean onTouchEvent(MotionEvent mainEvent) {
            if (readOnly) {
                return true;
            }
			for (int i = 0; i < mainEvent.getPointerCount(); i++) {
				int id = mainEvent.getPointerId(i);
				float x = mainEvent.getX(i);
				float y = mainEvent.getY(i);
				int action = mainEvent.getAction();
				if (action > 6) {
					action = (action % 256) - 5;
				}
				switch (action) {
					case MotionEvent.ACTION_DOWN:
						finalizePath(id);
						touch_start(id, x, y);
						invalidate();
                        dirty = true;
						break;
					case MotionEvent.ACTION_MOVE:
						touch_move(id, x, y);
						invalidate();
                        dirty = true;
						break;
					case MotionEvent.ACTION_UP:
						finalizePath(id);
						invalidate();
                        dirty = true;
						break;
				}
			}
			return true;
		}

		public void finalizePath(int id) {
			if (tiPaths[id] != null) {
				tiCanvas.drawPath(tiPaths[id], tiPaint);
				tiPaths[id].reset();
				tiPaths[id] = null;
			}
		}
		
		public void finalizePaths() {
			for (int i = 0; i < maxTouchPoints; i++) {
				if (tiPaths[i] != null) {
					tiCanvas.drawPath(tiPaths[i], tiPaint);
					tiPaths[i].reset();
					tiPaths[i] = null;
				}
			}
		}

		public void setImage(String imagePath) {
			tiImage = imagePath;
			if (tiImage == null) {
                Log.i(LCAT, "setImage called: blank");
                sourcebitmap_w = 0;
                sourcebitmap_h = 0;
				clear();
			} else {
                Log.i(LCAT, "setImage called: loading image");
				finalizePaths();
				TiDrawableReference ref = TiDrawableReference.fromUrl(proxy, tiImage);
                Bitmap sourceBitmap = ref.getBitmap();
                sourcebitmap_w = sourceBitmap.getWidth();
                sourcebitmap_h = sourceBitmap.getHeight();
                view_w = getWidth();
                view_h = getHeight();
                calculateSizes();
                if (active_w > 0 && active_h > 0) {
                    // If we know our width/height...
                    tiBitmap = Bitmap.createScaledBitmap(sourceBitmap.copy(Bitmap.Config.ARGB_8888, true), active_w, active_h, true);
                }
                else {
                    // Width/height unset as yet (e.g. on creation)
                    tiBitmap = sourceBitmap.copy(Bitmap.Config.ARGB_8888, true);
                }
                sourceBitmap.recycle();
				tiCanvas = new Canvas(tiBitmap);
				invalidate();
			}
            dirty = false;
		}

		public void clear() {
			finalizePaths();
			tiBitmap.eraseColor(Color.TRANSPARENT);
			invalidate();
		}
	}

}
