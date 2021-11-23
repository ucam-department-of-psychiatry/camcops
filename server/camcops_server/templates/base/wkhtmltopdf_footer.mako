## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/base/wkhtmltopdf_footer.mako

===============================================================================

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

===============================================================================

USED TO MAKE SEPARATE FOOTER HTML FILES FOR WKHTMLTOPDF.
WORKS IN CONJUNCTION WITH wkhtmltopdf_header.mako

</%doc>

<%inherit file="base.mako"/>

<%block name="css">
    <%include file="css_wkhtmltopdf.mako"/>
</%block>

<%block name="extra_head_start">
    ${ parent.extra_head_start() | n }

    <script nonce="${ request.nonce | n }">
        // Do not move this Javascript out into a file that's requested
        // separately; wkhtmltopdf will not be able to see it.
        //
        // This function looks for elements tagged by specific CSS classes, via
        // document.getElementsByClassName(), and replaces them with
        // wkhtmltopdf variables, from the "GET" URL string. See
        // - https://stackoverflow.com/questions/7174359/how-to-do-page-numbering-in-header-footer-htmls-with-wkhtmltopdf
        // - https://wkhtmltopdf.org/usage/wkhtmltopdf.txt
        //   ... which illustrates this function.
        //
        // If this doesn't work:
        // -- create dummy header.html, body.html, and footer.html files;
        // -- run wkhtmltopdf with "--quiet" disabled and "--debug-javascript"
        //    enabled.
        // Note that wkhtmltopdf v0.12.2.1 does not support "let" or "const"
        // and requires "var". Do NOT "fix" it just because PyCharm wants that!

        function subst() {
            var vars = {};
            var query_strings_from_url = document.location.search.substring(1).split('&');
            for (var query_string in query_strings_from_url) {
                if (query_strings_from_url.hasOwnProperty(query_string)) {
                    var temp_var = query_strings_from_url[query_string].split('=', 2);
                    vars[temp_var[0]] = decodeURI(temp_var[1]);
                }
            }
            var css_selector_classes = ['page', 'frompage', 'topage', 'webpage', 'section', 'subsection', 'date', 'isodate', 'time', 'title', 'doctitle', 'sitepage', 'sitepages'];
            for (var css_class in css_selector_classes) {
                if (css_selector_classes.hasOwnProperty(css_class)) {
                    var element = document.getElementsByClassName(css_selector_classes[css_class]);
                    for (var j = 0; j < element.length; ++j) {
                        element[j].textContent = vars[css_selector_classes[css_class]];
                    }
                }
            }
        }

        document.addEventListener("DOMContentLoaded", subst, false);
    </script>
</%block>

<div>
    ${ _("Page") } <span class="page"></span> ${ _("of") } <span class="topage"></span>.
    ${ inner_text | n }
</div>
