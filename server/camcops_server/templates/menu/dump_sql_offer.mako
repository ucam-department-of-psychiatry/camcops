## dump_sql_offer.mako
<%inherit file="base_web_form.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>Research data dump in SQL format</h1>

<h2>Explanation</h2>
<div>
    <ul>
        <li>This research dump takes some subset of data to which you have
            access, and builds a new database from it. That database is served
            to you in SQLite format; you can choose binary or SQL format.</li>
        <li>The records are restricted to ‘current’ tasks, and some irrelevant,
            administrative, and security-related columns are removed.</li>
        <li>Summary information (such as total scores) is automatically added,
            for convenience.</li>
        <li>Foreign key constraints are removed.</li>
        <li>You can load and explore the binary database like this:
            <pre>$ sqlite3 CamCOPS_dump_SOME_DATE.sqlite3
sqlite> .tables
sqlite> pragma table_info('patient');
sqlite> select * from patient;</pre></li>
        <li>The SQLite format is widely supported; see, for example, the
            <a href="https://cran.r-project.org/web/packages/RSQLite/index.html">RSQLite</a>
            package for <a href="https://www.r-project.org/">R</a>.</li>
    </ul>
</div>

<h2>Choose SQL dump parameters</h2>

${ form }

<%include file="to_main_menu.mako"/>
