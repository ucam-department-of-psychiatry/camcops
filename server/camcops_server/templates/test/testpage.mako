## testpage.mako
<%inherit file="base_web.mako"/>
## <%page> DOES NOT PLAY NICELY WITH INHERITANCE ## <%page args="param1='<missing>'"/>

<%!
    import pprint
    from cardinal_pythonlib.debugging import get_caller_stack_info
%>

<div>
    Hello, I'm a Mako test template!<br>

    Parameter param1 is: ${param1 | h}<br>

    Request (in str format) is:<br>
    <pre>${request | h}</pre><br>

    request.environ (WSGI environment):<br>
    <pre>${pprint.pformat(request.environ) | h}</pre>

    pageargs:<br>
    <pre>${pprint.pformat(pageargs) | h}</pre>

    dir():<br>
    <pre>${pprint.pformat(dir()) | h}</pre>

    context.__dict__:<br>
    <pre>${pprint.pformat(context.__dict__) | h}</pre>

    request.__dict__:<br>
    <pre>${pprint.pformat(request.__dict__) | h}</pre>

    callers:<br>
    <pre>${show_call_stack()}</pre>

    ## See also:
    ## http://docs.makotemplates.org/en/latest/runtime.html#all-the-built-in-names
    ## https://stackoverflow.com/questions/10689162/output-all-variables-into-mako-template
</div>

<%def name="show_call_stack()">
    %for stack_info in get_caller_stack_info():
${stack_info | h}<br>
    %endfor
</%def>
