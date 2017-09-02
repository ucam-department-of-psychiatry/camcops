## base_web_form.mako
<%inherit file="base_web.mako"/>

<%block name="extra_head_start">
    ## Extra for Deform; see https://docs.pylonsproject.org/projects/pyramid/en/latest/quick_tutorial/forms.html
    ## ... tal = PHP Template Attribute Language; https://phptal.org/manual/en/split/attributelanguage.html
    ## ... the tal blocks were junk under Mako
    ## https://github.com/zefciu/pyramid-concepts/blob/master/newssite/newssite/templates/render_form.mako

    <script src="${request.static_url('deform:static/scripts/jquery-2.0.3.min.js')}"
            type="text/javascript"></script>
    <script src="${request.static_url('deform:static/scripts/bootstrap.min.js')}"
            type="text/javascript"></script>
    <script src="${request.static_url('deform:static/scripts/deform.js')}"
            type="text/javascript"></script>
    ## ... potentially more needed

    <link rel="stylesheet"
          href="${request.static_url('deform:static/css/bootstrap.min.css')}"
          type="text/css" media="screen" charset="utf-8"/>
    <link rel="stylesheet"
          href="${request.static_url('deform:static/css/form.css')}"
          type="text/css"/>

    ## For "${parent.BLOCKNAME()}" see http://docs.makotemplates.org/en/latest/inheritance.html#parent-namespace
</%block>

<%block name="body_end">
    <script>
        deform.load();
    </script>
</%block>
