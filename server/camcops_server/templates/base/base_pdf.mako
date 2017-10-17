## base_pdf.mako
<%inherit file="base.mako"/>

<%!

from camcops_server.cc_modules.cc_constants import PDF_ENGINE

%>

## For CSS paged media:
<%block name="header_block">
    <div id="headerContent">
        <%block name="extra_header_content"/>
    </div>
</%block>

## For CSS paged media:
<%block name="footer_block">
    <div id="footerContent">
        Page <pdf:pagenumber/> of <pdf:pagecount/>.
        <%block name="extra_footer_content"/>
    </div>
</%block>

<%block name="logo">

    %if PDF_ENGINE in ["pdfkit", "weasyprint"]:
        ## weasyprint: div with floating img does not work properly
        <div class="pdf_logo_header">
            <table>
                <tr>
                    <td class="image_td">
                        <img class="logo_left" src="file://${ request.config.camcops_logo_file_absolute }" />
                    </td>
                    <td class="centregap_td"></td>
                    <td class="image_td">
                        <img class="logo_right" src="file://${ request.config.local_logo_file_absolute }" />
                    </td>
                </tr>
            </table>
        </div>
        <%doc>
        <div class="pdf_logo_header">
            <img class="logo_left" src="file://${ request.config.camcops_logo_file_absolute }" />
            <img class="logo_right" src="file://${ request.config.local_logo_file_absolute }" />
        </div>
        </%doc>

    %elif PDF_ENGINE in ["xhtml2pdf"]:
        ## xhtml2pdf
        ## hard to get logos positioned any other way than within a table
        <div class="header">
            <table class="noborder">
                <tr class="noborder">
                    <td class="noborderphoto" width="45%">
                        <img src="file://${ request.config.camcops_logo_file_absolute }"
                             height="${ va.PDF_LOGO_HEIGHT }"
                             align="left" />
                    </td>
                    <td class="noborderphoto" width="10%"></td>
                    <td class="noborderphoto" width="45%">
                        <img src="file://${ request.config.local_logo_file_absolute }"
                             height="${ va.PDF_LOGO_HEIGHT }"
                             align="right" />
                    </td>
                </tr>
            </table>
        </div>
    %else:
        MISSING_PDF_LOGO_BLOCK_UNKNOWN_ENGINE
    %endif

</%block>

${next.body()}
