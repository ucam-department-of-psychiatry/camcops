## patient.mako
<%page args="patient: Patient, include_special_notes: bool = True"/>

<div class="patient">
    <b>${ patient.get_surname_forename_upper() | h}</b>
        (${ patient.get_sex_verbose() })
        ${ patient.get_dob_html(longform=True)}
    ## TODO: remove HTML from Python further?
    %for pt_id_num in patient.idnums:
        <!-- ID${ pt_id_num.which_idnum } -->
        <br>${ pt_id_num.description(req) | h }: <b>${ pt_id_num.idnum_value }</b>
    %endfor
    %if patient.other:
        <br>Other details: <b>${ patient.other | h }</b>
    %endif
    %if patient.address:
        <br>Address: <b>${ patient.address | h }</b>
    %endif
    %if patient.gp:
        <br>GP: <b>${ patient.gp | h }</b>
    %endif
</div>

%if include_special_notes and patient.special_notes:
    <%include file="special_notes.mako" args="special_notes=patient.special_notes, title='PATIENT SPECIAL NOTES'"/>
%endif
