## task_contents_invalid.mako
<%page args="task: Task"/>

<div class="warning">
    <b>WARNING. Invalid values.</b>
    %for idx, explanation in enumerate(task.field_contents_invalid_because()):
        %if idx > 0:
            <br>
        %endif
        ${ explanation | h }
    %endfor
</div>
