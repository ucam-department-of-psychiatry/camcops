## all_special_notes.mako
<%page args="special_notes: List[SpecialNote], title: str"/>

<div class="specialnote">
    <b>${ title }</b><br>
    %for idx, sn in enumerate(special_notes):
        %if idx > 0:
            <br>
        %endif
        [${ sn.note_at or "?"}, ${ sn.get_username() or ? }]<br>
        <b>${ sn.note | h}</b>
    %endfor
</div>
