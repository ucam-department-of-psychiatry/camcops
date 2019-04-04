## patient.mako
<%page args="patient: Patient, viewtype: str, include_special_notes: bool = True"/>

<div class="patient">
    <b>${ patient.get_surname_forename_upper() | h}</b>
        (${ patient.get_sex_verbose() })
        ${ patient.get_dob_html(longform=True)}
    %for pt_id_num in patient.idnums:
        <!-- ID${ pt_id_num.which_idnum } -->
        <br>${ pt_id_num.description(req) | h }: <b>${ pt_id_num.idnum_value }</b>
        %if not pt_id_num.is_fully_valid(req):
            <span class="invalid_id_number_foreground">[${ pt_id_num.why_invalid(req) | h }]</span>
        %endif
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
    <%include file="special_notes.mako" args="special_notes=patient.special_notes, title='PATIENT SPECIAL NOTES', viewtype=viewtype"/>
%endif
