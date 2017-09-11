## base_web_form.mako
## <%page args="head_form_html: str"/>
<%inherit file="base_web.mako"/>

<%block name="extra_head_start">
    ## Extra for Deform; see
    ## https://docs.pylonsproject.org/projects/pyramid/en/latest/quick_tutorial/forms.html
    ## https://docs.pylonsproject.org/projects/deform/en/latest/widget.html#widget-requirements

    ## These aren't provided by the form's automatic resource detection:
    <script src="${request.static_url('deform:static/scripts/jquery-2.0.3.min.js')}"
            type="text/javascript"></script>
    <script src="${request.static_url('deform:static/scripts/bootstrap.min.js')}"
            type="text/javascript"></script>

    <link rel="stylesheet"
          href="${request.static_url('deform:static/css/bootstrap.min.css')}"
          type="text/css" media="screen" charset="utf-8"/>
    <link rel="stylesheet"
          href="${request.static_url('deform:static/css/form.css')}"
          type="text/css"/>

    ## Automatic things come here:
    ${head_form_html}

    ## For "${parent.BLOCKNAME()}" see http://docs.makotemplates.org/en/latest/inheritance.html#parent-namespace
</%block>

<%block name="body_tags">onload="deform.load();"</%block>

<%doc>
<%block name="body_end">
    <script>
        deform.load();
    </script>
</%block>
</%doc>

${next.body()}
