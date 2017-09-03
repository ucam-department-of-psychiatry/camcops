## hl7_run_view.mako
<%inherit file="base_web.mako"/>

<%include file="db_user_info.mako"/>

<h1>Individual HL7 run</h1>

<table>
    <tr>
        <th>Run ID</th>
        <td>${ hl7run.run_id }</td>
    </tr>
    <tr>
        <th>Time run was started (UTC)</th>
        <td>${ hl7run.start_at_utc }</td>
    </tr>
    <tr>
        <th>Time run was finished (UTC)</th>
        <td>${ hl7run.finish_at_utc }</td>
    </tr>
    <tr>
        <th>Recipient definition name (determines uniqueness)</th>
        <td>${ hl7run.recipient | h }</td>
    </tr>
    ## ========================================================================
    <tr>
        <td colspan="2">
            <i>Common to all ways of sending:</i>
        </td>
    </tr>
    ## ------------------------------------------------------------------------
    <tr>
        <th>Recipient type (e.g. hl7, file)</th>
        <td>${ hl7run.type | h }</td>
    </tr>
    <tr>
        <th>Which ID number was used as the primary ID?</th>
        <td>${ hl7run.primary_idnum }</td>
    </tr>
    <tr>
        <th>Must the primary ID number be mandatory in the relevant policy?</th>
        <td>${ hl7run.require_idnum_mandatory }</td>
    </tr>
    <tr>
        <th>Start date for tasks (UTC)</th>
        <td>${ hl7run.start_date }</td>
    </tr>
    <tr>
        <th>End date for tasks (UTC)</th>
        <td>${ hl7run.end_date }</td>
    </tr>
    <tr>
        <th>Send only finalized tasks</th>
        <td>${ hl7run.finalized_only }</td>
    </tr>
    <tr>
        <th>Format that task information was sent in</th>
        <td>${ hl7run.task_format | h }</td>
    </tr>
    <tr>
        <th>Include field comments in XML output?th>
        <td>${ hl7run.xml_field_comments }</td>
    </tr>
    ## ========================================================================
    <tr>
        <td colspan="2">
            <i>For HL7 method:</i>
        </td>
    </tr>
    ## ------------------------------------------------------------------------
    <tr>
        <th>(HL7) Destination host name/IP address</th>
        <td>${ hl7run.host | h }</td>
    </tr>
    <tr>
        <th>(HL7) Destination port number</th>
        <td>${ hl7run.port }</td>
    </tr>
    <tr>
        <th>(HL7) Divert to file with this name</th>
        <td>${ hl7run.divert_to_file }</td>
    </tr>
    <tr>
        <th>(HL7) Treat messages diverted to file as sent</th>
        <td>${ hl7run.treat_diverted_as_sent }</td>
    </tr>
    ## ========================================================================
    <tr>
        <td colspan="2">
            <i>For file method:</i>
        </td>
    </tr>
    ## ------------------------------------------------------------------------
    <tr>
        <th>(FILE) Include anonymous tasks</th>
        <td>${ hl7run.include_anonymous }</td>
    </tr>
    <tr>
        <th>(FILE) Overwrite existing files</th>
        <td>${ hl7run.overwrite_files }</td>
    </tr>
    <tr>
        <th>(FILE) Export RiO metadata file along with main file?</th>
        <td>${ hl7run.rio_metadata }</td>
    </tr>
    <tr>
        <th>(FILE) RiO metadata: which ID number is the RiO ID?</th>
        <td>${ hl7run.rio_idnum }</td>
    </tr>
    <tr>
        <th>(FILE) RiO metadata: name of automatic upload user</th>
        <td>${ hl7run.rio_uploading_user | h }</td>
    </tr>
    <tr>
        <th>(FILE) RiO metadata: document type for RiO</th>
        <td>${ hl7run.rio_document_type | h }</td>
    </tr>
    <tr>
        <th>(FILE) Command/script to run after file export</th>
        <td>${ hl7run.script_after_file_export | h }</td>
    </tr>
    ## ========================================================================
    <tr>
        <td colspan="2">
            <i>More, beyond the recipient definition:</i>
        </td>
    </tr>
    ## ------------------------------------------------------------------------
    <tr>
        <th>Return code from the script_after_file_export script</th>
        <td>${ hl7run.script_retcode }</td>
    </tr>
    <tr>
        <th>stdout from the script_after_file_export script</th>
        <td>${ hl7run.script_stdout | h }</td>
    </tr>
    <tr>
        <th>stderr from the script_after_file_export script</th>
        <td>${ hl7run.script_stderr | h }</td>
    </tr>
</table>

<%include file="to_main_menu.mako"/>
