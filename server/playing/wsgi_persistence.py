#!/usr/bin/env python

import base64
import http.cookies
import os


# noinspection PyUnusedLocal
def application(environ, start_response):
    status = '200 OK'
    output = 'Hello'.encode('utf-8')
    cookie = http.cookies.SimpleCookie()
    # No expiration date, making it a session cookie
    randbytes = os.urandom(10)
    randstring = base64.urlsafe_b64encode(randbytes).decode('ascii')
    cookie["randomness"] = randstring
    cookie_tuples = [
        ("Set-Cookie", morsel.OutputString())
        for morsel in cookie.values()
    ]
    response_headers = [('Content-type', 'text/plain; charset=utf-8'),
                        ('Content-Length', str(len(output)))] + cookie_tuples
    start_response(status, response_headers)
    return [output]

"""
Run with:
$ gunicorn wsgi_persistence:application

Check with:
$ wget http://127.0.0.1:8000 --server-response
"""
