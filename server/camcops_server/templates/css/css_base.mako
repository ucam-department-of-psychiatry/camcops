## css_base.mako
<%page args="
        MAINFONTSIZE: str,
        SMALLGAP: str,
        ELEMENTGAP: str,
        NORMALPAD: str,
        TABLEPAD: str,
        INDENT_NORMAL: str,
        INDENT_LARGE: str,
        THINLINE: str,
        ZERO: str,
        MAINMARGIN: str,
        BODYPADDING: str,
        BANNER_PADDING: str,

        PDF_LOGO_HEIGHT: str = '20mm',

        paged_media: bool = False,
        ORIENTATION: str = 'portrait'
    "/>

<%doc>

CSS notes:

Sequences of 4: top, right, bottom, left
margin is outside, padding is inside

#identifier
.class

http://www.w3schools.com/cssref/css_selectors.asp
http://stackoverflow.com/questions/4013604
http://stackoverflow.com/questions/6023419

</%doc>

<%
    SMALLFONTSIZE = "0.85em"
    TINYFONTSIZE = "0.7em"
    LARGEFONTSIZE = "1.2em"
    GIANTFONTSIZE = "1.4em"
    BANNERFONTSIZE = "1.6em"

    # Rules: line height is 1.1-1.2 * font size
    # ... but an em is related to the calculated font-size of the element,
    #   http://www.impressivewebs.com/understanding-em-units-css/
    # so it can always be 1.2:
    MAINLINEHEIGHT = "1.1em"
    SMALLLINEHEIGHT = "1.1em"
    TINYLINEHEIGHT = "1.0em"  # except this one
    LARGELINEHEIGHT = "1.1em"
    GIANTLINEHEIGHT = "1.1em"
    BANNERLINEHIGHT = "1.1em"
    TABLELINEHEIGHT = "1.1em"

    VSPACE_NORMAL = "0.5em"
    VSPACE_LARGE = "0.8em"

    SIGNATUREHEIGHT = "3em"
%>

/* Display PNG fallback image... */
svg img.svg {
    display: none;
}
img.pngfallback {
    display: inline;
}
/* ... unless our browser supports SVG */
html.svg svg img.svg {
    display: inline;
}
html.svg img.pngfallback {
    display: none;
}

/* Overall defaults */

body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: ${MAINFONTSIZE};
    line-height: ${MAINLINEHEIGHT};
    margin: ${ELEMENTGAP} ${ZERO} ${ELEMENTGAP} ${ZERO};
    padding: ${BODYPADDING};
}
code {
    font-size: 0.8em;
    font-family: Consolas, Monaco, 'Lucida Console', 'Liberation Mono',
        'DejaVu Sans Mono', 'Bitstream Vera Sans Mono', 'Courier New';
    background-color: #eeeeee;
    padding: 1px 5px 1px 5px;
}
div {
    margin: ${ELEMENTGAP} ${ZERO} ${ELEMENTGAP} ${ZERO};
    padding: ${NORMALPAD};
}
em {
    color: rgb(0, 0, 255);
    font-style: normal;
}
h1 {
    font-size: ${GIANTFONTSIZE};
    line-height: ${GIANTLINEHEIGHT};
    font-weight: bold;
    margin: ${ZERO};
}
h2 {
    font-size: ${LARGEFONTSIZE};
    line-height: ${LARGELINEHEIGHT};
    font-weight: bold;
    margin: ${ZERO};
}
h3 {
    font-size: ${LARGEFONTSIZE};
    line-height: ${LARGELINEHEIGHT};
    font-weight: bold;
    font-style: italic;
    margin: ${ZERO};
}
img {
    max-width: 100%;
    max-height: 100%;
}
p {
    margin: ${ELEMENTGAP} ${ZERO} ${ELEMENTGAP} ${ZERO};
}
sup, sub {
    font-size: 0.7em; /* 1 em is the size of the parent font */
    vertical-align: baseline;
    position: relative;
    top: -0.5em;
}
sub {
    top: 0.5em;
}
table {
    width: 100%; /* particularly for PDFs */
    vertical-align: top;
    border-collapse: collapse;
    border: ${THINLINE} solid black;
    padding: ${ZERO};
    margin: ${ELEMENTGAP} ${ZERO} ${ELEMENTGAP} ${ZERO};
}
tr, th, td {
    vertical-align: top;
    text-align: left;
    margin: ${ZERO};
    padding: ${TABLEPAD};
    border: ${THINLINE} solid black;
    line-height: ${TABLELINEHEIGHT};
}

/* Specific classes */

.badidpolicy_mild {
    background-color: rgb(255, 255, 153);
}
.badidpolicy_severe {
    background-color: rgb(255, 255, 0);
}
.banner {
    text-align: center;
    font-size: ${BANNERFONTSIZE};
    line-height: ${BANNERLINEHIGHT};
    padding: ${BANNER_PADDING};
    margin: ${ZERO};
}
.banner_referral_general_adult {
    background-color: rgb(255, 165, 0);
}
.banner_referral_old_age {
    background-color: rgb(0, 255, 127);
}
.banner_referral_substance_misuse {
    background-color: rgb(0, 191, 255);
}
.clinician {
    background-color: rgb(200, 255, 255);
}
table.clinician, table.clinician th, table.clinician td {
    border: ${THINLINE} solid black;
}
.copyright {
    font-style: italic;
    font-size: ${TINYFONTSIZE};
    line-height: ${TINYLINEHEIGHT};
    background-color: rgb(227, 227, 227);
}
.ctv_datelimit_start {
    /* line below */
    text-align: right;
    border-style: none none solid none;
    border-width: ${THINLINE};
    border-color: black;
}
.ctv_datelimit_end {
    /* line above */
    text-align: right;
    border-style: solid none none none;
    border-width: ${THINLINE};
    border-color: black;
}
.ctv_taskheading {
    background-color: rgb(200, 200, 255);
    font-weight: bold;
}
.ctv_fieldheading {
    background-color: rgb(200, 200, 200);
    font-weight: bold;
    font-style: italic;
    margin: ${ELEMENTGAP} ${ZERO} ${SMALLGAP} ${INDENT_NORMAL};
}
.ctv_fieldsubheading {
    background-color: rgb(200, 200, 200);
    font-style: italic;
    margin: ${ELEMENTGAP} ${ZERO} ${SMALLGAP} ${INDENT_NORMAL};
}
.ctv_fielddescription {
    font-style: italic;
    margin: ${ELEMENTGAP} ${ZERO} ${SMALLGAP} ${INDENT_NORMAL};
}
.ctv_fieldcontent {
    font-weight: bold;
    margin: ${SMALLGAP} ${ZERO} ${ELEMENTGAP} ${INDENT_NORMAL};
}
.ctv_warnings {
    margin: ${ELEMENTGAP} ${ZERO} ${SMALLGAP} ${INDENT_NORMAL};
}
.error {
    color: rgb(255, 0, 0);
}
.explanation {
    background-color: rgb(200, 255, 200);
}
table.extradetail {
    border: ${THINLINE} solid black;
    background-color: rgb(210, 210, 210);
}
table.extradetail th {
    border: ${THINLINE} solid black;
    font-style: italic;
    font-weight: bold;
    font-size: ${TINYFONTSIZE};
}
table.extradetail td {
    border: ${THINLINE} solid black;
    font-size: ${TINYFONTSIZE};
}
tr.extradetail2 {
    background-color: rgb(240, 240, 240);
}
td.figure {
    padding: ${ZERO};
    background-color: rgb(255, 255, 255);
}
div.filter {
    /* for task filters */
    margin-left: ${INDENT_LARGE};
    padding: ${ZERO};
}
form.filter {
    /* for task filters */
    display: inline;
    margin: ${ZERO};
}
.footnotes {
    /* font-style: italic; */
    font-size: ${SMALLFONTSIZE};
    line-height: ${SMALLLINEHEIGHT};
}
.formtitle {
    font-size: ${LARGEFONTSIZE};
    color: rgb(34, 139, 34);
}
table.general, table.general th, table.general td {
    border: ${THINLINE} solid black;
}
table.general th.col1, table.general td.col1 {
    width: 22%;
}
table.general th.col2, table.general td.col2 {
    width: 78%;
}
.green {
    color: rgb(34, 139, 34);
}
p.hangingindent {
    padding-left: ${INDENT_NORMAL};
    text-indent: -${INDENT_NORMAL};
}
.heading {
    background-color: rgb(0, 0, 0);
    color: rgb(255, 255, 255);
    font-style: italic;
}
.highlight {
    background-color: rgb(255, 250, 205);
}
.important {
    color: rgb(64, 0, 192);
    font-weight: bold;
}
.specialnote {
    background-color: rgb(255, 255, 153);
}
.live_on_tablet {
    background-color: rgb(216, 208, 245);
}
.incomplete {
    background-color: rgb(255, 165, 0);
}
.superuser {
    background-color: rgb(255, 192, 203);
}
p.indent {
    margin-left: ${INDENT_NORMAL};
}
div.indented {
    margin-left: ${INDENT_LARGE};
}
.navigation {
    background-color: rgb(200, 255, 200);
}
.noborder {
    border: none;
    /* NB also: hidden overrides none with border-collapse */
}
.noborderphoto {
    padding: ${ZERO};
    border: none;
}
.office {
    background-color: rgb(227, 227, 227);
    font-style: italic;
    font-size: ${TINYFONTSIZE};
    line-height: ${TINYLINEHEIGHT};
}
.patient {
    background-color: rgb(255, 200, 200);
}
.pdf_logo_header {
    width: 100%;
    border: none;
}
.pdf_logo_header table, .pdf_logo_header tr {
    width: 100%;
    border: none;
}
.pdf_logo_header .image_td {
    width: 45%;
    border: none;
}
.pdf_logo_header .centregap_td {
    width: 10%;
    border: none;
}
.pdf_logo_header .logo_left {
    float: left;
    max-width: 100%;
    max-height: ${PDF_LOGO_HEIGHT};
    height: auto;
    width: auto;
}
.pdf_logo_header .logo_right {
    float: right;
    max-width: 100%;
    max-height: ${PDF_LOGO_HEIGHT};
    height: auto;
    width: auto;
}
.photo {
    padding: ${ZERO};
}
.respondent {
    background-color: rgb(189, 183, 107);
}
table.respondent, table.respondent th, table.respondent td {
    border: ${THINLINE} solid black;
}
.signature_label {
    border: none;
    text-align: center;
}
.signature {
    line-height: ${SIGNATUREHEIGHT};
    border: ${THINLINE} solid black;
}
.smallprint {
    font-style: italic;
    font-size: ${SMALLFONTSIZE};
}
.subheading {
    background-color: rgb(200, 200, 200);
    font-style: italic;
}
.subsubheading {
    font-style: italic;
}
.summary {
    background-color: rgb(200, 200, 255);
}
table.summary, .summary th, .summary td {
    border: ${THINLINE} solid black;
}
table.taskconfig, .taskconfig th, .taskconfig td {
    border: ${THINLINE} solid black;
    background-color: rgb(230, 230, 230);
}
table.taskconfig th {
    font-style: italic; font-weight: normal;
}
table.taskdetail, .taskdetail th, .taskdetail td {
    border: ${THINLINE} solid black;
}
table.taskdetail th {
    font-weight: normal; font-style: italic;
}
table.taskdetail td {
    font-weight: normal;
}
.taskheader {
    background-color: rgb(200, 200, 200);
}
.trackerheader {
    font-size: ${TINYFONTSIZE};
    line-height: ${TINYLINEHEIGHT};
    background-color: rgb(218, 112, 240);
}
.tracker_all_consistent {
    font-style: italic;
    font-size: ${TINYFONTSIZE};
    line-height: ${TINYLINEHEIGHT};
    background-color: rgb(227, 227, 227);
}
.warning {
    background-color: rgb(255, 100, 100);
}

/* The next three: need both L/R to float and clear:both for IE */
.web_logo_header {
    display: block;
    overflow: hidden;
    width: 100%;
    border: none;
    clear: both;
}
/* ... overflow:hidden so the div expands to its floating contents */
.web_logo_header .logo_left {
    width: 45%;
    float: left;
    text-decoration: none;
    border: ${ZERO};
}
.web_logo_header .logo_right {
    width: 45%;
    float: right;
    text-decoration: none;
    border: ${ZERO};
}

/* For tables that will make it to a PDF, fix Weasyprint column widths.
   But not for all (e.g. webview task list) tables. */
table.clinician, table.extradetail, table.general,
        table.pdf_logo_header, table.summary,
        table.taskconfig, table.taskdetail,
        table.fixed {
    table-layout: fixed;
}

%if paged_media:

    /* PDF extras */
    #headerContent {
        font-size: ${SMALLFONTSIZE};
        line-height: ${SMALLLINEHEIGHT};
    }
    #footerContent {
        font-size: ${SMALLFONTSIZE};
        line-height: ${SMALLLINEHEIGHT};
    }
    
    /* PDF paging via CSS Paged Media */
    @page {
        size: A4 ${ORIENTATION};
        margin-left: ${MAINMARGIN};
        margin-right: ${MAINMARGIN};
        margin-top: ${MAINMARGIN};
        margin-bottom: ${MAINMARGIN};
        @frame header {
            /* -pdf-frame-border: 1; */ /* for debugging */
            -pdf-frame-content: headerContent;
            top: 1cm;
            margin-left: ${MAINMARGIN};
            margin-right: ${MAINMARGIN};
        }
        @frame footer {
            /* -pdf-frame-border: 1; */ /* for debugging */
            -pdf-frame-content: footerContent;
            bottom: 0.5cm; /* distance up from page's bottom margin? */
            height: 1cm; /* height of the footer */
            margin-left: ${MAINMARGIN};
            margin-right: ${MAINMARGIN};
        }
    }

    <%doc>
    WEASYPRINT: NOT WORKING PROPERLY YET: WEASYPRINT DOESN'T YET SUPPORT RUNNING ELEMENTS
    http://librelist.com/browser//weasyprint/2013/7/4/header-and-footer-for-each-page/#abe45ec357d593df44ffca48253817ef
    http://weasyprint.org/docs/changelog/
    </%doc>

%endif
