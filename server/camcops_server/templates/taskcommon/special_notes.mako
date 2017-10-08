## special_notes.mako
<%page args="special_notes: List[SpecialNote], title: str"/>

<%!

from camcops_server.cc_modules.cc_convert import br_html

%>

<div class="specialnote">
    <b>${ title }</b><br>
    %for idx, sn in enumerate(special_notes):
        %if idx > 0:
            <br>
        %endif
        [${ (sn.note_at or "?") }, ${ (sn.get_username() or "?") }]<br>
        <b>${ sn.note | br_html }</b>
    %endfor
</div>
