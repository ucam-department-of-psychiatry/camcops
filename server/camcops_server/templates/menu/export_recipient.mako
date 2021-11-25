## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/export_recipient.mako

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

</%doc>

<%inherit file="base_web.mako"/>

<%!
from markupsafe import escape
from camcops_server.cc_modules.cc_pyramid import Icons, Routes, ViewArg, ViewParam
from camcops_server.cc_modules.cc_exportrecipientinfo import ExportTransmissionMethod
%>

<%include file="db_user_info.mako"/>

<h1>
    ${ req.icon_text(
        icon=Icons.EXPORT_RECIPIENT,
        text=_("Export recipient")
    ) | n }
</h1>

<h2>${ _("About the recipient") }</h2>
<table>
    <colgroup>
        <col style="width:50%">
        <col style="width:50%">
    </colgroup>
    <tbody>
        <tr>
            <th>Recipient ID</th>
            <td>${ recipient.id }</td>
        </tr>
        <tr>
            <th>Name</th>
            <td>${ recipient.recipient_name or "" }</td>
        </tr>
        <tr>
            <th>Current?</th>
            <td>${ recipient.current }</td>
        </tr>
    </tbody>
</table>

<h2>${ _("How to export") }</h2>
<table>
    <colgroup>
        <col style="width:50%">
        <col style="width:50%">
    </colgroup>
    <tbody>
        <tr>
            <th>How: Transmission method</th>
            <td>${ recipient.transmission_method or "" }</td>
        </tr>
        <tr>
            <th>How: Push?</th>
            <td>${ recipient.push }</td>
        </tr>
        <tr>
            <th>How: Task format</th>
            <td>${ recipient.task_format or "" }</td>
        </tr>
        <tr>
            <th>How: Include fields comments in XML?</th>
            <td>${ recipient.xml_field_comments }</td>
        </tr>
    </tbody>
</table>

<h2>${ _("What to export") }</h2>
<table>
    <colgroup>
        <col style="width:50%">
        <col style="width:50%">
    </colgroup>
    <tbody>
        <tr>
            <th>What: All groups?</th>
            <td>${ recipient.all_groups }</td>
        </tr>
        <tr>
            <th>What: Groups</th>
            <td>${ ", ".join(str(gid) for gid in recipient.group_ids) }</td>
        </tr>
        <tr>
            <th>What: Start date/time (UTC)</th>
            <td>${ recipient.start_datetime_utc }</td>
        </tr>
        <tr>
            <th>What: End date/time (UTC)</th>
            <td>${ recipient.end_datetime_utc }</td>
        </tr>
        <tr>
            <th>What: Finalized tasks only?</th>
            <td>${ recipient.finalized_only }</td>
        </tr>
        <tr>
            <th>What: Include anonymous tasks?</th>
            <td>${ recipient.include_anonymous }</td>
        </tr>
        <tr>
            <th>What: Primary ID number type</th>
            <td>${ recipient.primary_idnum }</td>
        </tr>
        <tr>
            <th>What: Require primary ID number to be mandatory?</th>
            <td>${ recipient.require_idnum_mandatory }</td>
        </tr>
    </tbody>
</table>

%if recipient.transmission_method == ExportTransmissionMethod.DATABASE:
    <h2>${ _("Database export options") }</h2>
    <table>
        <colgroup>
            <col style="width:50%">
            <col style="width:50%">
        </colgroup>
        <tbody>
            <tr>
                <th>Database: URL</th>
                <td>${ recipient.db_url_obscuring_password or "" }</td>
            </tr>
            <tr>
                <th>Database: echo?</th>
                <td>${ recipient.db_echo }</td>
            </tr>
            <tr>
                <th>Database: include BLOBs?</th>
                <td>${ recipient.db_include_blobs }</td>
            </tr>
            <tr>
                <th>Database: add summaries?</th>
                <td>${ recipient.db_add_summaries }</td>
            </tr>
            <tr>
                <th>Database: patient ID per row?</th>
                <td>${ recipient.db_patient_id_per_row }</td>
            </tr>
        </tbody>
    </table>
%endif

%if recipient.transmission_method == ExportTransmissionMethod.EMAIL:
    <h2>${ _("E-mail export options") }</h2>
    <table>
        <colgroup>
            <col style="width:50%">
            <col style="width:50%">
        </colgroup>
        <tbody>
            <tr>
                <th>E-mail: host</th>
                <td>${ recipient.email_host or "" }</td>
            </tr>
            <tr>
                <th>E-mail: port</th>
                <td>${ recipient.email_port }</td>
            </tr>
            <tr>
                <th>E-mail: use TLS?</th>
                <td>${ recipient.email_use_tls }</td>
            </tr>
            <tr>
                <th>E-mail: from</th>
                <td>${ recipient.email_from or "" }</td>
            </tr>
            <tr>
                <th>E-mail: sender</th>
                <td>${ recipient.email_sender or "" }</td>
            </tr>
            <tr>
                <th>E-mail: reply-to</th>
                <td>${ recipient.email_reply_to or "" }</td>
            </tr>
            <tr>
                <th>E-mail: to</th>
                <td>${ recipient.email_to or "" }</td>
            </tr>
            <tr>
                <th>E-mail: CC</th>
                <td>${ recipient.email_cc or "" }</td>
            </tr>
            <tr>
                <th>E-mail: BCC</th>
                <td>${ recipient.email_bcc or "" }</td>
            </tr>
            <tr>
                <th>E-mail: patient spec</th>
                <td>${ recipient.email_patient_spec or "" }</td>
            </tr>
            <tr>
                <th>E-mail: patient spec if anonymous</th>
                <td>${ recipient.email_patient_spec_if_anonymous or "" }</td>
            </tr>
            <tr>
                <th>E-mail: subject</th>
                <td>${ recipient.email_subject or "" }</td>
            </tr>
            <tr>
                <th>E-mail: treat body as HTML?</th>
                <td>${ recipient.email_body_as_html }</td>
            </tr>
            <tr>
                <th>E-mail: body</th>
                <td>
                    %if recipient.email_body:
                        <pre>${ recipient.email_body  }</pre>
                    %endif
                </td>
            </tr>
            <tr>
                <th>E-mail: keep message?</th>
                <td>${ recipient.email_keep_message }</td>
            </tr>
        </tbody>
    </table>
%endif

%if recipient.transmission_method == ExportTransmissionMethod.FHIR:
    <h2>${ _("FHIR export options") }</h2>
    <table>
        <colgroup>
            <col style="width:50%">
            <col style="width:50%">
        </colgroup>
        <tbody>
            <tr>
                <th>FHIR API URL</th>
                <td>
                    %if recipient.fhir_api_url:
                        ${ req.icon_text(
                                icon=Icons.INFO_EXTERNAL,
                                url=recipient.fhir_api_url,
                                text=recipient.fhir_api_url
                        ) | n }
                    %endif
                </td>
            </tr>
            <tr>
                <th>FHIR app ID (of CamCOPS)</th>
                <td>${ recipient.fhir_app_id or "" }</td>
            </tr>
            <tr>
                <th>Server supports full concurrency?</th>
                <td>${ recipient.fhir_concurrent }</td>
            </tr>
        </tbody>
    </table>
%endif

%if recipient.transmission_method == ExportTransmissionMethod.FILE:
    <h2>${ _("File export options") }</h2>
    <table>
        <colgroup>
            <col style="width:50%">
            <col style="width:50%">
        </colgroup>
        <tbody>
            <tr>
                <th>File: patient spec</th>
                <td>${ recipient.file_patient_spec or "" }</td>
            </tr>
            <tr>
                <th>File: patient spec if anonymous</th>
                <td>${ recipient.file_patient_spec_if_anonymous or "" }</td>
            </tr>
            <tr>
                <th>File: filename spec</th>
                <td>${ recipient.file_filename_spec or "" }</td>
            </tr>
            <tr>
                <th>File: make directory?</th>
                <td>${ recipient.file_make_directory }</td>
            </tr>
            <tr>
                <th>File: overwrite files?</th>
                <td>${ recipient.file_overwrite_files }</td>
            </tr>
            <tr>
                <th>File: export RiO metadata?</th>
                <td>${ recipient.file_export_rio_metadata }</td>
            </tr>
            <tr>
                <th>File: script to run after export</th>
                <td>${ recipient.file_script_after_export or "" }</td>
            </tr>
            <tr>
                <th>File: RiO metadata: which ID number is the RiO ID?</th>
                <td>${ recipient.rio_idnum }</td>
            </tr>
            <tr>
                <th>File: RiO metadata: name of automatic upload user</th>
                <td>${ recipient.rio_uploading_user or "" }</td>
            </tr>
            <tr>
                <th>File: RiO metadata: document type for RiO</th>
                <td>${ recipient.rio_document_type or "" }</td>
            </tr>
        </tbody>
    </table>
%endif

%if recipient.transmission_method == ExportTransmissionMethod.HL7:
    <h2>${ _("HL7 export options") }</h2>
    <table>
        <colgroup>
            <col style="width:50%">
            <col style="width:50%">
        </colgroup>
        <tbody>
            <tr>
                <th>HL7: host</th>
                <td>${ recipient.hl7_host or "" }</td>
            </tr>
            <tr>
                <th>HL7: port</th>
                <td>${ recipient.hl7_port }</td>
            </tr>
            <tr>
                <th>HL7: ping first?</th>
                <td>${ recipient.hl7_ping_first }</td>
            </tr>
            <tr>
                <th>HL7: network timeout (ms)</th>
                <td>${ recipient.hl7_network_timeout_ms }</td>
            </tr>
            <tr>
                <th>HL7: keep messages?</th>
                <td>${ recipient.hl7_keep_message }</td>
            </tr>
            <tr>
                <th>HL7: keep reply?</th>
                <td>${ recipient.hl7_keep_reply }</td>
            </tr>
            <tr>
                <th>HL7 (DEBUG): divert to file?</th>
                <td>${ recipient.hl7_debug_divert_to_file }</td>
            </tr>
            <tr>
                <th>HL7 (DEBUG): treat diverted as sent?</th>
                <td>${ recipient.hl7_debug_treat_diverted_as_sent }</td>
            </tr>
        </tbody>
    </table>
%endif

%if recipient.transmission_method == ExportTransmissionMethod.REDCAP:
    <h2>${ _("REDCap export options") }</h2>
    <table>
        <colgroup>
            <col style="width:50%">
            <col style="width:50%">
        </colgroup>
        <tbody>
            <tr>
                <th>REDCap API URL</th>
                <td>
                    %if recipient.redcap_api_url:
                        ${ req.icon_text(
                                icon=Icons.INFO_EXTERNAL,
                                url=recipient.redcap_api_url,
                                text=recipient.redcap_api_url
                        ) | n }
                    %endif
                </td>
            </tr>
            <tr>
                <th>REDCap field map filename</th>
                <td>${ recipient.redcap_fieldmap_filename or "" }</td>
            </tr>
        </tbody>
    </table>
%endif

<%include file="to_offer_exported_task_list.mako"/>
<%include file="to_main_menu.mako"/>
