## clinician_comments.mako
<%page args="comment: str"/>

<div class="clinician">
    <table class="taskdetail">
        <tr>
            <td style="width:20%">${_("Clinician’s comments:")}</td>
            <td style="width:80%">
                %if comment is None:
                    <i>${_("None")}</i>
                %else:
                    <b>${ comment | h }</b>
                %endif
            </td>
        </tr>
    </table>
</div>
