#!/usr/bin/env python

"""
camcops_server/cc_modules/tests/cc_sms_tests.py

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

"""

import logging
from unittest import mock, TestCase

from camcops_server.cc_modules.cc_sms import get_sms_backend

TEST_MESSAGE = "Test Message"
# https://www.ofcom.org.uk/phones-telecoms-and-internet/information-for-industry/numbering/numbers-for-drama  # noqa: E501
# 07700 900000 to 900999 reserved for TV and Radio drama purposes
TEST_RECIPIENT = "+447700900123"
TEST_SENDER = "+447700900456"


class KapowSmsBackendTests(TestCase):
    @mock.patch("camcops_server.cc_modules.cc_sms.requests.post")
    def test_sends_sms(self, mock_post) -> None:

        config = {"username": "testuser", "password": "testpass"}

        backend = get_sms_backend("kapow", config)
        backend.send_sms(TEST_RECIPIENT, TEST_MESSAGE)

        args, kwargs = mock_post.call_args

        self.assertEqual(args[0], "https://www.kapow.co.uk/scripts/sendsms.php")

        data = kwargs["data"]
        self.assertEqual(data["username"], "testuser")
        self.assertEqual(data["password"], "testpass")
        self.assertEqual(data["mobile"], TEST_RECIPIENT)
        self.assertEqual(data["sms"], TEST_MESSAGE)


class TwilioSmsBackendTests(TestCase):
    def test_backend_creates_client(self) -> None:
        config = {"sid": "testsid",
                  "token": "testtoken",
                  "phone_number": TEST_SENDER}

        backend = get_sms_backend("twilio", config)

        self.assertEqual(backend.client.username, "testsid")
        self.assertEqual(backend.client.password, "testtoken")

    def test_sends_sms(self) -> None:
        config = {"sid": "testsid",
                  "token": "testtoken",
                  "phone_number": TEST_SENDER}

        backend = get_sms_backend("twilio", config)

        with mock.patch.object(backend.client.messages,
                               "create") as mock_create:
            backend.send_sms(TEST_RECIPIENT, TEST_MESSAGE)

        args, kwargs = mock_create.call_args

        self.assertEqual(kwargs["to"], TEST_RECIPIENT)
        self.assertEqual(kwargs["from_"], TEST_SENDER)
        self.assertEqual(kwargs["body"], TEST_MESSAGE)


class ConsoleSmsBackendTests(TestCase):
    def test_sends_sms(self) -> None:

        config = {"username": "testuser", "password": "testpass"}

        backend = get_sms_backend("console", config)

        with self.assertLogs(level=logging.INFO) as logging_cm:
            backend.send_sms(TEST_RECIPIENT, TEST_MESSAGE)

        logger_name = "camcops_server.cc_modules.cc_sms"

        self.assertIn(f"INFO:{logger_name}", logging_cm.output[0])

        self.assertIn(
            f"Sent message '{TEST_MESSAGE}' to {TEST_RECIPIENT}",
            logging_cm.output[0]
        )