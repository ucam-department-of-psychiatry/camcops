## base_pdf_portrait.mako
<%page cached="True" cache_region="local"/>
<%inherit file="base_pdf.mako"/>

<%block name="css">
    <%include file="css_pdf_paged_media.mako" args="ORIENTATION='portrait'"/>
</%block>
