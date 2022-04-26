#!/usr/bin/env python

"""
camcops_server/cc_modules/cc_sms.py

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

**Send SMS via supported backends**

"""

import logging
from typing import Any, Dict, Type

import requests
from twilio.rest import Client

from camcops_server.cc_modules.cc_constants import SmsBackendNames


_backends = {}
log = logging.getLogger(__name__)


class MissingBackendException(Exception):
    """
    SMS backend not configured.
    """

    pass


class SmsBackend:
    """
    Base class for sending SMS (text) messages.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Args:
            config:
                Dictionary of parameters specific to the backend in use.
        """
        self.config = config

    def send_sms(
        self, recipient: str, message: str, sender: str = None
    ) -> None:
        """
        Send an SMS message.

        Args:
            recipient:
                Recipient's phone number, as a string.
            message:
                Message contents.
            sender:
                Sender's phone number, if applicable.
        """
        raise NotImplementedError


class ConsoleSmsBackend(SmsBackend):
    """
    Debugging "backend" -- just prints the message to the server console.
    """

    PREFIX = "SMS debugging: would have sent message"

    @classmethod
    def make_msg(cls, recipient: str, message: str) -> str:
        """
        Returns the message sent to the console.
        """
        return f"{cls.PREFIX} {message!r} to {recipient}"

    def send_sms(
        self, recipient: str, message: str, sender: str = None
    ) -> None:
        log.info(self.make_msg(recipient, message))


class KapowSmsBackend(SmsBackend):
    """
    Send SMS messages via Kapow.
    """

    API_URL = "https://www.kapow.co.uk/scripts/sendsms.php"
    # Parameters must be in lower case; see _read_sms_config().
    PARAM_USERNAME = "username"
    PARAM_PASSWORD = "password"

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        assert (
            self.PARAM_USERNAME in config
        ), f"Kapow SMS: missing parameter {self.PARAM_USERNAME.upper()}"
        assert (
            self.PARAM_PASSWORD in config
        ), f"Kapow SMS: missing parameter {self.PARAM_PASSWORD.upper()}"

    def send_sms(
        self, recipient: str, message: str, sender: str = None
    ) -> None:
        data = {
            "username": self.config[self.PARAM_USERNAME],
            "password": self.config[self.PARAM_PASSWORD],
            "mobile": recipient,
            "sms": message,
        }
        requests.post(self.API_URL, data=data)


class TwilioSmsBackend(SmsBackend):
    """
    Send SMS messages via Twilio SMS.
    """

    # Parameters must be in lower case; see _read_sms_config().
    PARAM_SID = "sid"
    PARAM_TOKEN = "token"
    PARAM_FROM_PHONE_NUMBER = "from_phone_number"

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        assert (
            self.PARAM_SID in config
        ), f"Twilio SMS: missing parameter {self.PARAM_SID.upper()}"
        assert (
            self.PARAM_TOKEN in config
        ), f"Twilio SMS: missing parameter {self.PARAM_TOKEN.upper()}"
        assert self.PARAM_FROM_PHONE_NUMBER in config, (
            f"Twilio SMS: missing parameter "
            f"{self.PARAM_FROM_PHONE_NUMBER.upper()}"
        )
        self.client = Client(
            username=self.config[self.PARAM_SID],
            password=self.config[self.PARAM_TOKEN]
            # account_sid: defaults to username
        )

    def send_sms(
        self, recipient: str, message: str, sender: str = None
    ) -> None:
        # Twilio accounts are associated with a phone number so we ignore
        # ``sender``
        self.client.messages.create(
            to=recipient,
            body=message,
            from_=self.config[self.PARAM_FROM_PHONE_NUMBER],
        )


def register_backend(name: str, backend_class: Type[SmsBackend]) -> None:
    """
    Internal function to register an SMS backend by name.

    Args:
        name:
            Name of backend (e.g. as referred to in the config file).
        backend_class:
            Appropriate subclass of :class:`SmsBackend`.
    """
    global _backends
    _backends[name] = backend_class


register_backend(SmsBackendNames.CONSOLE, ConsoleSmsBackend)
register_backend(SmsBackendNames.KAPOW, KapowSmsBackend)
register_backend(SmsBackendNames.TWILIO, TwilioSmsBackend)


def get_sms_backend(label: str, config: Dict[str, Any]) -> SmsBackend:
    """
    Make an instance of an SMS backend by name, passing it appropriate
    backend-specific config options.
    """
    try:
        backend_class = _backends[label]
    except KeyError:
        raise MissingBackendException(f"No backend {label!r} registered")

    return backend_class(config)
