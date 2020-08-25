"""
camcops_server/cc_modules/cc_view_classes.py

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

Django-style class-based views for Pyramid.
Adapted from views/generic/base.py and views/generic/edit.py

Django has the following licence:

--8<---------------------------------------------------------------------------

Copyright (c) Django Software Foundation and individual contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    3. Neither the name of Django nor the names of its contributors may be used
       to endorse or promote products derived from this software without
       specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

--8<---------------------------------------------------------------------------

Custom views typically inherit from CreateView, DeleteView or UpdateView.

A Pyramid view function with named route should create a view of the custom
class, passing in the request and call its dispatch() method

To provide a custom view class to create a new object in the database:

* Inherit from CreateView
* Set object_class property
* Set form_class property
* Set template_name property
* Set extra_context property for any extra parameters to pass to the template
* Set success_url or override get_success_url() to be the redirect on
  successful creation
* For simple views, set model_form_dict property to be a mapping of
  object properties to form parameters
* Override save_object to do anything more than a simple record save
  (saving related objects for example)


To provide a custom view class to delete an object from the database:

* Inherit from DeleteView
* Set object_class property
* Set form_class property
* Set template_name property
* Set extra_context property for any extra parameters to pass to the template
* Set success_url or override get_success_url() to be the redirect on
  successful creation
* Set pk_param property to be the name of the parameter in the request
  that holds the unique/primary key of the object to be deleted
* Set server_pk_name property to be the name of the property on the object that
  is the unique/primary key
* Override get_object() if the object cannot be retrieved with the above
* Override delete() to do anything more than a simple record delete, for example
  to delete dependant objects


To provide a custom view class to update an object in the database:

* Inherit from UpdateView
* Set object_class property
* Set form_class property
* Set template_name property
* Set extra_context property for any extra parameters to pass to the template
* Set success_url or override get_success_url() to be the redirect on
  successful creation
* Set pk_param property to be the name of the parameter in the request
  that holds the unique/primary key of the object to be deleted
* Set server_pk_name property to be the name of the property on the object that
  is the unique/primary key
* Override get_object() if the object cannot be retrieved with the above
* For simple views, set model_form_dict property to be a mapping of
  object properties to form parameters
* Override save_object to do anything more than a simple record save
  (saving related objects for example)


You can use mixins for settings common to multiple views.

Some examples are in webview.py
"""

from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPFound,
    HTTPMethodNotAllowed,
)
from pyramid.renderers import render_to_response
from pyramid.response import Response

import logging
from typing import Any, Dict, List, NoReturn, Optional, Type, TYPE_CHECKING

from cardinal_pythonlib.deform_utils import get_head_form_html
from cardinal_pythonlib.logs import BraceStyleAdapter
from deform.exception import ValidationFailure

from camcops_server.cc_modules.cc_exception import raise_runtime_error
from camcops_server.cc_modules.cc_pyramid import FormAction
from camcops_server.cc_modules.cc_resource_registry import (
    CamcopsResourceRegistry
)

if TYPE_CHECKING:
    from deform.form import Form
    from camcops_server.cc_modules.cc_request import CamcopsRequest
    from camcops_server.cc_modules.cc_sqlalchemy import Base

log = BraceStyleAdapter(logging.getLogger(__name__))


class ContextMixin:
    """
    A default context mixin that passes the keyword arguments received by
    get_context_data() as the template context.
    """
    extra_context = None

    def get_context_data(self, **kwargs: Any) -> Any:
        kwargs.setdefault("view", self)
        if self.extra_context is not None:
            kwargs.update(self.extra_context)
        return kwargs


class View:
    """
    Simple parent class for all views
    """

    http_method_names = ["get", "post"]

    def __init__(self, request: "CamcopsRequest") -> None:
        self.request = request

    def dispatch(self) -> Any:
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        handler = self.http_method_not_allowed

        if self.request.method.lower() in self.http_method_names:
            handler = getattr(self, self.request.method.lower(),
                              handler)
        return handler()

    def http_method_not_allowed(self) -> NoReturn:
        log.warning(
            "Method Not Allowed (%s): %s",
            self.request.method, self.request.path,
            extra={"status_code": 405, "request": self.request}
        )
        raise HTTPMethodNotAllowed(
            detail=f"Allowed methods: {self._allowed_methods}"
        )

    def _allowed_methods(self) -> List[str]:
        return [m.upper() for m in self.http_method_names if hasattr(self, m)]


class TemplateResponseMixin:
    """A mixin that can be used to render a template."""
    request: "CamcopsRequest"
    template_name = None

    def render_to_response(self, context: Dict) -> Response:
        if self.template_name is None:
            raise_runtime_error(f"No template_name set for {self.__class__}.")

        return render_to_response(
            self.template_name,
            context,
            request=self.request
        )


class FormMixin(ContextMixin):
    """Provide a way to show and handle a form in a request."""
    cancel_url = None
    form_class = None
    success_url = None
    _form = None
    _error = None

    request: "CamcopsRequest"

    def get_form_class(self) -> Optional[Type["Form"]]:
        """Return the form class to use."""
        return self.form_class

    def get_form(self) -> "Form":
        """Return an instance of the form to be used in this view."""

        if self._form is None:
            form_class = self.get_form_class()
            if not form_class:
                raise_runtime_error("Your view must provide a form_class.")

            registry = CamcopsResourceRegistry()

            assert form_class is not None  # type checker

            self._form = form_class(request=self.request,
                                    resource_registry=registry)

        return self._form

    def get_cancel_url(self) -> str:
        """Return the URL to redirect to when cancelling a form."""
        if not self.cancel_url:
            return self.get_success_url()
        return str(self.cancel_url)  # cancel_url may be lazy

    def get_success_url(self) -> str:
        """Return the URL to redirect to after processing a valid form."""
        if not self.success_url:
            raise_runtime_error("Your view must provide a success_url.")
        return str(self.success_url)  # success_url may be lazy

    def form_valid(self, form: "Form", appstruct: Dict[str, Any]) -> None:
        """If the form is valid, redirect to the supplied URL."""
        raise HTTPFound(self.get_success_url())

    def form_invalid(self, validation_error: ValidationFailure) -> Any:
        """If the form is invalid, save the invalid form."""
        self._error = validation_error

        return self.render_to_response(
            self.get_context_data()
        )

    def get_context_data(self, **kwargs: Any) -> Any:
        """Insert the rendered form into the context dict."""

        form = self.get_form()
        kwargs["form"] = self.get_rendered_form()
        kwargs["head_form_html"] = get_head_form_html(
            self.request, [form]
        )

        return super().get_context_data(**kwargs)

    def get_rendered_form(self) -> str:
        if self._error is not None:
            return self._error.render()

        form = self.get_form()
        appstruct = self.get_form_values()

        return form.render(appstruct)


class SingleObjectMixin(ContextMixin):
    object: Optional["Base"]
    object_class: Optional[Type["Base"]]
    pk_param: str
    request: "CamcopsRequest"
    server_pk_name: str

    def get_context_data(self, **kwargs: Any) -> Any:
        """Insert the single object into the context dict."""
        context = {}
        if self.object:
            context["object"] = self.object

        context.update(kwargs)

        return super().get_context_data(**context)

    def get_object(self) -> "Base":
        pk_value = self.request.get_int_param(self.pk_param)

        if self.object_class is None:
            raise_runtime_error("Your view must provide an object_class.")

        pk_property = getattr(self.object_class, self.server_pk_name)

        obj = self.request.dbsession.query(self.object_class).filter(
            pk_property == pk_value
        ).one_or_none()

        if obj is None:
            _ = self.request.gettext

            assert self.object_class is not None  # type checker

            raise HTTPBadRequest(
                _("Cannot find {object_class} with {server_pk_name}:{pk_value}").format(  # noqa: E501
                    object_class=self.object_class.__name__,
                    server_pk_name=self.server_pk_name,
                    pk_value=pk_value
                )
            )

        return obj


class ModelFormMixin(FormMixin, SingleObjectMixin):
    object_class = None

    model_form_dict: Dict
    object: Optional["Base"]
    request: "CamcopsRequest"

    def form_valid(self, form: "Form", appstruct: Dict[str, Any]) -> None:
        """If the form is valid, save the associated model."""
        self.save_object(appstruct)
        return super().form_valid(form, appstruct)

    def save_object(self, appstruct: Dict[str, Any]) -> None:
        if self.object is None:
            if self.object_class is None:
                raise_runtime_error("Your view must provide an object_class.")

            assert self.object_class is not None  # type checker

            self.object = self.object_class()

        self.set_object_properties(appstruct)

        self.request.dbsession.add(self.object)

    def set_object_properties(self, appstruct: Dict[str, Any]) -> None:
        for (model_attr, form_param) in self.model_form_dict.items():
            value = appstruct.get(form_param)
            setattr(self.object, model_attr, value)

    def get_form_values(self) -> Dict:
        form_values = {}

        if self.object is not None:
            for (model_attr, form_param) in self.model_form_dict.items():
                value = getattr(self.object, model_attr)
                form_values[form_param] = value

        return form_values


class ProcessFormView(View):
    """Render a form on GET and processes it on POST."""
    def get(self) -> Any:
        """Handle GET requests: instantiate a blank version of the form."""
        return self.render_to_response(self.get_context_data())

    def post(self) -> Any:
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        if FormAction.CANCEL in self.request.POST:
            raise HTTPFound(self.get_cancel_url())

        form = self.get_form()

        controls = list(self.request.POST.items())

        try:
            appstruct = form.validate(controls)

            return self.form_valid(form, appstruct)
        except ValidationFailure as e:
            return self.form_invalid(e)


class BaseFormView(FormMixin, ProcessFormView):
    """A base view for displaying a form."""


class FormView(TemplateResponseMixin, BaseFormView):
    """A view for displaying a form and rendering a template response."""


class BaseCreateView(ModelFormMixin, ProcessFormView):
    """
    Base view for creating a new object instance.

    Using this base class requires subclassing to provide a response mixin.
    """
    def get(self) -> Any:
        self.object = None
        return super().get()

    def post(self) -> Any:
        self.object = None
        return super().post()


class CreateView(TemplateResponseMixin, BaseCreateView):
    """
    View for creating a new object, with a response rendered by a template.
    """


class BaseUpdateView(ModelFormMixin, ProcessFormView):
    """
    Base view for updating an existing object.

    Using this base class requires subclassing to provide a response mixin.
    """
    pk = None

    def get(self) -> Any:
        self.object = self.get_object()
        return super().get()

    def post(self) -> Any:
        self.object = self.get_object()
        return super().post()


class UpdateView(TemplateResponseMixin, BaseUpdateView):
    """View for updating an object, with a response rendered by a template."""


class BaseDeleteView(FormMixin, SingleObjectMixin, View):
    """
    Base view for deleting an object.

    Using this base class requires subclassing to provide a response mixin.
    """
    success_url = None

    def delete(self) -> None:
        """
        Delete the fetched object
        """
        self.request.dbsession.delete(self.object)

    def get(self) -> Any:
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def post(self) -> Any:
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()

        if FormAction.CANCEL in self.request.POST:
            raise HTTPFound(self.get_cancel_url())

        form = self.get_form()
        controls = list(self.request.POST.items())

        try:
            appstruct = form.validate(controls)

            return self.form_valid(form, appstruct)
        except ValidationFailure as e:
            return self.form_invalid(e)

    def form_valid(self, form: "Form", appstruct: Dict[str, Any]) -> None:
        """If the form is valid, delete the associated model."""

        self.delete()

        return super().form_valid(form, appstruct)

    def get_form_values(self) -> Dict:
        return {}


class DeleteView(TemplateResponseMixin, BaseDeleteView):
    """
    View for deleting an object retrieved with self.get_object(), with a
    response rendered by a template.
    """
