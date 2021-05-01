#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_response.py

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

**Implements a Pyramid Response object customized for CamCOPS.**

We do this only to set the HTTP ``Content-Security-Policy`` header to match
the nonce set by the
:class:``camcops_server.cc_modules.cc_request.CamcopsRequest``.

"""

from typing import TYPE_CHECKING

from pyramid.response import Response

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_request import CamcopsRequest


class CamcopsResponse(Response):
    def __init__(self, camcops_request: "CamcopsRequest", **kwargs) -> None:
        super().__init__(**kwargs)

        # ---------------------------------------------------------------------
        # Control resources that are permitted to load, to mitigate against
        # cross-site scripting attacks
        # ---------------------------------------------------------------------
        # - Content-Security-Policy.
        # - Recommended by Falanx penetration testing.
        # - https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy  # noqa
        # - Defaults from https://owasp.org/www-project-secure-headers/
        # - Re scripts: see https://csper.io/blog/no-more-unsafe-inline
        # - Re nonces (and in general): see
        #   https://stackoverflow.com/questions/42922784/what-s-the-purpose-of-the-html-nonce-attribute-for-script-and-style-elements  # noqa

        # This will add a header, not overwrite the existing header. However,
        # multiple headers combine to produce the most restrictive and can get
        # confusing; best to use one. See
        # https://chrisguitarguy.com/2019/07/05/working-with-multiple-content-security-policy-headers/  # noqa

        nonce = camcops_request.nonce
        self.headers["Content-Security-Policy"] = (
            "default-src 'self' data:; "
            "object-src 'none'; "
            "child-src 'self'; "

            f"style-src 'nonce-{nonce}' 'self'; "
            # ... meaning: allow inline CSS only if it is tagged with this
            # nonce, via <style nonce="XXX">, or if it comes from our site
            # ('self'). See
            # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/style-src  # noqa

            # And similarly for scripts:
            f"script-src 'nonce-{nonce}' 'self'; "

            "frame-ancestors 'none'; "
            "upgrade-insecure-requests; "
            "block-all-mixed-content"
        )


def camcops_response_factory(request: "CamcopsRequest") -> Response:
    return CamcopsResponse(camcops_request=request)
