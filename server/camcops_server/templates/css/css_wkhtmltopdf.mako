## css_wkhtmltopdf.mako
<%page args="MAINFONTSIZE, SMALLLINEHEIGHT"/>

<%namespace file="def_css_constants.mako" import="argstring, pdf_args"/>
<%!

pdf_arg_dict = pdf_args()
MAINFONTSIZE = pdf_arg_dict['MAINFONTSIZE']
SMALLFONTSIZE = "0.85em"
SMALLLINEHEIGHT = "1.1em"

%>

body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: ${MAINFONTSIZE};  /* absolute */
    line-height: ${SMALLLINEHEIGHT};
    padding: 0;
    margin: 0;  /* use header-spacing / footer-spacing instead */
}
div {
    font-size: ${SMALLFONTSIZE};  /* relative */
}

## http://stackoverflow.com/questions/11447672/fix-wkhtmltopdf-headers-clipping-content  # noqa
