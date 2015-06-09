#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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
"""

import string

from rnc_lang import merge_dicts
import rnc_plot
import rnc_web as ws

from cc_constants import ACTION, NUMBER_OF_IDNUMS, PARAM
import cc_pls  # caution, circular import
from cc_string import WSTRING
import cc_version

# =============================================================================
# Simple constants
# =============================================================================

DEFAULT_PLOT_DPI = 300

# Debugging option
USE_SVG_IN_HTML = True  # set to False for PNG debugging

RESTRICTED_WARNING = u"""
    <div class="warning">
        You are restricted to viewing records uploaded by you. Other records
        may exist for the same patient(s), uploaded by others.
    </div>"""
RESTRICTED_WARNING_SINGULAR = u"""
    <div class="warning">
        You are restricted to viewing records uploaded by you. Other records
        may exist for the same patient, uploaded by others.
    </div>"""


# =============================================================================
# CSS/HTML constants
# =============================================================================

CAMCOPS_FAVICON_FILE = "favicon_camcops.png"
PDF_LOGO_HEIGHT = "20mm"

CSS_PAGED_MEDIA = (cc_version.PDF_ENGINE != "pdfkit")

COMMON_DEFINITIONS = {
    "SMALLFONTSIZE": "0.85em",
    "TINYFONTSIZE": "0.7em",
    "LARGEFONTSIZE": "1.2em",
    "GIANTFONTSIZE": "1.4em",
    "BANNERFONTSIZE": "1.6em",

    # Rules: line height is 1.2 * font size
    # ... but an em is related to the calculated font-size of the element,
    #   http://www.impressivewebs.com/understanding-em-units-css/
    # so it can always be 1.2:
    "MAINLINEHEIGHT": "1.2em",
    #"SMALLLINEHEIGHT": "1.02em",
    #"TINYLINEHEIGHT": "0.84em",
    #"LARGELINEHEIGHT": "1.44em",
    #"GIANTLINEHEIGHT": "1.68em",
    #"BANNERLINEHIGHT": "1.2em",
    #"TABLELINEHEIGHT": "1.1em",
    "SMALLLINEHEIGHT": "1.2em",
    "TINYLINEHEIGHT": "1.2em",
    "LARGELINEHEIGHT": "1.2em",
    "GIANTLINEHEIGHT": "1.2em",
    "BANNERLINEHIGHT": "1.2em",
    "TABLELINEHEIGHT": "1.2em",

    "VSPACE_NORMAL": "0.5em",
    "VSPACE_LARGE": "0.8em",

    "SIGNATUREHEIGHT": "3em",

    # Specific to PDFs:
    "PDF_LOGO_HEIGHT": PDF_LOGO_HEIGHT,
}

WEB_SIZES = {
    "MAINFONTSIZE": "medium",
    "SMALLGAP": "2px",
    "ELEMENTGAP": "5px",
    "NORMALPAD": "2px",
    "TABLEPAD": "2px",
    "INDENT_NORMAL": "20px",
    "INDENT_LARGE": "75px",
    "THINLINE": "1px",
    "ZERO": "0px",
    "PDFEXTRA": "",
    "MAINMARGIN": "10px",
    "BODYPADDING": "5px",
    "BANNER_PADDING": "25px",
}

# Hard page margins for A4:
# - left/right: most printers can cope; hole punches to e.g. 13 mm; so 20mm
#   reasonable.
# - top: HP Laserjet 1100 e.g. clips at about 17.5mm
# - bottom: HP Laserjet 1100 e.g. clips at about 15mm
# ... so 20mm all round about right

PDF_SIZES = {
    "MAINFONTSIZE": "10pt",
    "SMALLGAP": "0.2mm",
    "ELEMENTGAP": "1mm",
    "NORMALPAD": "0.5mm",
    "TABLEPAD": "0.5mm",
    "INDENT_NORMAL": "5mm",
    "INDENT_LARGE": "10mm",
    "THINLINE": "0.1mm",
    "ZERO": "0mm",
    "MAINMARGIN": "2cm",
    "BODYPADDING": "0mm",
    "BANNER_PADDING": "0.5cm",
}

# Sequences of 4: top, right, bottom, left
# margin is outside, padding is inside
# #identifier
# .class
# http://www.w3schools.com/cssref/css_selectors.asp
# http://stackoverflow.com/questions/4013604
# http://stackoverflow.com/questions/6023419

# Avoid both {} and % substitution by using string.Template and $
CSS_BASE = string.Template(u"""

/* Display PNG fallback image... */
svg img.svg {
    display: none;
}
img.pngfallback {
    display: inline;
}
/* ... unless our browser supports SVG */
html.svg svg img.svg {
    display: inline;
}
html.svg img.pngfallback {
    display: none;
}

/* Overall defaults */

body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: $MAINFONTSIZE;
    line-height: $MAINLINEHEIGHT;
    margin: $ELEMENTGAP $ZERO $ELEMENTGAP $ZERO;
    padding: $BODYPADDING;
}
code {
    font-size: 0.8em;
    font-family: Consolas, Monaco, 'Lucida Console', 'Liberation Mono',
        'DejaVu Sans Mono', 'Bitstream Vera Sans Mono', 'Courier New';
    background-color: #eeeeee;
    padding: 1px 5px 1px 5px;
}
div {
    margin: $ELEMENTGAP $ZERO $ELEMENTGAP $ZERO;
    padding: $NORMALPAD;
}
em {
    color: rgb(0, 0, 255);
    font-style: normal;
}
h1 {
    font-size: $GIANTFONTSIZE;
    line-height: $GIANTLINEHEIGHT;
    font-weight: bold;
    margin: $ZERO;
}
h2 {
    font-size: $LARGEFONTSIZE;
    line-height: $LARGELINEHEIGHT;
    font-weight: bold;
    margin: $ZERO;
}
h3 {
    font-size: $LARGEFONTSIZE;
    line-height: $LARGELINEHEIGHT;
    font-weight: bold;
    font-style: italic;
    margin: $ZERO;
}
img {
    max-width: 100%;
    max-height: 100%;
}
p {
    margin: $ELEMENTGAP $ZERO $ELEMENTGAP $ZERO;
}
sup, sub {
    font-size: 0.7em; /* 1 em is the size of the parent font */
    vertical-align: baseline;
    position: relative;
    top: -0.5em;
}
sub {
    top: 0.5em;
}
table {
    width: 100%; /* particularly for PDFs */
    vertical-align: top;
    border-collapse: collapse;
    border: $THINLINE solid black;
    padding: $ZERO;
    margin: $ELEMENTGAP $ZERO $ELEMENTGAP $ZERO;
}
tr, th, td {
    vertical-align: top;
    text-align: left;
    margin: $ZERO;
    padding: $TABLEPAD;
    border: $THINLINE solid black;
    line-height: $TABLELINEHEIGHT;
}

/* Specific classes */

.badidpolicy_mild {
    background-color: rgb(255, 255, 153);
}
.badidpolicy_severe {
    background-color: rgb(255, 255, 0);
}
.banner {
    text-align: center;
    font-size: $BANNERFONTSIZE;
    line-height: $BANNERLINEHIGHT;
    padding: $BANNER_PADDING;
    margin: $ZERO;
}
.banner_referral_general_adult {
    background-color: rgb(255, 165, 0);
}
.banner_referral_old_age {
    background-color: rgb(0, 255, 127);
}
.banner_referral_substance_misuse {
    background-color: rgb(0, 191, 255);
}
.clinician {
    background-color: rgb(200, 255, 255);
}
table.clinician, table.clinician th, table.clinician td {
    border: $THINLINE solid black;
}
.copyright {
    font-style: italic;
    font-size: $TINYFONTSIZE;
    line-height: $TINYLINEHEIGHT;
    background-color: rgb(227, 227, 227);
}
.ctv_datelimit_start {
    /* line below */
    text-align: right;
    border-style: none none solid none;
    border-width: $THINLINE;
    border-color: black;
}
.ctv_datelimit_end {
    /* line above */
    text-align: right;
    border-style: solid none none none;
    border-width: $THINLINE;
    border-color: black;
}
.ctv_taskheading {
    background-color: rgb(200, 200, 255);
    font-weight: bold;
}
.ctv_fieldheading {
    background-color: rgb(200, 200, 200);
    font-weight: bold;
    font-style: italic;
    margin: $ELEMENTGAP $ZERO $SMALLGAP $INDENT_NORMAL;
}
.ctv_fieldsubheading {
    background-color: rgb(200, 200, 200);
    font-style: italic;
    margin: $ELEMENTGAP $ZERO $SMALLGAP $INDENT_NORMAL;
}
.ctv_fielddescription {
    font-style: italic;
    margin: $ELEMENTGAP $ZERO $SMALLGAP $INDENT_NORMAL;
}
.ctv_fieldcontent {
    font-weight: bold;
    margin: $SMALLGAP $ZERO $ELEMENTGAP $INDENT_NORMAL;
}
.ctv_warnings {
    margin: $ELEMENTGAP $ZERO $SMALLGAP $INDENT_NORMAL;
}
.error {
    color: rgb(255, 0, 0);
}
.explanation {
    background-color: rgb(200, 255, 200);
}
table.extradetail {
    border: $THINLINE solid black;
    background-color: rgb(210, 210, 210);
}
table.extradetail th {
    border: $THINLINE solid black;
    font-style: italic;
    font-weight: bold;
    font-size: $TINYFONTSIZE;
}
table.extradetail td {
    border: $THINLINE solid black;
    font-size: $TINYFONTSIZE;
}
tr.extradetail2 {
    background-color: rgb(240, 240, 240);
}
td.figure {
    padding: $ZERO;
    background-color: rgb(255, 255, 255);
}
div.filter {
    /* for task filters */
    margin-left: $INDENT_LARGE;
    padding: $ZERO;
}
form.filter {
    /* for task filters */
    display: inline;
    margin: $ZERO;
}
.footnotes {
    font-style: italic;
    font-size: $SMALLFONTSIZE;
    line-height: $SMALLLINEHEIGHT;
}
.formtitle {
    font-size: $LARGEFONTSIZE;
    color: rgb(34, 139, 34);
}
table.general, table.general th, table.general td {
    border: $THINLINE solid black;
}
table.general th.col1, table.general td.col1 {
    width: 22%;
}
table.general th.col2, table.general td.col2 {
    width: 78%;
}
.green {
    color: rgb(34, 139, 34);
}
p.hangingindent {
    padding-left: $INDENT_NORMAL;
    text-indent: -$INDENT_NORMAL;
}
.heading {
    background-color: rgb(0, 0, 0);
    color: rgb(255, 255, 255);
    font-style: italic;
}
.highlight {
    background-color: rgb(255, 250, 205);
}
.important {
    color: rgb(64, 0, 192);
    font-weight: bold;
}
.specialnote {
    background-color: rgb(255, 255, 153);
}
.live_on_tablet {
    background-color: rgb(216, 208, 245);
}
.incomplete {
    background-color: rgb(255, 165, 0);
}
.superuser {
    background-color: rgb(255, 192, 203);
}
p.indent {
    margin-left: $INDENT_NORMAL;
}
div.indented {
    margin-left: $INDENT_LARGE;
}
.navigation {
    background-color: rgb(200, 255, 200);
}
.noborder {
    border: none;
    /* NB also: hidden overrides none with border-collapse */
}
.noborderphoto {
    padding: $ZERO;
    border: none;
}
.office {
    background-color: rgb(227, 227, 227);
    font-style: italic;
    font-size: $TINYFONTSIZE;
    line-height: $TINYLINEHEIGHT;
}
.patient {
    background-color: rgb(255, 200, 200);
}
.pdf_logo_header {
    width: 100%;
    border: none;
}
.pdf_logo_header table, .pdf_logo_header tr {
    width: 100%;
    border: none;
}
.pdf_logo_header .image_td {
    width: 45%;
    border: none;
}
.pdf_logo_header .centregap_td {
    width: 10%;
    border: none;
}
.pdf_logo_header .logo_left {
    float: left;
    max-width: 100%;
    max-height: $PDF_LOGO_HEIGHT;
    height: auto;
    width: auto;
}
.pdf_logo_header .logo_right {
    float: right;
    max-width: 100%;
    max-height: $PDF_LOGO_HEIGHT;
    height: auto;
    width: auto;
}
.photo {
    padding: $ZERO;
}
.signature_label {
    border: none;
    text-align: center;
}
.signature {
    line-height: $SIGNATUREHEIGHT;
    border: $THINLINE solid black;
}
.smallprint {
    font-style: italic;
    font-size: $SMALLFONTSIZE;
}
.subheading {
    background-color: rgb(200, 200, 200);
    font-style: italic;
}
.subsubheading {
    font-style: italic;
}
.summary {
    background-color: rgb(200, 200, 255);
}
table.summary, .summary th, .summary td {
    border: $THINLINE solid black;
}
table.taskconfig, .taskconfig th, .taskconfig td {
    border: $THINLINE solid black;
    background-color: rgb(230, 230, 230);
}
table.taskconfig th {
    font-style: italic; font-weight: normal;
}
table.taskdetail, .taskdetail th, .taskdetail td {
    border: $THINLINE solid black;
}
table.taskdetail th {
    font-weight: normal; font-style: italic;
}
table.taskdetail td {
    font-weight: normal;
}
.taskheader {
    background-color: rgb(200, 200, 200);
}
.trackerheader {
    font-size: $TINYFONTSIZE;
    line-height: $TINYLINEHEIGHT;
    background-color: rgb(218, 112, 240);
}
.tracker_all_consistent {
    font-style: italic;
    font-size: $TINYFONTSIZE;
    line-height: $TINYLINEHEIGHT;
    background-color: rgb(227, 227, 227);
}
.warning {
    background-color: rgb(255, 100, 100);
}

/* The next three: need both L/R to float and clear:both for IE */
.web_logo_header {
    display: block;
    overflow: hidden;
    width: 100%;
    border: none;
    clear: both;
}
/* ... overflow:hidden so the div expands to its floating contents */
.web_logo_header .logo_left {
    width: 45%;
    float: left;
    text-decoration: none;
    border: $ZERO;
}
.web_logo_header .logo_right {
    width: 45%;
    float: right;
    text-decoration: none;
    border: $ZERO;
}

/* For tables that will make it to a PDF, fix Weasyprint column widths.
   But not for all (e.g. webview task list) tables. */
table.clinician, table.extradetail, table.general,
        table.pdf_logo_header, table.summary,
        table.taskconfig, table.taskdetail,
        table.fixed {
    table-layout: fixed;
}

""")

# Image sizing:
# http://stackoverflow.com/questions/787839/resize-image-proportionally-with-css  # noqa

PDF_PAGED_MEDIA_CSS = string.Template("""

/* PDF extras */
#headerContent {
    font-size: $SMALLFONTSIZE;
    line-height: $SMALLLINEHEIGHT;
}
#footerContent {
    font-size: $SMALLFONTSIZE;
    line-height: $SMALLLINEHEIGHT;
}

/* PDF paging via CSS Paged Media */
@page {
    size: A4 $ORIENTATION;
    margin-left: $MAINMARGIN;
    margin-right: $MAINMARGIN;
    margin-top: $MAINMARGIN;
    margin-bottom: $MAINMARGIN;
    @frame header {
        /* -pdf-frame-border: 1; */ /* for debugging */
        -pdf-frame-content: headerContent;
        top: 1cm;
        margin-left: $MAINMARGIN;
        margin-right: $MAINMARGIN;
    }
    @frame footer {
        /* -pdf-frame-border: 1; */ /* for debugging */
        -pdf-frame-content: footerContent;
        bottom: 0.5cm; /* distance up from page's bottom margin? */
        height: 1cm; /* height of the footer */
        margin-left: $MAINMARGIN;
        margin-right: $MAINMARGIN;
    }
}
""")
# WEASYPRINT: NOT WORKING PROPERLY YET: WEASYPRINT DOESN'T YET SUPPORT RUNNING
# ELEMENTS
# http://librelist.com/browser//weasyprint/2013/7/4/header-and-footer-for-each-page/#abe45ec357d593df44ffca48253817ef  # noqa
# http://weasyprint.org/docs/changelog/

COMMON_HEAD = string.Template(u"""
<!DOCTYPE html> <!-- HTML 5 -->
<html>
    <head>
        <title>CamCOPS</title>
        <meta charset="utf-8">
        <link rel="icon" type="image/png" href="$CAMCOPS_FAVICON_FILE">
        <script>
            /* set "html.svg" if our browser supports SVG */
            if (document.implementation.hasFeature(
                    "http://www.w3.org/TR/SVG11/feature#Image", "1.1")) {
                document.documentElement.className = "svg";
            }
        </script>
        <style type="text/css">
            $CSS
        </style>
    </head>
    <body>
""")

# Re PDFs:
# - The way in which xhtml2pdf copes with column widths
#   is somewhat restricted: CSS only
# - "height" not working for td
# TABLE STYLING HELP:
# http://www.somacon.com/p141.php
# http://www.w3.org/Style/Tables/examples.html


WEB_HEAD = COMMON_HEAD.substitute(
    CAMCOPS_FAVICON_FILE=CAMCOPS_FAVICON_FILE,
    CSS=CSS_BASE.substitute(merge_dicts(COMMON_DEFINITIONS, WEB_SIZES)),
)
PDF_HEAD_PORTRAIT = COMMON_HEAD.substitute(
    CAMCOPS_FAVICON_FILE=CAMCOPS_FAVICON_FILE,
    CSS=(
        CSS_BASE.substitute(merge_dicts(COMMON_DEFINITIONS, PDF_SIZES)) +
        PDF_PAGED_MEDIA_CSS.substitute(
            merge_dicts(COMMON_DEFINITIONS, PDF_SIZES,
                        {"ORIENTATION": "portrait"}))
    ),
)
PDF_HEAD_LANDSCAPE = COMMON_HEAD.substitute(
    CAMCOPS_FAVICON_FILE=CAMCOPS_FAVICON_FILE,
    CSS=(
        CSS_BASE.substitute(merge_dicts(COMMON_DEFINITIONS, PDF_SIZES)) +
        PDF_PAGED_MEDIA_CSS.substitute(
            merge_dicts(COMMON_DEFINITIONS, PDF_SIZES,
                        {"ORIENTATION": "landscape"}))
    ),
)
PDF_HEAD_NO_PAGED_MEDIA = COMMON_HEAD.substitute(
    CAMCOPS_FAVICON_FILE=CAMCOPS_FAVICON_FILE,
    CSS=CSS_BASE.substitute(merge_dicts(COMMON_DEFINITIONS, PDF_SIZES))
)

COMMON_END = "</body></html>"
WEBEND = COMMON_END
PDFEND = COMMON_END

WKHTMLTOPDF_CSS = string.Template("""
    body {
        font-family: Arial, Helvetica, sans-serif;
        font-size: $MAINFONTSIZE;  /* absolute */
        line-height: $SMALLLINEHEIGHT;
        padding: 0;
        margin: 0;  /* use header-spacing / footer-spacing instead */
    }
    div {
        font-size: $SMALLFONTSIZE;  /* relative */
    }
""").substitute(merge_dicts(COMMON_DEFINITIONS, PDF_SIZES))
# http://stackoverflow.com/questions/11447672/fix-wkhtmltopdf-headers-clipping-content  # noqa

WKHTMLTOPDF_OPTIONS = {
    "page-size": "A4",
    "margin-left": "20mm",
    "margin-right": "20mm",
    "margin-top": "21mm",  # from paper edge down to top of content
        # ... then 5mm more, i.e. specify 20mm and get 25mm?
    "margin-bottom": "24mm",  # from paper edge to bottom of content
        # ... then 3mm more, i.e. specify 20mm and get 23mm?
    "header-spacing": "3",  # mm, from content up to bottom of header
    "footer-spacing": "3",  # mm, from content down to top of footer
}


# =============================================================================
# Header/footer blocks for PDFs
# =============================================================================

def wkhtmltopdf_header(inner_html):
    # doctype is mandatory
    # https://github.com/wkhtmltopdf/wkhtmltopdf/issues/1645
    return string.Template(u"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8">
                <style type="text/css">
                    $WKHTMLTOPDF_CSS
                </style>
            </head>
            <body onload="subst()">
                <div>
                    $INNER
                </div>
            </body>
        </html>
    """).substitute(WKHTMLTOPDF_CSS=WKHTMLTOPDF_CSS, INNER=inner_html)


def wkhtmltopdf_footer(inner_text):
    return string.Template(u"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8">
                <style type="text/css">
                    $WKHTMLTOPDF_CSS
                </style>
                <script>
        function subst() {
            var vars = {},
                x = document.location.search.substring(1).split('&'),
                i,
                z,
                y,
                j;
            for (i in x) {
                if (x.hasOwnProperty(i)) {
                    z = x[i].split('=', 2);
                    vars[z[0]] = unescape(z[1]);
                }
            }
            x = ['frompage', 'topage', 'page', 'webpage', 'section',
                 'subsection','subsubsection'];
            for (i in x) {
                if (x.hasOwnProperty(i)) {
                    y = document.getElementsByClassName(x[i]);
                    for (j = 0; j < y.length; ++j) {
                        y[j].textContent = vars[x[i]];
                    }
                }
            }
        }
                </script>
            </head>
            <body onload="subst()">
                <div>
                    Page <span class="page"></span> of
                    <span class="topage"></span>.
                    $INNER
                </div>
            </body>
        </html>
    """).substitute(WKHTMLTOPDF_CSS=WKHTMLTOPDF_CSS, INNER=inner_text)


def csspagedmedia_header(inner_html):
    return u"""
        <div id="headerContent">
            {}
        </div>
    """.format(inner_html)


def csspagedmedia_footer(inner_text):
    return u"""
        <div id="footerContent">
            Page <pdf:pagenumber> of <pdf:pagecount>.
            {}
        </div>
    """.format(inner_text)


def pdf_header_content(inner_html):
    if CSS_PAGED_MEDIA:
        return csspagedmedia_header(inner_html)
    else:
        return wkhtmltopdf_header(inner_html)


def pdf_footer_content(inner_text):
    if CSS_PAGED_MEDIA:
        return csspagedmedia_footer(inner_text)
    else:
        return wkhtmltopdf_footer(inner_text)


# =============================================================================
# HTML elements
# =============================================================================

def table_row(columns, classes=None, colspans=None, colwidths=None,
              default="", heading=False):
    """Make HTML table row."""
    n = len(columns)

    if not classes or len(classes) != n:
        # blank, or duff (in which case ignore)
        classes = [""] * n
    else:
        classes = [(' class="{}"'.format(x) if x else '') for x in classes]

    if not colspans or len(colspans) != n:
        # blank, or duff (in which case ignore)
        colspans = [""] * n
    else:
        colspans = [(' colspan="{}"'.format(x) if x else '') for x in colspans]

    if not colwidths or len(colwidths) != n:
        # blank, or duff (in which case ignore)
        colwidths = [""] * n
    else:
        colwidths = [
            (' width="{}"'.format(x) if x else '')
            for x in colwidths
        ]

    return (
        u"<tr>"
        + "".join([
            "<{cellspec}{classdetail}{colspan}{colwidth}>"
            "{contents}</{cellspec}>".format(
                cellspec="th" if heading else "td",
                contents=default if columns[i] is None else columns[i],
                classdetail=classes[i],
                colspan=colspans[i],
                colwidth=colwidths[i],
            ) for i in range(n)
        ])
        + "</tr>\n"
    )


def div(content, div_class=""):
    """Make simple HTML div."""
    return u"""
        <div{div_class}>
            {content}
        </div>
    """.format(
        content=content,
        div_class=' class="{}"'.format(div_class) if div_class else '',
    )


def table(content, table_class=""):
    """Make simple HTML table."""
    return u"""
        <table{table_class}>
            {content}
        </table>
    """.format(
        content=content,
        table_class=' class="{}"'.format(table_class) if table_class else '',
    )


def tr(*args, **kwargs):
    """Make simple HTML table data row.

    *args: Set of columns data.
    **kwargs:
        literal: Treat elements as literals with their own <td> ... </td>,
            rather than things to be encapsulted.
        tr_class: table row class
    """
    tr_class = kwargs.get("tr_class", "")
    if kwargs.get("literal"):
        elements = args
    else:
        elements = [td(x) for x in args]
    return u"<tr{tr_class}>{contents}</tr>\n".format(
        tr_class=' class="{}"'.format(tr_class) if tr_class else '',
        contents="".join(elements),
    )


def td(contents, td_class="", td_width=""):
    """Make simple HTML table data cell."""
    return u"<td{td_class}{td_width}>{contents}</td>\n".format(
        td_class=' class="{}"'.format(td_class) if td_class else '',
        td_width=' width="{}"'.format(td_width) if td_width else '',
        contents=contents,
    )


def th(contents, th_class="", th_width=""):
    """Make simple HTML table header cell."""
    return u"<th{th_class}{th_width}>{contents}</th>\n".format(
        th_class=' class="{}"'.format(th_class) if th_class else '',
        th_width=' width="{}"'.format(th_width) if th_width else '',
        contents=contents,
    )


def tr_qa(q, a, default="?", default_for_blank_strings=False):
    """Make HTML two-column data row, with right-hand column formatted as an
    answer."""
    return tr(q, answer(a, default=default))


def heading_spanning_two_columns(s):
    """HTML table heading spanning 2 columns."""
    return tr_span_col(s, cols=2, tr_class="heading")


def subheading_spanning_two_columns(s, th_not_td=False):
    """HTML table subheading spanning 2 columns."""
    return tr_span_col(s, cols=2, tr_class="subheading", th_not_td=th_not_td)


def subheading_spanning_three_columns(s, th_not_td=False):
    """HTML table subheading spanning 3 columns."""
    return tr_span_col(s, cols=3, tr_class="subheading", th_not_td=th_not_td)


def subheading_spanning_four_columns(s, th_not_td=False):
    """HTML table subheading spanning 4 columns."""
    return tr_span_col(s, cols=4, tr_class="subheading", th_not_td=th_not_td)


def bold(x):
    """Applies HTML bold."""
    return u"<b>{}</b>".format(x)


def italic(x):
    """Applies HTML italic."""
    return u"<i>{}</i>".format(x)


def identity(x):
    """Returns argument unchanged."""
    return x


def answer(x, default="?", default_for_blank_strings=False,
           formatter_answer=bold, formatter_blank=italic):
    """Formats answer in bold, or the default value if None.

    Avoid the word None for the default, e.g.
    'Score indicating likelihood of abuse: None' ... may be misleading!
    Prefer '?' instead.
    """
    if x is None:
        return formatter_blank(default)
    if default_for_blank_strings and not x and (isinstance(x, str)
                                                or isinstance(x, unicode)):
        return formatter_blank(default)
    return formatter_answer(x)


def tr_span_col(x, cols=2, tr_class="", td_class="", th_not_td=False):
    """HTML table data row spanning several columns.

    Args:
        x: Data.
        cols: Number of columns to span.
        tr_class: CSS class to apply to tr.
        th_not_td: make it a th, not a td.
    """
    cell = "th" if th_not_td else "td"
    return u'<tr{tr_cl}><{c} colspan="{cols}"{td_cl}>{x}</{c}></tr>'.format(
        cols=cols,
        x=x,
        tr_cl=u' class="{}"'.format(tr_class) if tr_class else "",
        td_cl=u' class="{}"'.format(td_class) if td_class else "",
        c=cell,
    )


def get_html_from_pyplot_figure(fig):
    """Make HTML (as PNG or SVG) from pyplot figure."""
    if USE_SVG_IN_HTML and cc_pls.pls.useSVG:
        return (
            rnc_plot.svg_html_from_pyplot_figure(fig)
            + rnc_plot.png_img_html_from_pyplot_figure(fig, DEFAULT_PLOT_DPI,
                                                       "pngfallback")
        )
        # return both an SVG and a PNG image, for browsers that can't deal with
        # SVG; the Javascript header will sort this out
        # http://www.voormedia.nl/blog/2012/10/displaying-and-detecting-support-for-svg-images  # noqa
    else:
        return rnc_plot.png_img_html_from_pyplot_figure(fig, DEFAULT_PLOT_DPI)


def get_html_which_idnum_picker(param=PARAM.WHICH_IDNUM, selected=None):
    html = u"""
        <select name="{param}">
    """.format(
        param=param,
    )
    for n in range(1, NUMBER_OF_IDNUMS + 1):
        html += u"""
            <option value="{value}"{selected}>{description}</option>
        """.format(
            value=str(n),
            description=cc_pls.pls.get_id_desc(n),
            selected=ws.option_selected(selected, n),
        )
    html += u"""
        </select>
    """
    return html


def get_html_sex_picker(param=PARAM.SEX, selected=None, offer_all=False):
    if offer_all:
        option_all = '<option value="">(all)</option>'
    else:
        option_all = ''
    return """
        <select name="{param}">
        {option_all}
        <option value="M"{m}>Male</option>
        <option value="F"{f}>Female</option>
        <option value="X"{x}>
            Indeterminate/unspecified/intersex
        </option>
        </select>
    """.format(param=param,
               option_all=option_all,
               m=ws.option_selected(selected, "M"),
               f=ws.option_selected(selected, "F"),
               x=ws.option_selected(selected, "X"))


# =============================================================================
# Field formatting
# =============================================================================

def get_yes_no(x):
    """'Yes' if x else 'No'"""
    return WSTRING("Yes") if x else WSTRING("No")


def get_yes_no_none(x):
    """Returns 'Yes' for True, 'No' for False, or None for None."""
    if x is None:
        return None
    return get_yes_no(x)


def get_yes_no_unknown(x):
    """Returns 'Yes' for True, 'No' for False, or '?' for None."""
    if x is None:
        return "?"
    return get_yes_no(x)


def get_true_false(x):
    """'True' if x else 'False'"""
    return WSTRING("True") if x else WSTRING("False")


def get_true_false_none(x):
    """Returns 'True' for True, 'False' for False, or None for None."""
    if x is None:
        return None
    return get_true_false(x)


def get_true_false_unknown(x):
    """Returns 'True' for True, 'False' for False, or '?' for None."""
    if x is None:
        return "?"
    return get_true_false(x)


def get_present_absent(x):
    """'Present' if x else 'Absent'"""
    return WSTRING("Present") if x else WSTRING("Absent")


def get_present_absent_none(x):
    """Returns 'Present' for True, 'Absent' for False, or None for None."""
    if x is None:
        return None
    return get_present_absent(x)


def get_present_absent_unknown(x):
    """Returns 'Present' for True, 'Absent' for False, or '?' for None."""
    if x is None:
        return "?"
    return get_present_absent(x)


# =============================================================================
# Pages referred to in this module by simple success/failure messages
# =============================================================================

def login_page(extra_msg="", redirect=None):
    """HTML for main login page."""
    disable_autocomplete = (' autocomplete="off"'
                            if cc_pls.pls.DISABLE_PASSWORD_AUTOCOMPLETE
                            else '')
    # http://stackoverflow.com/questions/2530
    # Note that e.g. Chrome may ignore this.
    return cc_pls.pls.WEBSTART + u"""
        <div>{dbtitle}</div>
        <div>
            <b>Unauthorized access prohibited.</b>
            All use is recorded and monitored.
        </div>
        {extramsg}
        <h1>Please log in to the CamCOPS web portal</h1>
        <form method="POST" action="{script}">
            User name: <input type="text" name="{PARAM.USERNAME}"><br>
            Password: <input type="password" name="{PARAM.PASSWORD}"{da}><br>
            <input type="hidden" name="{PARAM.ACTION}" value="{ACTION.LOGIN}">
            <input type="hidden" name="{PARAM.REDIRECT}" value="{redirect}">
            <input type="submit" value="Submit">
        </form>
    """.format(
        dbtitle=get_database_title_string(),
        extramsg=extra_msg,
        script=cc_pls.pls.SCRIPT_NAME,
        da=disable_autocomplete,
        ACTION=ACTION,
        PARAM=PARAM,
        redirect="" if not redirect else redirect,
    ) + WEBEND


# =============================================================================
# Common page components
# =============================================================================

def simple_success_message(msg, extra_html=""):
    """HTML for simple success message."""
    return cc_pls.pls.WEBSTART + u"""
        <h1>Success</h1>
        <div>{}</div>
        {}
        {}
    """.format(
        ws.webify(msg),
        extra_html,
        get_return_to_main_menu_line()
    ) + WEBEND


def error_msg(msg):
    """HTML for error message."""
    return u"""<h2 class="error">{}</h2>""".format(msg)


def fail_with_error_not_logged_in(error, redirect=None):
    """HTML for you-have-failed-and-are-not-logged-in message."""
    return login_page(error_msg(error), redirect)


def fail_with_error_stay_logged_in(error, extra_html=""):
    """HTML for errors where the user stays logged in."""
    return cc_pls.pls.WEBSTART + u"""
        {}
        {}
        {}
    """.format(
        error_msg(error),
        get_return_to_main_menu_line(),
        extra_html
    ) + WEBEND


def get_return_to_main_menu_line():
    """HTML DIV for returning to the main menu."""
    return u"""
        <div>
            <a href="{}">Return to main menu</a>
        </div>
    """.format(get_url_main_menu())


def get_database_title_string():
    """Database title as HTML-safe unicode."""
    if not cc_pls.pls.DATABASE_TITLE:
        return ""
    return u"Database: <b>{}</b>.".format(ws.webify(cc_pls.pls.DATABASE_TITLE))


# =============================================================================
# URLs
# =============================================================================

def get_generic_action_url(action):
    """Make generic URL with initial action name/value pair."""
    return "{}?{}={}".format(cc_pls.pls.SCRIPT_NAME, PARAM.ACTION, action)


def get_url_field_value_pair(field, value):
    """Make generic "&field=value" pair to append to URL, with ampersand."""
    return "&amp;{}={}".format(field, value)


def get_url_main_menu():
    return get_generic_action_url(ACTION.MAIN_MENU)


def get_url_enter_new_password(username):
    """URL to enter new password."""
    return (
        get_generic_action_url(ACTION.ENTER_NEW_PASSWORD)
        + get_url_field_value_pair(PARAM.USERNAME, username)
    )
