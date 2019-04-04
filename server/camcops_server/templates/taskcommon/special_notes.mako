## special_notes.mako
<%page args="special_notes: List[SpecialNote], title: str, viewtype: str"/>

<%!

from camcops_server.cc_modules.cc_convert import br_html
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam

%>

<div class="specialnote">
    <b>${ title }</b><br>
    %for idx, sn in enumerate(special_notes):
        %if idx > 0:
            <br>
        %endif
        [${ (sn.note_at or "?") }, ${ (sn.get_username() or "?") }]<br>
        <b>${ sn.note | br_html }</b>
        %if viewtype == ViewArg.HTML and sn.user_may_delete_specialnote(req.user):
            <br>[<a href="${
                req.route_url(Routes.DELETE_SPECIAL_NOTE,
                              _query={ViewParam.NOTE_ID: sn.note_id}
                ) }">Delete special note</a>]
        %endif
    %endfor
</div>
