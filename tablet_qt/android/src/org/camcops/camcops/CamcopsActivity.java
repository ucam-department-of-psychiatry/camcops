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

import java.lang.String;
import java.lang.StringBuilder;
import java.util.Arrays;
import java.util.List;

import org.qtproject.qt5.android.bindings.QtActivity;

public class CamcopsActivity extends QtActivity
{
     @Override
     public void onCreate(Bundle savedInstanceState) {
          // Handle application launch from a hyperlink
          // e.g. http://camcops/?default_single_user_mode=true&default_server_location=https%3A%2F%2Fserver.example.com%2Fapi&default_access_key=fomom-nobij-hirug-hukor-rudal-nukup-kilum-fanif-b

          Intent intent = getIntent();

          if (intent != null && intent.getAction() == Intent.ACTION_VIEW) {
               List<String> names = Arrays.asList("default_single_user_mode",
                                                  "default_server_location",
                                                  "default_access_key");
               Uri uri = intent.getData();

               // String.join() not available at runtime
               StringBuilder sb = new StringBuilder();

               String separator = "";
               for (String name : names) {
                   String value = uri.getQueryParameter(name);
                   if (value != null) {
                        sb.append(separator)
                             .append("--").append(name)
                             .append("=").append(value);

                        separator = "\t";
                   }
               }

               APPLICATION_PARAMETERS = sb.toString();
          }

          super.onCreate(savedInstanceState);
     }
}
