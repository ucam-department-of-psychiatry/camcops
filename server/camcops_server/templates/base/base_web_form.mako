## base_web_form.mako
<%inherit file="base_web.mako"/>

<%block name="extra_head_start">
    ## Extra for Deform; see https://docs.pylonsproject.org/projects/pyramid/en/latest/quick_tutorial/forms.html
    ## tal = PHP Template Attribute Language; https://phptal.org/manual/en/split/attributelanguage.html

    <link rel="stylesheet"
          href="${request.static_url('deform:static/css/bootstrap.min.css')}"
          type="text/css" media="screen" charset="utf-8"/>
    <link rel="stylesheet"
          href="${request.static_url('deform:static/css/form.css')}"
          type="text/css"/>
    <%doc>
    <tal:block tal:repeat="reqt view.reqts['css']">
        <link rel="stylesheet" type="text/css"
              href="${request.static_url(reqt)}"/>
    </tal:block>
    </%doc>
    <script src="${request.static_url('deform:static/scripts/jquery-2.0.3.min.js')}"
            type="text/javascript"></script>
    <script src="${request.static_url('deform:static/scripts/bootstrap.min.js')}"
            type="text/javascript"></script>
    <%doc>
    <tal:block tal:repeat="reqt view.reqts['js']">
        <script src="${request.static_url(reqt)}"
                type="text/javascript"></script>
    </tal:block>
    </%doc>

    ## For "${parent.BLOCKNAME()}" see http://docs.makotemplates.org/en/latest/inheritance.html#parent-namespace
</%block>

<%block name="body_end">
    <script type="text/javascript">
        deform.load()
    </script>
</%block>
