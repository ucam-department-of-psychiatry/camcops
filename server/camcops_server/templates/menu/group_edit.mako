## group_edit.mako
<%inherit file="base_web_form.mako"/>
<%!
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako"/>

<h1>${_("Edit group")} ${ group.name | h }</h1>

${ form }

<div class="footnotes">
    ${_("Policies define the minimum amount of information about a patient that must be present before records can be <i>uploaded</i> to the server or <i>finalized</i> (uploaded but also cleared off the source device).")}<br>

    ${_("Policies are specified using")}
    <ul>
        <li>${_("these logical operators:")} <code>AND</code>, <code>OR</code>,
            <code>NOT</code>;</li>

        <li>${_("these precedence operators:")} <code>(</code>, <code>)</code>;</li>

        <li>${_("these named fields:")} <code>forename</code>, <code>surname</code>,
            <code>sex</code>, <code>dob</code> (date of birth),
            <code>address</code>, <code>gp</code>,
            <code>otherdetails</code>;</li>

        <li>${_("a specific ID number using")} “idnum<i>n</i>”;
            ${_("for example, <code>idnum3</code> refers to ID number 3 as defined by the server’s")}
            <a href="${ req.route_url(Routes.VIEW_SERVER_INFO) }">${_("ID numbers")}</a>;</li>

        <li>${_("the token <code>anyidnum</code> as a shorthand to mean “at least one of the server’s ID numbers is present”;")}</li>

        <li>${_("the token <code>otheridnum</code> as a shorthand to mean “at least one of the server’s ID numbers that is not named in the policy”;")}</li>
    </ul>

    ${_("The policies are case-insensitive.")}<br>

    ${_("Examples:")}
    <ul>
        <li>
            ${_("A liaison psychiatry department might operate in a mental health environment using idnum1, and an acute hospital environment using idnum2. It might want to allow uploads using either ID number, for quick access to the CamCOPS server version from the acute hospital environment, but require idnum1 to be present before the data can be finalized. It also wants full identification with forename, surname, DOB, and sex. It could use an upload policy of <code>forename AND surname AND dob AND sex AND (idnum1 OR idnum2)</code> and a finalize policy of <code>forename AND surname AND dob AND sex AND idnum1</code>.")}
        </li>
        <li>
            ${_("In contrast, a research environment might want no patient-identifying information, and a single research pseudonym for that study. It might use an upload and a finalize policy that are both <code>sex AND idnum1</code>.")}
        </li>
    </ul>
</div>

<%include file="to_main_menu.mako"/>
