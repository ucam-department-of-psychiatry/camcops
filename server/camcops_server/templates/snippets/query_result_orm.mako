## Creates an HTML table from a query result
<%page args="attrnames, descriptions, orm_objects, null_html='<i>NULL</i>'"/>

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

def get_value(orm_object, attrname, null_html):
    value = getattr(orm_object, attrname)
    return filter_value(value, null_html)

%>

<table>
    <tr>
        %for desc in descriptions:
            <th>${filter_description(desc)}</th>
        %endfor
    </tr>
    %for orm_object in orm_objects:
        <tr>
            %for attrname in attrnames:
                <td>${get_value(orm_object, attrname, null_html)}</td>
            %endfor
        </tr>
    %endfor
</table>
