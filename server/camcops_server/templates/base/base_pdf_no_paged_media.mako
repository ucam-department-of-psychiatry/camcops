## base_pdf_no_paged_media.mako
<%inherit file="base_pdf.mako"/>

<%block name="header_block"></%block>
<%block name="footer_block"></%block>

<%block name="css">
    <%include file="css_pdf_no_paged_media.mako"/>
</%block>

${next.body()}
