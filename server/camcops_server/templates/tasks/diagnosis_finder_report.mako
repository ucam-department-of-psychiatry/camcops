## diagnosis_finder_report.mako
<%inherit file="report.mako"/>

<%block name="additional_report_above_results">
    <h2>${_("Parameters:")}</h2>
    <div>
        ${_("Which ID number type:")} ${idnum_desc}.<br>
        ${_("Inclusion diagnoses:")} ${inclusion_dx}.<br>
        ${_("Exclusion diagnoses:")} ${exclusion_dx}.<br>
        ${_("Minimum age:")} ${age_minimum}.<br>
        ${_("Maximum age:")} ${age_maximum}.
    </div>
    <h2>${_("Results:")}</h2>
</%block>

<%block name="additional_report_below_menu">
    <h2>SQL:</h2>
    <div>
        <code>${sql}</code>
    </div>
</%block>