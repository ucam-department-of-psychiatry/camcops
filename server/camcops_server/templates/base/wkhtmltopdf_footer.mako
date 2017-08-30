## wkhtmltopdf_footer.mako
## USED TO MAKE SEPARATE FOOTER HTML FILES FOR WKHTMLTOPDF.
## WORKS IN CONJUNCTION WITH wkhtmltopdf_header.mako
<%page args="inner_text: str"/>
<%inherit file="base.mako"/>

<%block name="css">
    <%include file="css_wkhtmltopdf.mako"/>
</%block>

<%block name="extra_head">
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
</%block>

<%block name="body_tags">
    onload="subst()"
    ## the function itself is defined in wkhtmltopdf_footer.mako
</%block>

<div>
    Page <span class="page"></span> of <span class="topage"></span>.
    ${inner_text}
</div>
