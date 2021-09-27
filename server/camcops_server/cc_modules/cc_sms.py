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
from typing import Any, Dict, Type


import requests
from twilio.rest import Client

_backends = {}
log = logging.getLogger(__name__)


class MissingBackendException(Exception):
    pass


class SmsBackend:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config

    def send_sms(self, recipient: str,
                 message: str, sender: str = None) -> None:
        raise NotImplementedError


class ConsoleSmsBackend(SmsBackend):
    def send_sms(self, recipient: str,
                 message: str, sender: str = None) -> None:
        log.info(f"Sent message '{message}' to {recipient}")


class KapowSmsBackend(SmsBackend):
    API_URL = "https://www.kapow.co.uk/scripts/sendsms.php"

    def send_sms(self, recipient: str,
                 message: str, sender: str = None) -> None:
        data = {"username": self.config["username"],
                "password": self.config["password"]}

        data.update(mobile=recipient, sms=message)

        requests.post(self.API_URL, data=data)


class TwilioSmsBackend(SmsBackend):
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)

        self.client = Client(self.config["sid"], self.config["token"])

    def send_sms(self, recipient: str, message:
                 str, sender: str = None) -> None:

        # Twilio accounts are associated with a phone number so we ignore
        # ``sender``
        self.client.messages.create(to=recipient, body=message,
                                    from_=self.config["phone_number"])


def register_backend(name: str, backend_class: Type[SmsBackend]) -> None:
    global _backends
    _backends[name] = backend_class


register_backend("console", ConsoleSmsBackend)
register_backend("kapow", KapowSmsBackend)
register_backend("twilio", TwilioSmsBackend)


def get_sms_backend(label: str, config: Dict[str, Any]) -> SmsBackend:
    global _backends
    try:
        backend_class = _backends[label]
    except KeyError:
        raise MissingBackendException(f"No backend '{label}' registered")

    return backend_class(config)
