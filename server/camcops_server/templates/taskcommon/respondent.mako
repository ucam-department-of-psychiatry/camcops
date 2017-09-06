## respondent.mako
<%page args="task: Task"/>

<div class="respondent">
    <table class="taskdetail">
        <tr>
            <td width="50%">Respondent’s name:</td>
            <td width="50%"><b>${ task.respondent_name | h }</b></td>
        </tr>
        <tr>
            <td>Respondent’s relationship to patient:</td>
            <td><b>${ task.respondent_relationship | h }</b></td>
        </tr>
    </table>
</div>
