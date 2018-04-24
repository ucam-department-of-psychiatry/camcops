## diagnosis_finder_report.mako
<%inherit file="report.mako"/>

<%block name="additional_report_above_results">
    <h2>Parameters:</h2>
    <div>
        Which ID number type: ${idnum_desc}.<br>
        Inclusion diagnoses: ${inclusion_dx}.<br>
        Exclusion diagnoses: ${exclusion_dx}.<br>
        Minimum age: ${age_minimum}.<br>
        Maximum age: ${age_maximum}.
    </div>
    <h2>Results:</h2>
</%block>

<%block name="additional_report_below_menu">
    <h2>SQL:</h2>
    <div>
        <code>${sql}</code>
    </div>
</%block>