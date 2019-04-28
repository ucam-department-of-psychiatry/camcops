## dump_basic_offer.mako
<%inherit file="base_web_form.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>Basic research data dump</h1>

<h2>Explanation</h2>
<div>
    <ul>
        <li>
            Provides a spreadsheet-style download (usually one sheet per task;
            for some tasks, more than one).
        </li>
        <li>
            Incorporates patient and summary information into each row.
            Doesn’t provide BLOBs (e.g. pictures).
        </li>
        <li>
            If there are no instances of a particular task, no sheet is returned.
        </li>
        <li>
            Restricted to current records (i.e. ignores historical
            versions of tasks that have been edited).
        </li>
        <li>
            For TSV, NULL values are represented by blank fields and are
            therefore indistinguishable from blank strings, and the Excel
            dialect of TSV is used. If you want to read TSV files into R, try
            <code>mydf = read.table("something.tsv", sep="\t", header=TRUE,
            na.strings="", comment.char="")</code> (note that R will prepend
            ‘X’ to variable names starting with an underscore; see
            <code>?make.names</code>). Inspect the results with e.g.
            <code>colnames(mydf)</code>, or in RStudio,
            <code>View(mydf)</code>.
        </li>
        <li>
            For more advanced features, use the
            <a href="${ request.route_url(Routes.OFFER_SQL_DUMP) }">SQL dump</a>
            to get the raw data.
        </li>
        <li>
            <b>For explanations of each field (field comments),</b> see each
            task’s XML view or
            <a href="${ request.route_url(Routes.VIEW_DDL) }">inspect the table definitions</a>.
        </li>
    </ul>
</div>

<h2>Choose basic dump settings</h2>

${ form }

<%include file="to_main_menu.mako"/>
