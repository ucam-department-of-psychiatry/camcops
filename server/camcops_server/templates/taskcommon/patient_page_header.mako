## patient_page_header.mako
<%page args="patient: Patient"/>

<b>${ task.patient.get_surname_forename_upper() }</b> (${ task.patient.get_sex_verbose() }).
${ task.patient.get_dob_html(longform=False) }
%for idobj in task.patient.idnums:
    ${ idobj.short_description(request) }: ${ idobj.idnum_value }
%endfor
