#!/usr/bin/python

# Author: Rudolf Cardinal (rudolf@pobox.com)
# Created: 2012
# Employer: University of Cambridge
# Funding: Wellcome Trust
# Copyright (C) 2012-2013
# Licence: http://creativecommons.org/licenses/by/3.0/

import camcopswebview  # module that does the real work

# =============================================================================
# CGI method - no longer used
# =============================================================================

# A two-script method:
# (a) better exception reporting to the HTTP client --- SUPERSEDED by import
#     cgitb
# (b) imported modules are automatically compiled, so load faster
# (c) Apache not quite so fussy about ownership of the script that gets edited
#     more

# camcopswebview.main()

# =============================================================================
# Wrapper to print errors
# =============================================================================

import sys
import cgitb
import StringIO


class ErrorReportingMiddleware(object):
    def __init__(self, app):
        self.app = app

    def format_exception(self, exc_info):
        dummy_file = StringIO.StringIO()
        hook = cgitb.Hook(file=dummy_file)
        hook(*exc_info)
        return [dummy_file.getvalue()]

    def __call__(self, environ, start_response):
        try:
            return self.app(environ, start_response)
        except:
            exc_info = sys.exc_info()
            start_response(
                '500 Internal Server Error',
                [('content-type', 'text/html')],
                exc_info
            )
            return self.format_exception(exc_info)

# =============================================================================
# WSGI entry point
# =============================================================================

application = ErrorReportingMiddleware(camcopswebview.application)
