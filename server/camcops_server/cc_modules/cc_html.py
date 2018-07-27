#!/usr/bin/env python
# camcops_server/cc_modules/cc_html.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
from typing import Any, Callable, List, Optional, TYPE_CHECKING, Union

import cardinal_pythonlib.rnc_web as ws

from camcops_server.cc_modules.cc_constants import CssClass

if TYPE_CHECKING:
    from .cc_request import CamcopsRequest


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


def tr(*args, tr_class: str = "", literal: bool = False) -> str:
    """
    Make simple HTML table data row.

    Args:
        *args: Set of columns data.
        literal: Treat elements as literals with their own <td> ... </td>,
            rather than things to be encapsulated.
        tr_class: table row class
    """
    if literal:
        elements = args
    else:
        elements = [td(x) for x in args]
    return "<tr{tr_class}>{contents}</tr>\n".format(
        tr_class=' class="{}"'.format(tr_class) if tr_class else '',
        contents="".join(elements),
    )


def td(contents: Any, td_class: str = "", td_width: str = "") -> str:
    """Make simple HTML table data cell."""
    return "<td{td_class}{td_width}>{contents}</td>\n".format(
        td_class=' class="{}"'.format(td_class) if td_class else '',
        td_width=' width="{}"'.format(td_width) if td_width else '',
        contents=contents,
    )


def th(contents: Any, th_class: str = "", th_width: str = "") -> str:
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
    return tr_span_col(s, cols=2, tr_class=CssClass.HEADING)


def subheading_spanning_two_columns(s: str, th_not_td: bool = False) -> str:
    """HTML table subheading spanning 2 columns."""
    return tr_span_col(s, cols=2, tr_class=CssClass.SUBHEADING,
                       th_not_td=th_not_td)


def subheading_spanning_three_columns(s: str, th_not_td: bool = False) -> str:
    """HTML table subheading spanning 3 columns."""
    return tr_span_col(s, cols=3, tr_class=CssClass.SUBHEADING,
                       th_not_td=th_not_td)


def subheading_spanning_four_columns(s: str, th_not_td: bool = False) -> str:
    """HTML table subheading spanning 4 columns."""
    return tr_span_col(s, cols=4, tr_class=CssClass.SUBHEADING,
                       th_not_td=th_not_td)


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


def sub(x: str) -> str:
    """Applies HTML subscript."""
    return "<sub>{}</sub>".format(x)


def sup(x: str) -> str:
    """Applies HTML superscript."""
    return "<sup>{}</sup>".format(x)


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

def get_yes_no(req: "CamcopsRequest", x: Any) -> str:
    """'Yes' if x else 'No'"""
    return req.wappstring("yes") if x else req.wappstring("no")


def get_yes_no_none(req: "CamcopsRequest", x: Any) -> Optional[str]:
    """Returns 'Yes' for True, 'No' for False, or None for None."""
    if x is None:
        return None
    return get_yes_no(req, x)


def get_yes_no_unknown(req: "CamcopsRequest", x: Any) -> str:
    """Returns 'Yes' for True, 'No' for False, or '?' for None."""
    if x is None:
        return "?"
    return get_yes_no(req, x)


def get_true_false(req: "CamcopsRequest", x: Any) -> str:
    """'True' if x else 'False'"""
    return req.wappstring("true") if x else req.wappstring("false")


def get_true_false_none(req: "CamcopsRequest", x: Any) -> Optional[str]:
    """Returns 'True' for True, 'False' for False, or None for None."""
    if x is None:
        return None
    return get_true_false(req, x)


def get_true_false_unknown(req: "CamcopsRequest", x: Any) -> str:
    """Returns 'True' for True, 'False' for False, or '?' for None."""
    if x is None:
        return "?"
    return get_true_false(req, x)


def get_present_absent(req: "CamcopsRequest", x: Any) -> str:
    """'Present' if x else 'Absent'"""
    return req.wappstring("present") if x else req.wappstring("absent")


def get_present_absent_none(req: "CamcopsRequest", x: Any) -> Optional[str]:
    """Returns 'Present' for True, 'Absent' for False, or None for None."""
    if x is None:
        return None
    return get_present_absent(req, x)


def get_present_absent_unknown(req: "CamcopsRequest", x: str) -> str:
    """Returns 'Present' for True, 'Absent' for False, or '?' for None."""
    if x is None:
        return "?"
    return get_present_absent(req, x)


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
