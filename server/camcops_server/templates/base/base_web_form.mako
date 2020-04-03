## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/base/base_web_form.mako

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================

</%doc>

## <%page args="head_form_html: str"/>
<%inherit file="base_web.mako"/>

<%block name="extra_head_start">
    ${parent.extra_head_start()}
    ## Extra for Deform; see
    ## https://docs.pylonsproject.org/projects/pyramid/en/latest/quick_tutorial/forms.html
    ## https://docs.pylonsproject.org/projects/deform/en/latest/widget.html#widget-requirements

    ## These aren't provided by the form's automatic resource detection:
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
