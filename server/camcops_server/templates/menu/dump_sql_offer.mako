## dump_sql_offer.mako
<%inherit file="base_web_form.mako"/>

<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>${_("Research data dump in SQL format")}</h1>

<h2>${_("Explanation")}</h2>
<div>
    <ul>
        <li>
            ${_("This research dump takes some subset of data to which you have access, and builds a new database from it. That database is served to you in SQLite format; you can choose binary or SQL format.")}
        </li>
        <li>
            ${_("The records are restricted to ‘current’ tasks, and some irrelevant, administrative, and security-related columns are removed.")}
        </li>
        <li>
            ${_("Summary information (such as total scores) is automatically added, for convenience.")}
        </li>
        <li>${_("Foreign key constraints are removed.")}</li>
        <li>${_("You can load and explore the binary database like this:")}
            <pre>$ sqlite3 CamCOPS_dump_SOME_DATE.sqlite3
sqlite> .tables
sqlite> pragma table_info('patient');
sqlite> select * from patient;</pre></li>
        <li>${_("The SQLite format is widely supported; see, for example, the")}
            <a href="https://cran.r-project.org/web/packages/RSQLite/index.html">RSQLite</a>
            ${_("package for")} <a href="https://www.r-project.org/">R</a>.</li>
    </ul>
</div>

<h2>${_("Choose SQL dump parameters")}</h2>

${ form }

<%include file="to_main_menu.mako"/>
