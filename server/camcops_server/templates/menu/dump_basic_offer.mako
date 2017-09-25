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
            Provides a ZIP file containing tab-separated value (TSV) files
            (usually one per task; for some tasks, more than one).
        </li>
        <li>
            Restricted to current records (i.e. ignores historical
            versions of tasks that have been edited).
        </li>
        <li>
            If there are no instances of a particular task, no TSV is returned.
        </li>
        <li>
            Incorporates patient and summary information into each row.
            Doesn’t provide BLOBs (e.g. pictures).
            NULL values are represented by blank fields and are therefore
            indistinguishable from blank strings.
            Tabs are escaped to a literal <code>\t</code>.
            Newlines are escaped to a literal <code>\n</code>.
        </li>
        <li>
            Once you’ve unzipped the resulting file, you can import TSV files
            into many other software packages. Here are some examples:
            <ul>
                <li>
                    <b>Excel:</b> Delimited / Tab.
                    <i>(Make sure no other delimiters are selected!)</i>
                </li>
                <li>
                    <b>OpenOffice:</b>
                    Character set =  UTF-8; Separated by / Tab.
                    <i>(Make sure no other delimiters are selected!)</i>
                </li>
                <li>
                    <b>R:</b>
                    <code>mydf = read.table("something.tsv", sep="\t",
                    header=TRUE, na.strings="", comment.char="")</code>
                    <i>(note that R will prepend ‘X’ to variable names starting
                    with an underscore; see <code>?make.names</code>)</i>.
                    Inspect the results with e.g. <code>colnames(mydf)</code>,
                    or in RStudio, <code>View(mydf)</code>.
                </li>
            </ul>
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

<h2>Choose TSV dump parameters</h2>

${ form }

<%include file="to_main_menu.mako"/>
