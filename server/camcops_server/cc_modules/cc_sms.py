#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_sms.py

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

**Send SMS via supported backends**

"""

import logging
from typing import Any, Dict


import requests

_backends = {}
log = logging.getLogger(__name__)


class MissingBackendException(Exception):
    pass


def register_backend(name: str, backend_class) -> None:
    global _backends
    _backends[name] = backend_class


class SmsBackend:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config

    def send_sms(self, recipient: str, message: str, sender: str = None):
        raise NotImplementedError


class ConsoleSmsBackend(SmsBackend):
    def send_sms(self, recipient: str, message: str, sender: str = None):
        log.info(f"Sent message '{message}' to {recipient}")


class KapowSmsBackend(SmsBackend):
    API_URL = "https://www.kapow.co.uk/scripts/sendsms.php"

    def send_sms(self, recipient: str, message: str, sender: str = None):
        data = {"username": self.config["username"],
                "password": self.config["password"]}

        data.update(mobile=recipient, sms=message)

        requests.post(self.API_URL, data=data)


register_backend("console", ConsoleSmsBackend)
register_backend("kapow", KapowSmsBackend)


def get_sms_backend(label: str, config: Dict[str, Any]) -> SmsBackend:
    global _backends
    try:
        backend_class = _backends[label]
    except KeyError:
        raise MissingBackendException(f"No backend '{label}' registered")

    return backend_class(config)
