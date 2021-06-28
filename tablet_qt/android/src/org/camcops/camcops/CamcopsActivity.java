/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
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

import org.qtproject.qt5.android.bindings.QtActivity;
import org.qtproject.qt5.android.bindings.QtApplication;

public class CamcopsActivity extends QtActivity
{
    private static final String TAG = "camcops";

    // Handle application launch from a hyperlink
    // e.g. http://camcops/?default_single_user_mode=true&default_server_location=https%3A%2F%2Fserver.example.com%2Fapi&default_access_key=fomom-nobij-hirug-hukor-rudal-nukup-kilum-fanif-b

    public static native void setDefaultSingleUserMode(String value);
    public static native void setDefaultServerLocation(String value);
    public static native void setDefaultAccessKey(String value);

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
        // Called when the app is already running. Send the URL parameters
        // as signals to the app. This will work, provided the user hasn't
        // already registered manually
        Log.i(TAG, "onNewIntent");

        super.onNewIntent(intent);

        Uri uri = intent.getData();

        if (uri != null) {
            Log.i(TAG, intent.getDataString());

            Map<String, String> parameters = getQueryParameters(uri);
            String default_single_user_mode = parameters.get("default_single_user_mode");
            if (default_single_user_mode != null) {
                setDefaultSingleUserMode(default_single_user_mode);
            }

            String default_server_location = parameters.get("default_server_location");
            if (default_server_location != null) {
                setDefaultServerLocation(default_server_location);
            }

            String default_access_key = parameters.get("default_access_key");
            if (default_access_key != null) {
                setDefaultAccessKey(default_access_key);
            }
        }
    }

    private Map<String, String> getQueryParameters(Uri uri) {
        List<String> names = Arrays.asList(
                                           "default_single_user_mode",
                                           "default_server_location",
                                           "default_access_key"
                                           );

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
        super_onConfigurationChanged(newConfig);
        QtApplication.invokeDelegate(newConfig);
    }
}
