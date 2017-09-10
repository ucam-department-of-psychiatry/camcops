## wkhtmltopdf_header.mako
## USED TO MAKE SEPARATE HEADER HTML FILES FOR WKHTMLTOPDF.
## WORKS IN CONJUNCTION WITH wkhtmltopdf_footer.mako
<%inherit file="base.mako"/>

<%block name="css">
    <%include file="css_wkhtmltopdf.mako"/>
</%block>

<%block name="body_tags">
    onload="subst()"
    ## the function itself is defined in wkhtmltopdf_footer.mako
</%block>

<div>
    ${inner_text}
</div>
