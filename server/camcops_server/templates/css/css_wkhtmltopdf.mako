## css_wkhtmltopdf.mako

<%namespace file="def_css_constants.mako" import="_get_css_varargs"/>
<%

# Note the important difference between <% %> and <%! %>
# http://docs.makotemplates.org/en/latest/syntax.html#python-blocks
# http://docs.makotemplates.org/en/latest/syntax.html#module-level-blocks

va = _get_css_varargs("wkhtmltopdf_header_footer")

%>

body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: ${va.MAINFONTSIZE};  /* absolute */
    line-height: ${va.SMALLLINEHEIGHT};
    padding: 0;
    margin: 0;  /* use header-spacing / footer-spacing instead */
}
div {
    font-size: ${va.SMALLFONTSIZE};  /* relative */
}

## http://stackoverflow.com/questions/11447672/fix-wkhtmltopdf-headers-clipping-content  # noqa
