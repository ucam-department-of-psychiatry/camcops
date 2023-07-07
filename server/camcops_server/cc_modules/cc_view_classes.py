"""
camcops_server/cc_modules/cc_view_classes.py

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

Django-style class-based views for Pyramid.
Adapted from Django's ``views/generic/base.py`` and ``views/generic/edit.py``.

Django has the following licence:

.. code-block:: none

    Copyright (c) Django Software Foundation and individual contributors.
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

        1. Redistributions of source code must retain the above copyright
           notice, this list of conditions and the following disclaimer.

        2. Redistributions in binary form must reproduce the above copyright
           notice, this list of conditions and the following disclaimer in the
           documentation and/or other materials provided with the distribution.

        3. Neither the name of Django nor the names of its contributors may be
           used to endorse or promote products derived from this software
           without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
    LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    POSSIBILITY OF SUCH DAMAGE.

Custom views typically inherit from :class:`CreateView`, :class:`DeleteView` or
:class:`UpdateView`.

A Pyramid view function with a named route should create a view of the custom
class, passing in the request, and return the results of its ``dispatch()``
method. For example:

.. code-block:: python

    @view_config(route_name="edit_server_created_patient")
    def edit_server_created_patient(req: Request) -> Response:
        return EditServerCreatedPatientView(req).dispatch()

To provide a custom view class to create a new object in the database:

- Inherit from :class:`CreateView`.
- Set the ``object_class`` property.
- Set the ``form_class`` property.
- Set the ``template_name`` property or implement ``get_template_name()``.
- Override ``get_extra_context()`` for any extra parameters to pass to the
  template.
- Set ``success_url`` or override ``get_success_url()`` to be the redirect on
  successful creation.
- Override ``get_form_kwargs()`` for any extra parameters to pass to the form
  constructor.
- For simple views, set the ``model_form_dict`` property to be a mapping of
  object properties to form parameters.
- Override ``get_form_values()`` with any values additional to
  ``model_form_dict`` to populate the form.
- Override ``save_object()`` to do anything more than a simple record save
  (saving related objects, for example).

To provide a custom view class to delete an object from the database:

- Inherit from :class:`DeleteView`.
- Set the ``object_class`` property.
- Set the ``form_class`` property.
- Set the ``template_name`` property or implement ``get_template_name()``.
- Override ``get_extra_context()``. for any extra parameters to pass to the
  template.
- Set ``success_url`` or override ``get_success_url()`` to be the redirect on
  successful creation.
- Override ``get_form_kwargs()`` for any extra parameters to pass to the form
  constructor.
- Set the ``pk_param`` property to be the name of the parameter in the request
  that holds the unique/primary key of the object to be deleted.
- Set the ``server_pk_name`` property to be the name of the property on the
  object that is the unique/primary key.
- Override ``get_object()`` if the object cannot be retrieved with the above.
- Override ``delete()`` to do anything more than a simple record delete; for
  example, to delete dependant objects

To provide a custom view class to update an object in the database:

- Inherit from :class:`UpdateView`.
- Set the ``object_class`` property.
- Set the ``form_class`` property.
- Set the ``template_name`` property or implement ``get_template_name()``.
- Override ``get_extra_context()`` for any extra parameters to pass to the
  template.
- Set ``success_url`` or override ``get_success_url()`` to be the redirect on
  successful creation.
- Override ``get_form_kwargs()`` for any extra parameters to pass to the form
  constructor.
- Set the ``pk_param`` property to be the name of the parameter in the request
  that holds the unique/primary key of the object to be updated.
- Set the ``server_pk_name`` property to be the name of the property on the
  object that is the unique/primary key.
- Override ``get_object()`` if the object cannot be retrieved with the above.
- For simple views, set the ``model_form_dict`` property to be a mapping of
  object properties to form parameters.
- Override ``save_object()`` to do anything more than a simple record save
  (saving related objects, for example).

You can use mixins for settings common to multiple views.

.. note::

    When we move to Python 3.8, there is ``typing.Protocol``, which allows
    mixins to be type-checked properly. Currently we suppress warnings.

Some examples are in ``webview.py``.

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
from cardinal_pythonlib.httpconst import HttpMethod, HttpStatus
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.typing_helpers import with_typehint, with_typehints
from deform.exception import ValidationFailure

from camcops_server.cc_modules.cc_exception import raise_runtime_error
from camcops_server.cc_modules.cc_pyramid import FlashQueue, FormAction
from camcops_server.cc_modules.cc_resource_registry import (
    CamcopsResourceRegistry,
)

if TYPE_CHECKING:
    from deform.form import Form
    from camcops_server.cc_modules.cc_request import CamcopsRequest

log = BraceStyleAdapter(logging.getLogger(__name__))


# =============================================================================
# View
# =============================================================================


class View(object):
    """
    Simple parent class for all views. Owns the request object and provides a
    dispatcher for HTTP requests.

    Derived classes typically implement ``get()`` and ``post()``.
    """

    http_method_names = [HttpMethod.GET.lower(), HttpMethod.POST.lower()]

    # -------------------------------------------------------------------------
    # Creation
    # -------------------------------------------------------------------------

    def __init__(self, request: "CamcopsRequest") -> None:
        """
        Args:
            request:
                a :class:`camcops_server.cc_modules.cc_request.CamcopsRequest`
        """
        self.request = request

    # -------------------------------------------------------------------------
    # Dispatching GET and POST requests
    # -------------------------------------------------------------------------

    def dispatch(self) -> Response:
        """
        Try to dispatch to the right HTTP method (e.g. GET, POST). If a method
        doesn't exist, defer to the error handler. Also defer to the error
        handler if the request method isn't on the approved list.

        Specifically, this ends up calling ``self.get()`` or ``self.post()`` or
        ``self.http_method_not_allowed()``.
        """
        handler = self.http_method_not_allowed
        method_lower = self.request.method.lower()
        if method_lower in self.http_method_names:
            handler = getattr(self, method_lower, handler)
        return handler()

    def http_method_not_allowed(self) -> NoReturn:
        """
        Raise a :exc:`pyramid.httpexceptions.HTTPMethodNotAllowed` (error 405)
        indicating that the selected HTTP method is not allowed.
        """
        log.warning(
            "Method Not Allowed (%s): %s",
            self.request.method,
            self.request.path,
            extra={
                "status_code": HttpStatus.METHOD_NOT_ALLOWED,
                "request": self.request,
            },
        )
        raise HTTPMethodNotAllowed(
            detail=f"Allowed methods: {self._allowed_methods}"
        )

    def _allowed_methods(self) -> List[str]:
        """
        Which HTTP methods are allowed? Returns a list of upper-case strings.
        """
        return [m.upper() for m in self.http_method_names if hasattr(self, m)]


# =============================================================================
# Basic mixins
# =============================================================================


class ContextMixin(object):
    """
    A default context mixin that passes the keyword arguments received by
    get_context_data() as the template context.
    """

    def get_extra_context(self) -> Dict[str, Any]:
        """
        Override to provide extra context, merged in by
        :meth:`get_context_data`.
        """
        return {}

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Provides context for a template, including the ``view`` argument and
        any additional context provided by :meth:`get_extra_context`.
        """
        kwargs.setdefault("view", self)
        kwargs.update(self.get_extra_context())

        return kwargs


class TemplateResponseMixin(object):
    """
    A mixin that can be used to render a Mako template.
    """

    request: "CamcopsRequest"
    template_name: str = None

    def render_to_response(self, context: Dict) -> Response:
        """
        Takes the supplied context, renders it through our specified template
        (set by ``template_name``), and returns a
        :class:`pyramid.response.Response`.
        """
        return render_to_response(
            self.get_template_name(), context, request=self.request
        )

    def get_template_name(self) -> str:
        """
        Returns the template filename.
        """
        if self.template_name is None:
            raise_runtime_error(
                "You must set template_name or override "
                f"get_template_name() in {self.__class__}."
            )

        return self.template_name


# =============================================================================
# Form views
# =============================================================================


class ProcessFormView(
    View, with_typehints(ContextMixin, TemplateResponseMixin)
):
    """
    Render a form on GET and processes it on POST.

    Requires ContextMixin.
    """

    # -------------------------------------------------------------------------
    # GET and POST handlers
    # -------------------------------------------------------------------------

    def get(self) -> Response:
        """
        Handle GET requests: instantiate a blank version of the form and render
        it.
        """
        # noinspection PyUnresolvedReferences
        return self.render_to_response(self.get_context_data())

    def post(self) -> Response:
        """
        Handle POST requests:

        - if the user has cancelled, redirect to the cancellation URL;
        - instantiate a form instance with the passed POST variables and then
          check if it's valid;
        - if it's invalid, call ``form_invalid()``, which typically
          renders the form to show the errors and allow resubmission;
        - if it's valid, call ``form_valid()``, which in the default handler

          (a) processes data via ``form_valid_process_data()``, and
          (b) returns a response (either another form or redirection to another
              URL) via ``form_valid_response()``.
        """
        if FormAction.CANCEL in self.request.POST:
            # noinspection PyUnresolvedReferences
            raise HTTPFound(self.get_cancel_url())

        # noinspection PyUnresolvedReferences
        form = self.get_form()
        controls = list(self.request.POST.items())

        try:
            appstruct = form.validate(controls)

            # noinspection PyUnresolvedReferences
            return self.form_valid(form, appstruct)
        except ValidationFailure as e:
            # e.error.asdict() will reveal more

            # noinspection PyUnresolvedReferences
            return self.form_invalid(e)

    # -------------------------------------------------------------------------
    # Cancellation
    # -------------------------------------------------------------------------

    def get_cancel_url(self) -> str:
        """
        Return the URL to redirect to when cancelling a form.
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Processing valid and invalid forms on POST
    # -------------------------------------------------------------------------

    def form_valid(self, form: "Form", appstruct: Dict[str, Any]) -> Response:
        """
        2021-10-05: separate data handling and the response to return. Why?
        Because:

        (a) returning a response can involve "return response" or "raise
            HTTPFound", making flow harder to track;
        (b) the Python method resolution order (MRO) makes it harder to be
            clear on the flow through the combination function.
        """
        self.form_valid_process_data(form, appstruct)
        return self.form_valid_response(form, appstruct)

    def form_valid_process_data(
        self, form: "Form", appstruct: Dict[str, Any]
    ) -> None:
        """
        Perform any handling of data from the form.

        Override in subclasses or mixins if necessary. Be sure to call the
        superclass method to ensure all actions are performed.
        """
        pass

    def form_valid_response(
        self, form: "Form", appstruct: Dict[str, Any]
    ) -> Response:
        """
        Return the response (or raise a redirection exception) following valid
        form submission.
        """
        raise NotImplementedError

    def form_invalid(self, validation_error: ValidationFailure) -> Response:
        """
        Called when the form is submitted via POST and is invalid.
        Returns a response with a rendering of the invalid form.
        """
        raise NotImplementedError


# =============================================================================
# Form mixin
# =============================================================================


class FormMixin(ContextMixin, with_typehint(ProcessFormView)):
    """
    Provide a way to show and handle a single form in a request.
    """

    cancel_url = None
    form_class: Type["Form"] = None
    success_url = None
    failure_url = None
    _form = None
    _error = None

    request: "CamcopsRequest"

    # -------------------------------------------------------------------------
    # Creating the form
    # -------------------------------------------------------------------------

    def get_form_class(self) -> Optional[Type["Form"]]:
        """
        Return the form class to use.
        """
        return self.form_class

    def get_form(self) -> "Form":
        """
        Return an instance of the form to be used in this view.
        """
        form_class = self.get_form_class()
        if not form_class:
            raise_runtime_error("Your view must provide a form_class.")
        assert form_class is not None  # type checker

        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self) -> Dict[str, Any]:
        """
        Return the keyword arguments for instantiating the form.
        """
        return {
            "request": self.request,
            "resource_registry": CamcopsResourceRegistry(),
        }

    def get_rendered_form(self, form: "Form") -> str:
        """
        Returns the form, rendered as HTML.
        """
        if self._error is not None:
            return self._error.render()

        # noinspection PyUnresolvedReferences
        appstruct = self.get_form_values()
        return form.render(appstruct)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Insert the rendered form (as HTML) into the context dict.
        """
        form = self.get_form()
        kwargs["form"] = self.get_rendered_form(form)
        kwargs["head_form_html"] = get_head_form_html(self.request, [form])
        return super().get_context_data(**kwargs)

    # -------------------------------------------------------------------------
    # Destination URLs
    # -------------------------------------------------------------------------

    def get_cancel_url(self) -> str:
        """
        Return the URL to redirect to when cancelling a form.
        """
        if not self.cancel_url:
            return self.get_success_url()
        return str(self.cancel_url)  # cancel_url may be lazy

    def get_success_url(self) -> str:
        """
        Return the URL to redirect to after processing a valid form.
        """
        if not self.success_url:
            raise_runtime_error("Your view must provide a success_url.")
        return str(self.success_url)  # success_url may be lazy

    def get_failure_url(self) -> str:
        """
        Return the URL to redirect to on error after processing a valid form.
        e.g. when a password is of the correct form but is invalid.
        """
        if not self.failure_url:
            raise_runtime_error("Your view must provide a failure_url.")
        return str(self.failure_url)  # failure_url may be lazy

    # -------------------------------------------------------------------------
    # Handling valid/invalid forms
    # -------------------------------------------------------------------------

    # noinspection PyTypeChecker
    def form_valid_response(
        self, form: "Form", appstruct: Dict[str, Any]
    ) -> Response:
        """
        Called when the form is submitted via POST and is valid.
        Redirects to the supplied "success" URL.
        """
        raise HTTPFound(self.get_success_url())

    def form_invalid(self, validation_error: ValidationFailure) -> Response:
        """
        Called when the form is submitted via POST and is invalid.
        Returns a response with a rendering of the invalid form.
        """
        self._error = validation_error

        # noinspection PyUnresolvedReferences
        return self.render_to_response(self.get_context_data())

    # -------------------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------------------

    def fail(self, message: str) -> NoReturn:
        """
        Raises a failure exception, redirecting to a failure URL.
        """
        self.request.session.flash(message, queue=FlashQueue.DANGER)
        raise HTTPFound(self.get_failure_url())


class BaseFormView(FormMixin, ProcessFormView):
    """
    A base view for displaying a form.
    """

    pass


class FormView(TemplateResponseMixin, BaseFormView):
    """
    A view for displaying a form and rendering a template response.
    """

    pass


# =============================================================================
# Multi-step forms
# =============================================================================


class FormWizardMixin(with_typehints(FormMixin, ProcessFormView)):
    """
    Basic support for multi-step form entry.
    For more complexity we could do something like
    https://github.com/jazzband/django-formtools/tree/master/formtools/wizard

    We store temporary state in the ``form_state`` dictionary on the
    :class:`CamcopsSession` object on the request. Arbitrary values can be
    stored in ``form_state``. The following are used by this mixin:

    - "step" stores the name of the current form entry step.
    - "route_name" stores the name of the current route, so we can detect if
      the form state is stale from a previous incomplete operation.

    Views using this Mixin should implement:

    ``wizard_first_step``: The name of the first form entry step
    ``wizard_forms``: step name -> :class:``Form`` dict
    ``wizard_templates``: step name -> template filename dict
    ``wizard_extra_contexts``: step name -> context dict dict

    Alternatively, subclasses can override ``get_first_step()`` etc.

    The logic of changing steps is left to the subclass.
    """

    PARAM_FINISHED = "finished"
    PARAM_STEP = "step"
    PARAM_ROUTE_NAME = "route_name"

    wizard_first_step: Optional[str] = None
    wizard_forms: Dict[str, Type["Form"]] = {}
    wizard_templates: Dict[str, str] = {}
    wizard_extra_contexts: Dict[str, Dict[str, Any]] = {}

    def __init__(self, *args, **kwargs) -> None:
        """
        We prevent stale state from messing things up by clearing state when a
        form sequence starts. Form sequences start with HTTP GET and proceed
        via HTTP POST. So, if this is a GET request, we clear the state. We do
        so in the __init__ sequence, as others may wish to write state before
        the view is dispatched.

        An example of stale state: the user sets an MFA method but then that is
        disallowed on the server whilst they are halfway through login. (That
        leaves users totally stuffed as they are not properly "logged in" and
        therefore can't easily log out.)

        There are other examples seen in testing. This method gets round all
        those. (For example, the worst-case situation is then advising the user
        to log in again, or start whatever form-based process it was again).

        We also reset the state if the stored route name doesn't match the
        current route name.
        """
        super().__init__(*args, **kwargs)  # initializes self.request

        # Make sure we save any changes to the form state
        self.request.dbsession.add(self.request.camcops_session)

        if (
            self.request.method == HttpMethod.GET
            or self.route_name != self._request_route_name
        ):
            # If self.route_name was None when tested here, it will be
            # initialised to self._request_route_name when first fetched
            # (see getter/setter below) so this "!=" test will be False.
            self._clear_state()

    # -------------------------------------------------------------------------
    # State
    # -------------------------------------------------------------------------

    @property
    def state(self) -> Dict[str, Any]:
        """
        Returns the (arbitrary) state dictionary. See class help.
        """
        if self.request.camcops_session.form_state is None:
            self.request.camcops_session.form_state = dict()

        return self.request.camcops_session.form_state

    @state.setter
    def state(self, state: Optional[Dict[str, Any]]) -> None:
        """
        Sets the (arbitrary) state dictionary. See class help.
        """
        self.request.camcops_session.form_state = state

    def _clear_state(self) -> None:
        """
        Creates a fresh starting state.
        """
        self.state = {
            self.PARAM_FINISHED: False,
            self.PARAM_ROUTE_NAME: self._request_route_name,
            # ... we use str() largely because in the unit testing framework,
            # we get objects like <Mock name='mock.name' id='140226165199816'>,
            # which is not JSON-serializable.
        }

    # -------------------------------------------------------------------------
    # Step (an aspect of state)
    # -------------------------------------------------------------------------

    @property
    def step(self) -> str:
        """
        Returns the current step.
        """
        step = self.state.setdefault(self.PARAM_STEP, self.get_first_step())
        return step

    @step.setter
    def step(self, step: str) -> None:
        """
        Sets the current step.
        """
        self.state[self.PARAM_STEP] = step

    def get_first_step(self) -> str:
        """
        Returns the first step to be used when the form is first loaded.
        """
        return self.wizard_first_step

    # -------------------------------------------------------------------------
    # Finishing (an aspect of state)
    # -------------------------------------------------------------------------

    def finish(self) -> None:
        """
        Ends, by marking the state as finished, and clearing any other
        state except the current route/step (the step in particular may be
        useful for subsequent functions).
        """
        self.state = {
            self.PARAM_FINISHED: True,
            self.PARAM_ROUTE_NAME: self._request_route_name,
            self.PARAM_STEP: self.step,
        }

    def finished(self) -> bool:
        """
        Have we finished?
        """
        return self.state.get(self.PARAM_FINISHED, False)

    # -------------------------------------------------------------------------
    # Routes (an aspect of state)
    # -------------------------------------------------------------------------

    @property
    def _request_route_name(self) -> str:
        """
        Return the route name from the request. If for some reason it's
        missing, we return an empty string.

        We convert using ``str()`` largely because in the unit testing
        framework, we get objects like ``<Mock name='mock.name'
        id='140226165199816'>``, which is not JSON-serializable.
        """
        name = self.request.matched_route.name
        return str(name) if name else ""

    @property
    def route_name(self) -> Optional[str]:
        """
        Get the name of the current route. See class help.
        """
        return self.state.setdefault(
            self.PARAM_ROUTE_NAME, self._request_route_name
        )

    @route_name.setter
    def route_name(self, route_name: str) -> None:
        """
        Set the name of the current route. See class help.
        """
        self.state[self.PARAM_ROUTE_NAME] = route_name

    # -------------------------------------------------------------------------
    # Step-specific information
    # -------------------------------------------------------------------------

    def get_form_class(self) -> Optional[Type["Form"]]:
        """
        Returns the class of Form to be used for the current step (not a form
        instance).
        """
        return self.wizard_forms[self.step]

    def get_template_name(self) -> str:
        """
        Returns the Mako template filename to be used for the current step.
        """
        return self.wizard_templates[self.step]

    def get_extra_context(self) -> Dict[str, Any]:
        """
        Returns any extra context information (as a dictionary) for the current
        step.
        """
        return self.wizard_extra_contexts[self.step]

    # -------------------------------------------------------------------------
    # Success
    # -------------------------------------------------------------------------

    def form_valid_response(
        self, form: "Form", appstruct: Dict[str, Any]
    ) -> Response:
        """
        Called when the form is submitted via POST and is valid.
        Redirects to the supplied "success" URL.
        """
        if self.finished():
            raise HTTPFound(self.get_success_url())
        else:
            # Try to keep this in POST -- fewer requests, but it also means
            # that we can use GET to indicate the first in a sequence, and thus
            # be able to clear stale state correctly.

            # The "step" should have been changed, and that means that we will
            # get a new form:
            return self.get()

    # -------------------------------------------------------------------------
    # Failure
    # -------------------------------------------------------------------------

    def fail(self, message: str) -> NoReturn:
        """
        Raises a failure.
        """
        self.finish()
        super().fail(message)  # will raise
        assert False, "Bug: FormWizardMixin.fail() falling through"


# =============================================================================
# ORM mixins
# =============================================================================


class SingleObjectMixin(ContextMixin):
    """
    Represents a single ORM object, for use as a mixin.
    """

    object: Any
    object_class: Optional[Type[Any]]
    pk_param: str
    request: "CamcopsRequest"
    server_pk_name: str

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Insert the single object into the context dict.
        """
        context = {}
        if self.object:
            context["object"] = self.object

        context.update(kwargs)

        return super().get_context_data(**context)

    def get_object(self) -> Any:
        """
        Returns the ORM object being manipulated.
        """
        pk_value = self.get_pk_value()

        if self.object_class is None:
            raise_runtime_error("Your view must provide an object_class.")

        pk_property = getattr(self.object_class, self.server_pk_name)

        obj = (
            self.request.dbsession.query(self.object_class)
            .filter(pk_property == pk_value)
            .one_or_none()
        )

        if obj is None:
            _ = self.request.gettext

            assert self.object_class is not None  # type checker

            raise HTTPBadRequest(
                _(
                    "Cannot find {object_class} with "
                    "{server_pk_name}:{pk_value}"
                ).format(
                    object_class=self.object_class.__name__,
                    server_pk_name=self.server_pk_name,
                    pk_value=pk_value,
                )
            )

        return obj

    def get_pk_value(self) -> int:
        """
        Returns the integer primary key of the object.
        """
        return self.request.get_int_param(self.pk_param)


class ModelFormMixin(FormMixin, SingleObjectMixin):
    """
    Represents an ORM object (the model) and an associated form.
    """

    object_class: Optional[Type[Any]] = None

    model_form_dict: Dict  # maps model attribute name to form param name
    object: Any  # the object being manipulated
    request: "CamcopsRequest"

    def form_valid_process_data(
        self, form: "Form", appstruct: Dict[str, Any]
    ) -> None:
        """
        Called when the form is valid.
        Saves the associated model.
        """
        self.save_object(appstruct)
        super().form_valid_process_data(form, appstruct)

    def save_object(self, appstruct: Dict[str, Any]) -> None:
        """
        Saves the object in the database, from data provided via the form.
        """
        if self.object is None:
            if self.object_class is None:
                raise_runtime_error("Your view must provide an object_class.")
            assert self.object_class is not None  # type checker
            self.object = self.object_class()

        self.set_object_properties(appstruct)
        self.request.dbsession.add(self.object)

    def get_model_form_dict(self) -> Dict[str, str]:
        """
        Returns the dictionary mapping model attribute names to form parameter
        names.
        """
        return self.model_form_dict

    def set_object_properties(self, appstruct: Dict[str, Any]) -> None:
        """
        Sets properties of the object, from form data.
        """
        # No need to call superclass method; this is the top level.
        for (model_attr, form_param) in self.get_model_form_dict().items():
            try:
                value = appstruct[form_param]
                setattr(self.object, model_attr, value)
            except KeyError:
                # Value may have been removed from appstruct: don't change
                pass

    def get_form_values(self) -> Dict[str, Any]:
        """
        Reads form values from the object (or provides an empty dictionary if
        there is no object yet). Returns a form dictionary.
        """
        form_values = {}

        if self.object is not None:
            for (model_attr, form_param) in self.get_model_form_dict().items():
                value = getattr(self.object, model_attr)

                # Not sure if this is a good idea. There may be legitimate
                # reasons for keeping the value None here, but the view is
                # likely to be overriding get_form_values() in that case.
                # The alternative is we have to set all None string values
                # to empty, in order to prevent the word None from appearing
                # in text input fields.
                if value is None:
                    value = ""
                form_values[form_param] = value

        return form_values


# =============================================================================
# Views involving forms and ORM objects
# =============================================================================


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

    pass


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
    """
    View for updating an object, with a response rendered by a template.
    """

    pass


class BaseDeleteView(FormMixin, SingleObjectMixin, ProcessFormView):
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

    def get(self) -> Response:
        """
        Handle GET requests: fetch the object from the database, and renders
        a form with its data.
        """
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        # noinspection PyUnresolvedReferences
        return self.render_to_response(context)

    def post(self) -> Response:
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()
        return super().post()

    def form_valid_process_data(
        self, form: "Form", appstruct: Dict[str, Any]
    ) -> None:
        """
        Called when the form is valid.
        Deletes the associated model.
        """
        self.delete()
        super().form_valid_process_data(form, appstruct)

    # noinspection PyMethodMayBeStatic
    def get_form_values(self) -> Dict[str, Any]:
        # Docstring in superclass
        return {}


class DeleteView(TemplateResponseMixin, BaseDeleteView):
    """
    View for deleting an object retrieved with self.get_object(), with a
    response rendered by a template.
    """

    pass
