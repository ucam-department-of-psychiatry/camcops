## Creates an HTML table from a query result
<%page args="descriptions, rows, null_html='<i>NULL</i>'"/>

<%!

from mako.filters import html_escape

def filter_description(desc):
    if not desc:  # None or ""
        return ""
    return html_escape(desc)

def filter_value(value, null_html):
    if value is None:
        return null_html
    return html_escape(str(value))

%>

<table>
    <tr>
        %for desc in descriptions:
            <th>${filter_description(desc)}</th>
        %endfor
    </tr>
    %for row in rows:
        <tr>
            %for value in row:
                <td>${filter_value(value, null_html)}</td>
            %endfor
        </tr>
    %endfor
</table>
