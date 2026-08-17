## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/css/css_base.mako

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

CSS notes:

- Sequences of 4: top, right, bottom, left

- margin is outside, padding is inside

- ``#identifier``
- ``.class``

- http://www.w3schools.com/cssref/css_selectors.asp
- http://stackoverflow.com/questions/4013604
- http://stackoverflow.com/questions/6023419

</%doc>

<%page expression_filter="n"/>
## ... everything here is trusted.

<%
    # Passing parameters through templates:
    # https://groups.google.com/forum/#!topic/mako-discuss/U5jNLDqgppQ

    va = self.get_css_varargs()  # calls child
%>


/* Overall defaults */

body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: ${va.MAINFONTSIZE};
    margin: ${va.ZERO} ${va.ZERO} ${va.ZERO} ${va.ZERO};  /* margin here affects form layout too */
    padding: ${va.BODYPADDING};
}
code {
    font-size: 0.8em;
    font-family: Consolas, Monaco, 'Lucida Console', 'Liberation Mono',
        'DejaVu Sans Mono', 'Bitstream Vera Sans Mono', 'Courier New';
    background-color: #eeeeee;
    padding: 1px 5px 1px 5px;
}
div {
    margin: ${va.ELEMENTGAP} ${va.ZERO} ${va.ELEMENTGAP} ${va.ZERO};
    padding: ${va.NORMALPAD};
}
em {
    color: rgb(0, 0, 255);  /* blue */
    font-style: normal;
}
h1 {
    font-size: ${va.GIANTFONTSIZE};
    line-height: ${va.GIANTLINEHEIGHT};
    font-weight: bold;
    margin: ${va.TWICE_ELEMENTGAP} ${va.ZERO} ${va.ZERO} ${va.ZERO};
}
h2 {
    font-size: ${va.LARGEFONTSIZE};
    line-height: ${va.LARGELINEHEIGHT};
    font-weight: bold;
    margin: ${va.ELEMENTGAP} ${va.ZERO} ${va.ZERO} ${va.ZERO};
}
h3 {
    font-size: ${va.NORMALFONTSIZE};
    line-height: ${va.MAINLINEHEIGHT};
    font-weight: bold;
    margin: ${va.ELEMENTGAP} ${va.ZERO} ${va.ZERO} ${va.ZERO};
}
h4 {
    font-size: ${va.NORMALFONTSIZE};
    line-height: ${va.MAINLINEHEIGHT};
    font-weight: normal;
    font-style: italic;
    margin: ${va.ELEMENTGAP} ${va.ZERO} ${va.ZERO} ${va.ZERO};
}
img {
    max-width: 100%;
    max-height: 100%;
}
ol, ul {
    margin: ${va.ELEMENTGAP};
}
p {
    margin: ${va.ELEMENTGAP} ${va.ZERO} ${va.ELEMENTGAP} ${va.ZERO};  /* see esp. p within div, such as task footnotes for web version */
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
/* Matplotlib fixes width and height in point sizes */
svg {
    max-width: 100%;
    max-height: 100%;
}
table {
    width: 100%; /* particularly for PDFs */
    vertical-align: top;
    border-collapse: collapse;
    border: ${va.THINLINE} solid black;
    padding: ${va.ZERO};
    margin: ${va.ELEMENTGAP} ${va.ZERO} ${va.ELEMENTGAP} ${va.ZERO};
}
tr, th, td {
    vertical-align: top;
    text-align: left;
    margin: ${va.ZERO};
    padding: ${va.TABLEPAD};
    border: ${va.THINLINE} solid black;
    line-height: ${va.TABLELINEHEIGHT};
}

blockquote > p {
    background: #eee;  /* light grey */
    padding: 15px;
}

blockquote > p::before {
    content: '\201C';  /* left double quote */
}

blockquote > p::after {
    content: '\201D';  /* right double quote */
}

/* Specific classes */

.badidpolicy_mild {
    background-color: rgb(255, 255, 153);  /* canary */
}
.badidpolicy_severe {
    background-color: rgb(255, 255, 0);  /* yellow */
}
.invalid_id_number_foreground {
    color: rgb(128, 0, 128);  /* purple */
    font-weight: bold;
}
.invalid_id_number_background {
    background-color: rgb(218, 112, 214);  /* orchid */
}
.banner {
    text-align: center;
    font-size: ${va.BANNERFONTSIZE};
    line-height: ${va.BANNERLINEHIGHT};
    padding: ${va.BANNER_PADDING};
    margin: ${va.ZERO};
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
    border: ${va.THINLINE} solid black;
}
.copyright {
    font-style: italic;
    font-size: ${va.TINYFONTSIZE};
    line-height: ${va.TINYLINEHEIGHT};
    background-color: rgb(227, 227, 227);
}
.ctv_datelimit_start {
    /* line below */
    text-align: right;
    border-style: none none solid none;
    border-width: ${va.THINLINE};
    border-color: black;
}
.ctv_datelimit_end {
    /* line above */
    text-align: right;
    border-style: solid none none none;
    border-width: ${va.THINLINE};
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
    margin: ${va.ELEMENTGAP} ${va.ZERO} ${va.SMALLGAP} ${va.INDENT_NORMAL};
}
.ctv_fieldsubheading {
    background-color: rgb(200, 200, 200);
    font-style: italic;
    margin: ${va.ELEMENTGAP} ${va.ZERO} ${va.SMALLGAP} ${va.INDENT_NORMAL};
}
.ctv_fielddescription {
    font-style: italic;
    margin: ${va.ELEMENTGAP} ${va.ZERO} ${va.SMALLGAP} ${va.INDENT_NORMAL};
}
.ctv_fieldcontent {
    /* font-weight: bold; */
    margin: ${va.SMALLGAP} ${va.ZERO} ${va.ELEMENTGAP} ${va.INDENT_NORMAL};
}
.ctv_warnings {
    margin: ${va.ELEMENTGAP} ${va.ZERO} ${va.SMALLGAP} ${va.INDENT_NORMAL};
}
.duplicates {
    list-style: none;
}
.error {
    color: rgb(255, 0, 0);
}
.explanation {
    background-color: rgb(200, 255, 200);
}
.filters {
    font-style: italic;
}
.info {
    color: rgb(0, 102, 0);
    font-weight: bold;
}
input[type="date"].form-control,
input[type="time"].form-control {
    line-height: normal; /* Bootstrap default looks wrong */
}
input[name="mfa_secret_key"].form-control {
    background-color: inherit;
    border: none;
    font-size: medium;
    font-weight: bold;
    color: black;
    padding: 0;
    box-shadow: none;
}
table.extradetail {
    border: ${va.THINLINE} solid black;
    background-color: rgb(210, 210, 210);
}
table.extradetail th {
    border: ${va.THINLINE} solid black;
    font-style: italic;
    font-weight: bold;
    font-size: ${va.TINYFONTSIZE};
}
table.extradetail td {
    border: ${va.THINLINE} solid black;
    font-size: ${va.TINYFONTSIZE};
}
.extradetail2 {
    background-color: rgb(240, 240, 240);
}
td.figure {
    padding: ${va.ZERO};
    background-color: rgb(255, 255, 255);
}
div.filter {
    /* for task filters */
    margin-left: ${va.INDENT_LARGE};
    padding: ${va.ZERO};
}
form.filter {
    /* for task filters */
    display: inline;
    margin: ${va.ZERO};
}
.flash_messages {
    padding:0;
    margin:0;
}
.footnotes {
    /* font-style: italic; */
    font-size: ${va.SMALLFONTSIZE};
    line-height: ${va.SMALLLINEHEIGHT};
}
.formtitle {
    font-size: ${va.LARGEFONTSIZE};
    color: rgb(34, 139, 34);
}
table.general, table.general th, table.general td {
    border: ${va.THINLINE} solid black;
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
    padding-left: ${va.INDENT_NORMAL};
    text-indent: -${va.INDENT_NORMAL};
}
.heading {
    background-color: rgb(0, 0, 0);
    color: rgb(255, 255, 255);
    font-style: italic;
}
.highlight {
    background-color: rgb(255, 250, 205);
}
.idnum {
    margin: 0;
}
.important {
    color: rgb(64, 0, 192);
    font-weight: bold;
}
.ip_use_label {
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
    margin-left: ${va.INDENT_NORMAL};
}
div.indented {
    margin-left: ${va.INDENT_LARGE};
}
.menu {
    list-style: none;
    padding-left: ${va.INDENT_NORMAL};
}
.navigation {
    background-color: rgb(200, 255, 200);
}
.noborder {
    border: none;
    /* NB also: hidden overrides none with border-collapse */
}
.noborderphoto {
    padding: ${va.ZERO};
    border: none;
}
.office {
    background-color: rgb(227, 227, 227);
    font-style: italic;
    font-size: ${va.TINYFONTSIZE};
    line-height: ${va.TINYLINEHEIGHT};
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
    max-height: ${va.PDF_LOGO_HEIGHT};
    height: auto;
    width: auto;
}
.pdf_logo_header .logo_right {
    float: right;
    max-width: 100%;
    max-height: ${va.PDF_LOGO_HEIGHT};
    height: auto;
    width: auto;
}
.photo {
    padding: ${va.ZERO};
}

.mini_table {
    padding: 0px;
    border: none;
}

.mini_table > table {
    border-collapse:collapse;
    border-style:hidden;
    margin: 0px;
}

.mini_table > table > tbody > tr > td {
    border: none;
}
.qr_container {
    margin: 0px;
    padding: 0px;
}
.respondent {
    background-color: rgb(189, 183, 107);
}
table.respondent, table.respondent th, table.respondent td {
    border: ${va.THINLINE} solid black;
}
.signature_label {
    border: none;
    text-align: center;
}
.signature {
    line-height: ${va.SIGNATUREHEIGHT};
    border: ${va.THINLINE} solid black;
}
.smallprint {
    font-style: italic;
    font-size: ${va.SMALLFONTSIZE};
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
    border: ${va.THINLINE} solid black;
}
table.taskconfig, .taskconfig th, .taskconfig td {
    border: ${va.THINLINE} solid black;
    background-color: rgb(230, 230, 230);
}
table.taskconfig th {
    font-style: italic; font-weight: normal;
}
table.taskdetail, .taskdetail th, .taskdetail td {
    border: ${va.THINLINE} solid black;
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
    font-size: ${va.TINYFONTSIZE};
    line-height: ${va.TINYLINEHEIGHT};
    background-color: rgb(218, 112, 240);
}
.tracker_all_consistent {
    font-style: italic;
    font-size: ${va.TINYFONTSIZE};
    line-height: ${va.TINYLINEHEIGHT};
    background-color: rgb(227, 227, 227);
}
.warning {
    background-color: rgb(255, 110, 110);
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
    border: ${va.ZERO};
}
.web_logo_header .logo_right {
    width: 45%;
    float: right;
    text-decoration: none;
    border: ${va.ZERO};
}

%if va.paged_media:

    /* PDF extras */
    #headerContent {
        font-size: ${va.SMALLFONTSIZE};
        line-height: ${va.SMALLLINEHEIGHT};
    }
    #footerContent {
        font-size: ${va.SMALLFONTSIZE};
        line-height: ${va.SMALLLINEHEIGHT};
    }

    /* PDF paging via CSS Paged Media */
    @page {
        font-family: Arial, Helvetica, sans-serif;
        font-size: ${va.SMALLFONTSIZE};
        line-height: ${va.SMALLLINEHEIGHT};
        size: A4 ${va.ORIENTATION};
        margin-left: ${va.MAINMARGIN};
        margin-right: ${va.MAINMARGIN};
        margin-top: ${va.MAINMARGIN};
        margin-bottom: ${va.MAINMARGIN};
        @frame header {
            /* -pdf-frame-border: 1; */ /* for debugging */
            -pdf-frame-content: headerContent;
            top: 1cm;
            margin-left: ${va.MAINMARGIN};
            margin-right: ${va.MAINMARGIN};
        }
        @frame footer {
            /* -pdf-frame-border: 1; */ /* for debugging */
            -pdf-frame-content: footerContent;
            bottom: 0.5cm; /* distance up from page's bottom margin? */
            height: 1cm; /* height of the footer */
            margin-left: ${va.MAINMARGIN};
            margin-right: ${va.MAINMARGIN};
        }
    }
%endif

/* Task specifics */
.ace3-col-task-aspect,
.ace3-col-question {
    width: 67%;
}

.ace3-col-setting,
.ace3-col-answer-score {
    width: 33%;
}
.aims-question-col {
    width: 50%;
}
.aims-answer-col {
    width: 50%;
}

.apeq-cpft-perinatal-question-col {
    width: 60%;
}
.apeq-cpft-perinatal-answer-col {
    width: 40%;
}

.apeqpt-question-col {
    width: 60%;
}
.apeqpt-answer-col {
    width: 40%;
}

.aq-statement-col {
    width: 70%;
}
.aq-answer-col {
    width: 20%;
}
.aq-score-col {
    width: 10%;
}

.aq10-statement-col {
    width: 70%;
}
.aq10-answer-col {
    width: 20%;
}
.aq10-score-col {
    width: 10%;
}

.asdas-question-col {
    width: 60%;
}
.asdas-answer-col {
    width: 40%;
}

.audit-question-col {
    width: 50%;
}
.audit-answer-col {
    width: 50%;
}

.audit-c-question-col {
    width: 50%;
}
.audit-c-answer-col {
    width: 50%;
}

.badls-question-col {
    width: 30%;
}
.badls-answer-col {
    width: 50%;
}
.badls-score-col {
    width: 20%;
}

.basdai-question-col {
    width: 60%;
}
.basdai-answer-col {
    width: 40%;
}

.bdi-question-col {
    width: 70%;
}
.bdi-answer-col {
    width: 30%;
}


.bprs-question-col {
    width: 60%;
}
.bprs-answer-col {
    width: 40%;
}

.bprse-question-col {
    width: 60%;
}
.bprse-answer-col {
    width: 40%;
}

.cage-question-col {
    width: 70%;
}
.cage-answer-col {
    width: 30%;
}


.caps-question-col {
    width: 60%;
}
.caps-endorsed-col {
    width: 10%;
}
.caps-distress-col {
    width: 10%;
}
.caps-intrusiveness-col {
    width: 10%;
}
.caps-frequency-col {
    width: 10%;
}

.cardinal-expdetthreshold-configuration-col {
    width: 50%;
}
.cardinal-expdetthreshold-value-col {
    width: 50%;
}

.cardinal-expdetthreshold-measure-col {
    width: 50%;
}
.cardinal-expdetthreshold-value-col {
    width: 50%;
}

.cardinal-expdet-configuration-col {
    width: 50%;
}
.cardinal-expdet-value-col {
    width: 50%;
}

.cardinal-expdet-measure-col {
    width: 50%;
}
.cardinal-expdet-value-col {
    width: 50%;
}

.cbir-question-col {
    width: 50%;
}
.cbir-frequency-col {
    width: 25%;
}
.cbir-distress-col {
    width: 25%;
}


.cesd-question-col {
    width: 70%;
}
.cesd-answer-col {
    width: 30%;
}

.cesdr-question-col {
    width: 70%;
}
.cesdr-answer-col {
    width: 30%;
}

.cet-question-col {
    width: 60%;
}
.cet-answer-col {
    width: 40%;
}

.cgi-question-col {
    width: 30%;
}
.cgi-answer-col {
    width: 70%;
}

.cgi-i-question-col {
    width: 50%;
}
.cgi-i-answer-col {
    width: 50%;
}

.cgisch-question-col {
    width: 70%;
}
.cgisch-answer-col {
    width: 30%;
}

.chit-question-col {
    width: 60%;
}
.chit-answer-col {
    width: 40%;
}

.cia-question-col {
    width: 60%;
}
.cia-response-col {
    width: 40%;
}

.cisr-page-col {
    width: 75%;
}

.cisr-page-col {
    width: 75%;
}

.ciwa-question-col {
    width: 35%;
}
.ciwa-answer-col {
    width: 65%;
}


.cope-brief-question-col {
    width: 50%;
}
.cope-brief-answer-col {
    width: 50%;
}

.core10-question-col {
    width: 60%;
}
.core10-answer-col {
    width: 40%;
}

.cpft-covid-medical-question-col {
    width: 60%;
}
.cpft-covid-medical-answer-col {
    width: 40%;
}


.cpft-research-preferences-question-col {
    width: 60%;
}
.cpft-research-preferences-answer-col {
    width: 40%;
}


.dast-question-col {
    width: 80%;
}
.dast-answer-col {
    width: 20%;
}

.deakin-s1-healthreview-question-col {
    width: 50%;
}
.deakin-s1-healthreview-answer-col {
    width: 50%;
}

.demoquestionnaire-question-col {
    width: 50%;
}
.demoquestionnaire-answer-col {
    width: 50%;
}

.demqol-question-col {
    width: 50%;
}
.demqol-answer-col {
    width: 50%;
}

.demqolproxy-question-col {
    width: 50%;
}
.demqolproxy-answer-col {
    width: 50%;
}

.diagnosis-diagnosis-col {
    width: 10%;
}
.diagnosis-code-col {
    width: 10%;
}
.diagnosis-description-col {
    width: 40%;
}
.diagnosis-comment-col {
    width: 40%;
}

.distressthermometer-question-col {
    width: 50%;
}
.distressthermometer-answer-col {
    width: 50%;
}

.edeq-question-col {
    width: 60%;
}
.edeq-score-col {
    width: 40%;
}

.elixhauserci-question-col {
    width: 50%;
}
.elixhauserci-answer-col {
    width: 50%;
}


.epds-question-col {
    width: 50%;
}
.epds-answer-col {
    width: 50%;
}

.eq5d5l-question-col {
    width: 60%;
}
.eq5d5l-answer-col {
    width: 40%;
}

.esspri-question-col {
    width: 60%;
}
.esspri-answer-col {
    width: 40%;
}

.factg-question-col {
    width: 50%;
}
.factg-answer-col {
    width: 50%;
}

.fast-question-col {
    width: 60%;
}
.fast-answer-col {
    width: 40%;
}

.fft-question-col {
    width: 50%;
}
.fft-answer-col {
    width: 50%;
}

.frs-question-col {
    width: 50%;
}
.frs-answer-col {
    width: 50%;
}

.gad7-question-col {
    width: 50%;
}
.gad7-answer-col {
    width: 50%;
}


.gbogres-goal-col {
    width: 85%;
}
.gbogres-goal-col {
    width: 85%;
}

.gbogpc-date-col {
    width: 30%;
}

.gbogras-goal-col {
    width: 15%;
}
.gbogras-description-col {
    width: 70%;
}
.gbogras-progress-col {
    width: 15%;
}

.gds15-question-col {
    width: 70%;
}
.gds15-answer-col {
    width: 30%;
}

.gmcpq-question-col {
    width: 60%;
}
.gmcpq-answer-col {
    width: 40%;
}

.hads-question-col {
    width: 50%;
}
.hads-answer-col {
    width: 50%;
}

.hama-question-col {
    width: 50%;
}
.hama-answer-col {
    width: 50%;
}

.hamd-question-col {
    width: 40%;
}
.hamd-answer-col {
    width: 60%;
}

.hamd7-question-col {
    width: 30%;
}
.hamd7-answer-col {
    width: 70%;
}

.honos-question-col {
    width: 50%;
}
.honos-answer-col {
    width: 50%;
}

.honos65-question-col {
    width: 50%;
}
.honos65-answer-col {
    width: 50%;
}

.honosca-question-col {
    width: 50%;
}
.honosca-answer-col {
    width: 50%;
}

.icd10depressive-question-col {
    width: 80%;
}
.icd10depressive-answer-col {
    width: 20%;
}

.icd10manic-question-col {
    width: 80%;
}
.icd10manic-answer-col {
    width: 20%;
}

.icd10mixed-question-col {
    width: 80%;
}
.icd10mixed-answer-col {
    width: 20%;
}

.icd10schizophrenia-question-col {
    width: 80%;
}
.icd10schizophrenia-answer-col {
    width: 20%;
}

.icd10schizotypal-question-col {
    width: 80%;
}
.icd10schizotypal-answer-col {
    width: 20%;
}

.icd10specpd-question-col {
    width: 80%;
}
.icd10specpd-answer-col {
    width: 20%;
}

.ided3d-configuration-col {
    width: 50%;
}
.ided3d-value-col {
    width: 50%;
}

.ided3d-measure-col {
    width: 50%;
}
.ided3d-value-col {
    width: 50%;
}

.iesr-question-col {
    width: 75%;
}
.iesr-answer-col {
    width: 25%;
}

.ifs-question-col {
    width: 50%;
}
.ifs-answer-col {
    width: 50%;
}

.irac-question-col {
    width: 50%;
}
.irac-answer-col {
    width: 50%;
}

.isaaq10-title-col {
    width: 70%;
}
.isaaq10-score-col {
    width: 30%;
}


.isaaqed-title-col {
    width: 70%;
}
.isaaqed-score-col {
    width: 30%;
}


.khandaker-mojo-medical-question-col {
    width: 60%;
}
.khandaker-mojo-medical-answer-col {
    width: 40%;
}

.khandaker-mojo-medical-question-col {
    width: 60%;
}
.khandaker-mojo-medical-answer-col {
    width: 40%;
}

.khandaker-mojo-medical-question-col {
    width: 60%;
}
.khandaker-mojo-medical-answer-col {
    width: 40%;
}


.khandaker-mojo-sociodemographics-question-col {
    width: 60%;
}
.khandaker-mojo-sociodemographics-answer-col {
    width: 40%;
}

.kirby-mcq-question-col {
    width: 75%;
}
.kirby-mcq-answer-col {
    width: 25%;
}

.lynall-iam-life-question-col {
    width: 40%;
}
.lynall-iam-life-experienced-col {
    width: 20%;
}
.lynall-iam-life-severity-col {
    width: 20%;
}
.lynall-iam-life-frequency-col {
    width: 20%;
}

.lynall-iam-medical-req-col {
    width: 40%;
}
.lynall-iam-medical-req-col {
    width: 40%;
}

.maas-question-col {
    width: 60%;
}
.maas-answer-col {
    width: 40%;
}

.mast-question-col {
    width: 80%;
}
.mast-answer-col {
    width: 20%;
}

.mds-updrs-question-col {
    width: 70%;
}
.mds-updrs-answer-col {
    width: 30%;
}

.mfi20-question-col {
    width: 60%;
}
.mfi20-answer-col {
    width: 40%;
}

.moca-question-col {
    width: 69%;
}
.moca-score-col {
    width: 31%;
}

.nart-word-col {
    width: 16%;
}

.npiq-question-col {
    width: 40%;
}
.npiq-endorsed-col {
    width: 20%;
}
.npiq-severity-col {
    width: 20%;
}
.npiq-distress-col {
    width: 20%;
}

.ors-question-col {
    width: 60%;
}
.ors-answer-col {
    width: 40%;
}

.panss-question-col {
    width: 40%;
}
.panss-answer-col {
    width: 60%;
}

.paradise24-question-col {
    width: 60%;
}
.paradise24-score-col {
    width: 40%;
}

.pbq-question-col {
    width: 60%;
}
.pbq-answer-col {
    width: 40%;
}

.pcl-question-col {
    width: 70%;
}
.pcl-answer-col {
    width: 30%;
}

.pcl5-question-col {
    width: 70%;
}
.pcl5-answer-col {
    width: 30%;
}

.pdss-question-col {
    width: 60%;
}
.pdss-answer-col {
    width: 40%;
}

.perinatal-poem-question-col {
    width: 60%;
}
.perinatal-poem-answer-col {
    width: 40%;
}


.phq15-question-col {
    width: 70%;
}
.phq15-answer-col {
    width: 30%;
}

.phq8-question-col {
    width: 60%;
}
.phq8-answer-col {
    width: 40%;
}

.phq9-question-col {
    width: 60%;
}
.phq9-answer-col {
    width: 40%;
}


.pswq-question-col {
    width: 70%;
}
.pswq-answer-col {
    width: 15%;
}
.pswq-score-col {
    width: 15%;
}


.qolbasic-scale-col {
    width: 33%;
}
.qolbasic-answer-col {
    width: 33%;
}

.qolsg-measure-col {
    width: 50%;
}
.qolsg-value-col {
    width: 50%;
}

.rand36-question-col {
    width: 60%;
}
.rand36-answer-col {
    width: 30%;
}
.rand36-score-col {
    width: 10%;
}

.rapid3-question-col {
    width: 60%;
}
.rapid3-answer-col {
    width: 40%;
}

.service-satisfaction-question-col {
    width: 50%;
}
.service-satisfaction-answer-col {
    width: 50%;
}

.sfmpq2-question-col {
    width: 60%;
}
.sfmpq2-answer-col {
    width: 40%;
}

.shaps-question-col {
    width: 60%;
}
.shaps-answer-col {
    width: 40%;
}

.slums-question-col {
    width: 80%;
}
.slums-score-col {
    width: 20%;
}

.smast-question-col {
    width: 80%;
}
.smast-answer-col {
    width: 20%;
}

.srs-question-col {
    width: 60%;
}
.srs-answer-col {
    width: 40%;
}

.suppsp-question-col {
    width: 60%;
}
.suppsp-score-col {
    width: 40%;
}

.wemwbs-question-col {
    width: 60%;
}
.wemwbs-answer-col {
    width: 40%;
}

.swemwbs-question-col {
    width: 60%;
}
.swemwbs-answer-col {
    width: 40%;
}

.wsas-question-col {
    width: 75%;
}
.wsas-answer-col {
    width: 25%;
}

.wsas-question-col {
    width: 75%;
}
.wsas-answer-col {
    width: 25%;
}

.ybocs-target-col {
    width: 50%;
}
.ybocs-detail-col {
    width: 50%;
}

.ybocs-question-col {
    width: 50%;
}
.ybocs-answer-col {
    width: 50%;
}

.ybocssc-symptom-col {
    width: 55%;
}
.ybocssc-current-col {
    width: 15%;
}
.ybocssc-past-col {
    width: 15%;
}
.ybocssc-principal-col {
    width: 15%;
}

.zbi12-question-col {
    width: 75%;
}
