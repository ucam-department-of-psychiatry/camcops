/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/


package org.camcops.camcops;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.content.res.Configuration;
import android.util.Log;

import java.lang.String;
import java.lang.StringBuilder;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.qtproject.qt.android.bindings.QtActivity;
import org.qtproject.qt.android.bindings.QtApplication;

public class CamcopsActivity extends QtActivity
{
    /* Handle application launch from a hyperlink
     * e.g. https://ucam-department-of-psychiatry.github.io/camcops/register/?default_single_user_mode=true&default_server_location=https%3A%2F%2Fserver.example.com%2Fapi&default_access_key=abcde-fghij-klmno-pqrst-uvwxy-zabcd-efghi-jklmn-o
     * If no instance of the app is running, onCreate() is called and we pass
     * the URL parameters as arguments to the app's main().
     * If the app is already running, onNewIntent() is called and the URL
     * parameters are sent as signals to the app via UrlHandler.
    */

    private static final String TAG = "camcops";

    // Defined in urlhandler.cpp
    public static native void handleAndroidUrl(String url);

    @Override
    public void onCreate(Bundle savedInstanceState) {
        // Called when no instance of the app is running. Pass URL parameters
        // as arguments to the app's main()
        Intent intent = getIntent();

        Log.i(TAG, "onCreate");

        if (intent != null && intent.getAction() == Intent.ACTION_VIEW) {
            Uri uri = intent.getData();
            if (uri != null) {
                Log.i(TAG, intent.getDataString());

                Map<String, String> parameters = getQueryParameters(uri);

                // String.join() not available at runtime
                StringBuilder sb = new StringBuilder();

                String separator = "";
                for (Map.Entry<String, String> entry : parameters.entrySet()) {
                    String name = entry.getKey();
                    String value = entry.getValue();
                    if (value != null) {
                        sb.append(separator)
                            .append("--").append(name)
                            .append("=").append(value);

                        separator = "\t";
                    }
                }

                APPLICATION_PARAMETERS = sb.toString();
            }
        }

        super.onCreate(savedInstanceState);
    }

    @Override
    public void onNewIntent(Intent intent) {
        /* Called when the app is already running. Send the URL parameters
         * as signals to the app. If the user has already registered manually,
         * this will have no effect.
         */
        Log.i(TAG, "onNewIntent");

        super.onNewIntent(intent);

        sendUrlToApp(intent);
    }

    private void sendUrlToApp(Intent intent) {
        String url = intent.getDataString();

        if (url != null) {
            Log.i(TAG, url);

            handleAndroidUrl(url);
        }
    }

    private Map<String, String> getQueryParameters(Uri uri) {
        List<String> names = Arrays.asList("default_single_user_mode",
                                           "default_server_location",
                                           "default_access_key");

        Map<String, String> parameters = new HashMap<String, String>();

        for (String name : names) {
            String value = uri.getQueryParameter(name);
            if (value != null) {
                parameters.put(name, value);
            }
        }

        return parameters;
    }

    public void onConfigurationChanged(Configuration newConfig) {
        // https://bugreports.qt.io/browse/QTBUG-38971
        // SuperNotCalled exception on orientation change
        super_onConfigurationChanged(newConfig);
        QtApplication.invokeDelegate(newConfig);
    }
}
