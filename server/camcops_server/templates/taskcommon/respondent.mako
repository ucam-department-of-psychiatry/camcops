## respondent.mako
<%page args="task: Task"/>

<div class="respondent">
    <table class="taskdetail">
        <tr>
            <td style="width:50%">${_("Respondent’s name:")}</td>
            <td style="width:50%"><b>${ task.respondent_name | h }</b></td>
        </tr>
        <tr>
            <td>${_("Respondent’s relationship to patient:")}</td>
            <td><b>${ task.respondent_relationship | h }</b></td>
        </tr>
    </table>
</div>
