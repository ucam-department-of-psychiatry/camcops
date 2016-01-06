#!/usr/bin/python

# http://pylonsbook.com/en/1.0/the-web-server-gateway-interface-wsgi.html

import cgitb
import os
import StringIO
import sys

import pythonlib.rnc_db as rnc_db
import pythonlib.rnc_web as ws


# =============================================================================
# Actual demo application
# =============================================================================

def connect_to_database(environ):
    # Specific to our setup. Select a database engine.
    CAMCOPS_DB_NAME = environ.get("CAMCOPS_DB_NAME", "camcops")
    CAMCOPS_DB_USER = environ.get("CAMCOPS_DB_USER", "root")
    CAMCOPS_DB_PASSWORD = environ.get("CAMCOPS_DB_PASSWORD")
    CAMCOPS_DB_SERVER = environ.get("CAMCOPS_DB_SERVER", "localhost")
    CAMCOPS_DB_PORT = int(environ.get("CAMCOPS_DB_PORT", "3306"))

    if CAMCOPS_DB_PASSWORD is None:
        raise Exception("No database password specified")
    db = rnc_db.DatabaseSupporter()
    db.connect_to_database_mysql(
        server=CAMCOPS_DB_SERVER,
        port=CAMCOPS_DB_PORT,
        database=CAMCOPS_DB_NAME,
        user=CAMCOPS_DB_USER,
        password=CAMCOPS_DB_PASSWORD
    )
    return db


def application_show_environment_test_database(environ, start_response):
    LINEBREAK = "=" * 79 + "\n"

    status = '200 OK'
    if not environ['mod_wsgi.process_group']:
        output = 'mod_wsgi EMBEDDED MODE'
    else:
        output = 'mod_wsgi DAEMON MODE'

    output += "\n\nenviron parameter:\n" + LINEBREAK
    for (k, v) in sorted(environ.iteritems()):
        output += str(k) + ": " + str(v) + "\n"

    output += "\nos.environ:\n" + LINEBREAK
    for (k, v) in sorted(os.environ.iteritems()):
        output += str(k) + ": " + str(v) + "\n"

    output += "\nCGI form:\n" + LINEBREAK
    form = ws.get_cgi_fieldstorage_from_wsgi_env(environ)
    for k in form.keys():
        output += "{0} = {1}\n".format(k, form.getvalue(k))

    output += "\nCGI value for 'test' field:\n" + LINEBREAK
    output += "{}\n".format(ws.get_cgi_parameter_str(form, "test"))

    output += "\nCGI value for 'Test' field:\n" + LINEBREAK
    output += "{}\n".format(ws.get_cgi_parameter_str(form, "Test"))

    # This successfully writes to the Apache log:
    sys.stderr.write("testwsgi.py: STARTING\n")

    # Let's not bother with a persistent database connection for now.
    # http://stackoverflow.com/questions/405352/mysql-connection-pooling-question-is-it-worth-it  # noqa

    testDatabase = False
    if testDatabase:
        db = connect_to_database(environ)
        output += "\nCONNECTED TO DATABASE\n" + LINEBREAK
        output += (
            "Count: " +
            str(db.fetchvalue("SELECT COUNT(*) FROM expdetthreshold")) + "\n"
        )

    # Final output
    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]


# =============================================================================
# Wrapper to print errors
# =============================================================================

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

application = ErrorReportingMiddleware(
    application_show_environment_test_database)
