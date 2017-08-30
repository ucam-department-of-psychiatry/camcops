#!/usr/bin/env python
# camcops_server/cc_modules/forms.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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
"""

from typing import List

from colander import MappingSchema, SchemaNode, String
from deform.form import Button, Form
from deform.widget import HiddenWidget, PasswordWidget

from .cc_constants import PARAM


# =============================================================================
# Debugging form errors (which can be hidden in their depths)
# =============================================================================

def get_form_errors(form: Form) -> str:
    errors = [form.error]  # type: List[str]
    for child in form.children:
        errors.append(child.error)
    return "; ".join(repr(e) for e in errors)


# =============================================================================
# Login
# =============================================================================

class LoginSchema(MappingSchema):
    username = SchemaNode(  # name must match PARAM.USERNAME
        String(),
        description="Enter the user name",
    )
    password = SchemaNode(  # name must match PARAM.PASSWORD
        String(),
        widget=PasswordWidget(),
        description="Enter the password",
    )
    redirect_url = SchemaNode(  # name must match PARAM.REDIRECT_URL
        String(),
        missing="",
        widget=HiddenWidget(),
    )


class LoginForm(Form):
    def __init__(self, autocomplete_password: bool = True) -> None:
        schema = LoginSchema()
        super().__init__(
            schema,
            buttons=('submit',),
            autocomplete=autocomplete_password
        )
        # Suboptimal: autocomplete_password is not applied to the password
        # widget, just to the form; see
        # http://stackoverflow.com/questions/2530
        # Note that e.g. Chrome may ignore this.


# =============================================================================
# Offer/agree terms
# =============================================================================

class OfferTermsSchema(MappingSchema):
    pass


class OfferTermsForm(Form):
    def __init__(self, agree_button_text: str) -> None:
        schema = OfferTermsSchema()
        super().__init__(
            schema,
            buttons=[Button(name=PARAM.AGREE, title=agree_button_text)]
        )
