#!/usr/bin/env python
# camcops_server/cc_modules/cc_html.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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
===============================================================================
"""

import base64
import string
from typing import Any, Callable, List, Optional, Union

import cardinal_pythonlib.plot as rnc_plot
import cardinal_pythonlib.rnc_web as ws

from .cc_constants import (
    ACTION,
    CSS_PAGED_MEDIA,
    DEFAULT_PLOT_DPI,
    PARAM,
    USE_SVG_IN_HTML,
    WEBEND,
    WKHTMLTOPDF_CSS,
)
from .cc_request import CamcopsRequest
from .cc_string import wappstring


# =============================================================================
# Header/footer blocks for PDFs
# =============================================================================

def wkhtmltopdf_header(inner_html: str) -> str:
    # doctype is mandatory
    # https://github.com/wkhtmltopdf/wkhtmltopdf/issues/1645
    return string.Template("""
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


def wkhtmltopdf_footer(inner_text: str) -> str:
    return string.Template("""
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


def csspagedmedia_header(inner_html: str) -> str:
    return """
        <div id="headerContent">
            {}
        </div>
    """.format(inner_html)


def csspagedmedia_footer(inner_text: str) -> str:
    return """
        <div id="footerContent">
            Page <pdf:pagenumber> of <pdf:pagecount>.
            {}
        </div>
    """.format(inner_text)


def pdf_header_content(inner_html: str) -> str:
    if CSS_PAGED_MEDIA:
        return csspagedmedia_header(inner_html)
    else:
        return wkhtmltopdf_header(inner_html)


def pdf_footer_content(inner_text: str) -> str:
    if CSS_PAGED_MEDIA:
        return csspagedmedia_footer(inner_text)
    else:
        return wkhtmltopdf_footer(inner_text)


# =============================================================================
# HTML elements
# =============================================================================

def table_row(columns: List[str],
              classes: List[str] = None,
              colspans: List[str] = None,
              colwidths: List[str] = None,
              default: str = "",
              heading: bool = False) -> str:
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
        "<tr>" +
        "".join([
            "<{cellspec}{classdetail}{colspan}{colwidth}>"
            "{contents}</{cellspec}>".format(
                cellspec="th" if heading else "td",
                contents=default if columns[i] is None else columns[i],
                classdetail=classes[i],
                colspan=colspans[i],
                colwidth=colwidths[i],
            ) for i in range(n)
        ]) +
        "</tr>\n"
    )


def div(content: str, div_class: str = "") -> str:
    """Make simple HTML div."""
    return """
        <div{div_class}>
            {content}
        </div>
    """.format(
        content=content,
        div_class=' class="{}"'.format(div_class) if div_class else '',
    )


def table(content: str, table_class: str = "") -> str:
    """Make simple HTML table."""
    return """
        <table{table_class}>
            {content}
        </table>
    """.format(
        content=content,
        table_class=' class="{}"'.format(table_class) if table_class else '',
    )


def tr(*args, **kwargs) -> str:
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
    return "<tr{tr_class}>{contents}</tr>\n".format(
        tr_class=' class="{}"'.format(tr_class) if tr_class else '',
        contents="".join(elements),
    )


def td(contents: str, td_class: str = "", td_width: str = "") -> str:
    """Make simple HTML table data cell."""
    return "<td{td_class}{td_width}>{contents}</td>\n".format(
        td_class=' class="{}"'.format(td_class) if td_class else '',
        td_width=' width="{}"'.format(td_width) if td_width else '',
        contents=contents,
    )


def th(contents: str, th_class: str = "", th_width: str = "") -> str:
    """Make simple HTML table header cell."""
    return "<th{th_class}{th_width}>{contents}</th>\n".format(
        th_class=' class="{}"'.format(th_class) if th_class else '',
        th_width=' width="{}"'.format(th_width) if th_width else '',
        contents=contents,
    )


def tr_qa(q: str,
          a: Any,
          default: str = "?",
          default_for_blank_strings: bool = False) -> str:
    """Make HTML two-column data row, with right-hand column formatted as an
    answer."""
    return tr(q, answer(a, default=default,
                        default_for_blank_strings=default_for_blank_strings))


def heading_spanning_two_columns(s: str) -> str:
    """HTML table heading spanning 2 columns."""
    return tr_span_col(s, cols=2, tr_class="heading")


def subheading_spanning_two_columns(s: str, th_not_td: bool = False) -> str:
    """HTML table subheading spanning 2 columns."""
    return tr_span_col(s, cols=2, tr_class="subheading", th_not_td=th_not_td)


def subheading_spanning_three_columns(s: str, th_not_td: bool = False) -> str:
    """HTML table subheading spanning 3 columns."""
    return tr_span_col(s, cols=3, tr_class="subheading", th_not_td=th_not_td)


def subheading_spanning_four_columns(s: str, th_not_td: bool = False) -> str:
    """HTML table subheading spanning 4 columns."""
    return tr_span_col(s, cols=4, tr_class="subheading", th_not_td=th_not_td)


def bold(x: str) -> str:
    """Applies HTML bold."""
    return "<b>{}</b>".format(x)


def italic(x: str) -> str:
    """Applies HTML italic."""
    return "<i>{}</i>".format(x)


def identity(x: Any) -> Any:
    """Returns argument unchanged."""
    return x


def bold_webify(x: str) -> str:
    """Webifies the string, then makes it bold."""
    return bold(ws.webify(x))


def answer(x: Any,
           default: str = "?",
           default_for_blank_strings: bool = False,
           formatter_answer: Callable[[str], str] = bold_webify,
           formatter_blank: Callable[[str], str] = italic) -> str:
    """Formats answer in bold, or the default value if None.

    Avoid the word None for the default, e.g.
    'Score indicating likelihood of abuse: None' ... may be misleading!
    Prefer '?' instead.
    """
    if x is None:
        return formatter_blank(default)
    if default_for_blank_strings and not x and isinstance(x, str):
        return formatter_blank(default)
    return formatter_answer(x)


def tr_span_col(x: str,
                cols: int = 2,
                tr_class: str = "",
                td_class: str = "",
                th_not_td: bool = False) -> str:
    """HTML table data row spanning several columns.

    Args:
        x: Data.
        cols: Number of columns to span.
        tr_class: CSS class to apply to tr.
        td_class: CSS class to apply to td.
        th_not_td: make it a th, not a td.
    """
    cell = "th" if th_not_td else "td"
    return '<tr{tr_cl}><{c} colspan="{cols}"{td_cl}>{x}</{c}></tr>'.format(
        cols=cols,
        x=x,
        tr_cl=' class="{}"'.format(tr_class) if tr_class else "",
        td_cl=' class="{}"'.format(td_class) if td_class else "",
        c=cell,
    )


def get_html_from_pyplot_figure(request: CamcopsRequest, fig) -> str:
    """Make HTML (as PNG or SVG) from pyplot figure."""
    ccsession = request.camcops_session
    if USE_SVG_IN_HTML and ccsession.use_svg:
        return (
            rnc_plot.svg_html_from_pyplot_figure(fig) +
            rnc_plot.png_img_html_from_pyplot_figure(fig, DEFAULT_PLOT_DPI,
                                                     "pngfallback")
        )
        # return both an SVG and a PNG image, for browsers that can't deal with
        # SVG; the Javascript header will sort this out
        # http://www.voormedia.nl/blog/2012/10/displaying-and-detecting-support-for-svg-images  # noqa
    else:
        return rnc_plot.png_img_html_from_pyplot_figure(fig, DEFAULT_PLOT_DPI)


def get_html_which_idnum_picker(request: CamcopsRequest,
                                param: str = PARAM.WHICH_IDNUM,
                                selected: int = None) -> str:
    cfg = request.config
    html = """
        <select name="{param}">
    """.format(
        param=param,
    )
    for n in cfg.get_which_idnums():
        html += """
            <option value="{value}"{selected}>{description}</option>
        """.format(
            value=str(n),
            description=cfg.get_id_desc(n),
            selected=ws.option_selected(selected, n),
        )
    html += """
        </select>
    """
    return html


def get_html_sex_picker(param: str = PARAM.SEX,
                        selected: str = None,
                        offer_all: bool = False) -> str:
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


def get_data_url(mimetype: str, data: Union[bytes, memoryview]) -> str:
    """
    Takes data (in binary format) and returns a data URL as per RFC 2397:
        https://tools.ietf.org/html/rfc2397
    such as:
        data:MIMETYPE;base64,B64_ENCODED_DATA
    """
    return "data:{mimetype};base64,{b64encdata}".format(
        mimetype=mimetype,
        b64encdata=base64.b64encode(data).decode('ascii'),
    )


def get_embedded_img_tag(mimetype: str, data: Union[bytes, memoryview]) -> str:
    """
    Takes a binary image and its MIME type, and produces an HTML tag of the
    form:

    <img src="DATA_URL">
    """
    return '<img src={}>'.format(get_data_url(mimetype, data))


# =============================================================================
# Field formatting
# =============================================================================

def get_yes_no(x: Any) -> str:
    """'Yes' if x else 'No'"""
    return wappstring("yes") if x else wappstring("no")


def get_yes_no_none(x: Any) -> Optional[str]:
    """Returns 'Yes' for True, 'No' for False, or None for None."""
    if x is None:
        return None
    return get_yes_no(x)


def get_yes_no_unknown(x: Any) -> str:
    """Returns 'Yes' for True, 'No' for False, or '?' for None."""
    if x is None:
        return "?"
    return get_yes_no(x)


def get_true_false(x: Any) -> str:
    """'True' if x else 'False'"""
    return wappstring("true") if x else wappstring("false")


def get_true_false_none(x: Any) -> Optional[str]:
    """Returns 'True' for True, 'False' for False, or None for None."""
    if x is None:
        return None
    return get_true_false(x)


def get_true_false_unknown(x: Any) -> str:
    """Returns 'True' for True, 'False' for False, or '?' for None."""
    if x is None:
        return "?"
    return get_true_false(x)


def get_present_absent(x: Any) -> str:
    """'Present' if x else 'Absent'"""
    return wappstring("present") if x else wappstring("absent")


def get_present_absent_none(x: Any) -> Optional[str]:
    """Returns 'Present' for True, 'Absent' for False, or None for None."""
    if x is None:
        return None
    return get_present_absent(x)


def get_present_absent_unknown(x: str) -> str:
    """Returns 'Present' for True, 'Absent' for False, or '?' for None."""
    if x is None:
        return "?"
    return get_present_absent(x)


def get_ternary(x: Any,
                value_true: Any = True,
                value_false: Any = False,
                value_none: Any = None) -> Any:
    if x is None:
        return value_none
    if x:
        return value_true
    return value_false


def get_correct_incorrect_none(x: Any) -> Optional[str]:
    # noinspection PyTypeChecker
    return get_ternary(x, "Correct", "Incorrect", None)


# =============================================================================
# Pages referred to in this module by simple success/failure messages
# =============================================================================

def login_page(request: CamcopsRequest, extra_msg: str = "", redirect=None):
    """HTML for main login page."""
    cfg = request.config
    disable_autocomplete = (' autocomplete="off"'
                            if cfg.DISABLE_PASSWORD_AUTOCOMPLETE
                            else '')
    # http://stackoverflow.com/questions/2530
    # Note that e.g. Chrome may ignore this.
    return request.webstart_html + """
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
        dbtitle=get_database_title_string(request),
        extramsg=extra_msg,
        script=request.script_name,
        da=disable_autocomplete,
        ACTION=ACTION,
        PARAM=PARAM,
        redirect="" if not redirect else redirect,
    ) + WEBEND


# =============================================================================
# Common page components
# =============================================================================

def simple_success_message(request: CamcopsRequest, msg: str,
                           extra_html: str = ""):
    """HTML for simple success message."""
    return request.webstart_html + """
        <h1>Success</h1>
        <div>{}</div>
        {}
        {}
    """.format(
        ws.webify(msg),
        extra_html,
        get_return_to_main_menu_line(request)
    ) + WEBEND


def error_msg(msg: str) -> str:
    """HTML for error message."""
    return """<h2 class="error">{}</h2>""".format(msg)


def fail_with_error_not_logged_in(request: CamcopsRequest,
                                  error: str, redirect: str = None) -> str:
    """HTML for you-have-failed-and-are-not-logged-in message."""
    return login_page(request, error_msg(error), redirect)


def fail_with_error_stay_logged_in(request: CamcopsRequest,
                                   error: str, extra_html: str = "") -> str:
    """HTML for errors where the user stays logged in."""
    return request.webstart_html + """
        {}
        {}
        {}
    """.format(
        error_msg(error),
        get_return_to_main_menu_line(request),
        extra_html
    ) + WEBEND


def get_return_to_main_menu_line(request: CamcopsRequest) -> str:
    """HTML DIV for returning to the main menu."""
    return """
        <div>
            <a href="{}">Return to main menu</a>
        </div>
    """.format(get_url_main_menu(request))


def get_database_title_string(request: CamcopsRequest) -> str:
    """Database title as HTML-safe unicode."""
    cfg = request.config
    if not cfg.DATABASE_TITLE:
        return ""
    return "Database: <b>{}</b>.".format(ws.webify(cfg.DATABASE_TITLE))


# =============================================================================
# URLs
# =============================================================================

def get_generic_action_url(request: CamcopsRequest, action: str) -> str:
    """Make generic URL with initial action name/value pair."""
    return "{}?{}={}".format(request.script_name, PARAM.ACTION, action)


def get_url_field_value_pair(field: str, value: Any) -> str:
    """Make generic "&field=value" pair to append to URL, with ampersand."""
    return "&amp;{}={}".format(field, value)


def get_url_main_menu(request: CamcopsRequest) -> str:
    return get_generic_action_url(request, ACTION.MAIN_MENU)


def get_url_enter_new_password(request: CamcopsRequest, username: str) -> str:
    """URL to enter new password."""
    return (
        get_generic_action_url(request, ACTION.ENTER_NEW_PASSWORD) +
        get_url_field_value_pair(PARAM.USERNAME, username)
    )
