## testpage.mako
<%inherit file="base_web.mako"/>

<div>
    Hello, I'm a Mako test template!<br>
    Parameter param1 is: ${param1}<br>
    Parameter request is:<br>
    <pre>${request}</pre><br>
    All parameters from context.__dict__:<br>
    <pre>${context.__dict__}</pre>
    ## See also:
    ## http://docs.makotemplates.org/en/latest/runtime.html#all-the-built-in-names
    ## https://stackoverflow.com/questions/10689162/output-all-variables-into-mako-template
</div>
