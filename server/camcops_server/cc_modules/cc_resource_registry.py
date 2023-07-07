#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_resource_registry.py

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

**Deform resource registry class, for HTML forms.**

"""


from deform.widget import ResourceRegistry


class CamcopsResourceRegistry(ResourceRegistry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_js_resources(
            "jsoneditor",
            None,
            "camcops_server.static:jsoneditor/jsoneditor.min.js",
        )

        self.set_css_resources(
            "jsoneditor",
            None,
            "camcops_server.static:jsoneditor/jsoneditor.min.css",
            "camcops_server.static:jsoneditor/jsonwidget.css",
        )
