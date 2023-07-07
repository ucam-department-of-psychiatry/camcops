## -*- coding: utf-8 -*-
<%doc>

camcops_server/templates/menu/client_api_signposting.mako

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

</%doc>

<%inherit file="base_web.mako"/>

<h1>${ _("Please install the CamCOPS app") }</h1>
<div>
    <p>
        ${ _("You’ve probably come here by mistake, having entered <b>{server_url}</b> into a web browser instead of into the CamCOPS app.").format(server_url=server_url) | n}
    </p>

    <p>
        ${ _("You need to download and install the CamCOPS app from one of the following places:") }
    </p>

    <ul>
        <li>${ _("For Android smartphones and tablets, search for CamCOPS in the Google Play Store") }</li>
        <li>${ _("For iPhones and iPads, search for CamCOPS in the Apple App Store") }</li>
        <li>${ _("For Windows and Mac computers, laptops and tablets, download CamCOPS from {github_link}").format(github_link=github_link) | n }</li>
    </ul>
</div>
