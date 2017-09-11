## base_pdf_portrait.mako
<%inherit file="base_pdf.mako"/>

<%block name="css">
    <%include file="css_pdf_portrait.mako"/>
</%block>

${next.body()}
