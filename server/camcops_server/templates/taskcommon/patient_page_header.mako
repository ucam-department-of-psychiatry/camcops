## patient_page_header.mako
<%page args="patient: Patient"/>

<b>${ patient.get_surname_forename_upper() }</b> (${ patient.get_sex_verbose() }).
${ patient.get_dob_html(longform=False) }
%for idobj in patient.idnums:
    ${ idobj.short_description(request) }: ${ idobj.idnum_value }
%endfor
