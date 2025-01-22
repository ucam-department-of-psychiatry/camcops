"""
camcops_server/cc_modules/tests/client_api_tests.py

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

"""

import json
import logging
import string
from typing import Dict

from cardinal_pythonlib.classes import class_attribute_names
from cardinal_pythonlib.convert import (
    base64_64format_encode,
    hex_xformat_encode,
)
from cardinal_pythonlib.nhs import generate_random_nhs_number
from cardinal_pythonlib.sql.literals import sql_quote_string
from cardinal_pythonlib.text import escape_newlines, unescape_newlines
from pendulum import DateTime as Pendulum, Duration, local, parse

from pyramid.response import Response

from camcops_server.cc_modules.cc_all_models import CLIENT_TABLE_MAP
from camcops_server.cc_modules.cc_client_api_core import (
    fail_server_error,
    fail_unsupported_operation,
    fail_user_error,
    ServerErrorException,
    TabletParam,
    UserErrorException,
)
from camcops_server.cc_modules.cc_convert import decode_values
from camcops_server.cc_modules.cc_proquint import uuid_from_proquint
from camcops_server.cc_modules.cc_taskindex import (
    PatientIdNumIndexEntry,
    TaskIndexEntry,
)
from camcops_server.cc_modules.cc_testfactories import (
    DeviceFactory,
    GroupFactory,
    NHSPatientIdNumFactory,
    PatientFactory,
    PatientTaskScheduleFactory,
    ServerCreatedNHSPatientIdNumFactory,
    ServerCreatedPatientFactory,
    TaskScheduleFactory,
    TaskScheduleItemFactory,
    UserFactory,
    UserGroupMembershipFactory,
)
from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase
from camcops_server.cc_modules.cc_user import User
from camcops_server.cc_modules.cc_version import MINIMUM_TABLET_VERSION
from camcops_server.cc_modules.cc_validators import (
    validate_alphanum_underscore,
)
from camcops_server.cc_modules.client_api import (
    client_api,
    FAILURE_CODE,
    get_or_create_single_user,
    make_single_user_mode_username,
    Operations,
    SUCCESS_CODE,
)
from camcops_server.tasks.tests.factories import BmiFactory

TEST_NHS_NUMBER = generate_random_nhs_number()


def get_reply_dict_from_response(response: Response) -> Dict[str, str]:
    """
    For unit testing: convert the text in a :class:`Response` back to a
    dictionary, so we can check it was correct.
    """
    txt = str(response)
    d = {}  # type: Dict[str, str]
    # Format is: "200 OK\r\n<other headers>\r\n\r\n<content>"
    # There's a blank line between the heads and the body.
    http_gap = "\r\n\r\n"
    camcops_linesplit = "\n"
    camcops_k_v_sep = ":"
    try:
        start_of_content = txt.index(http_gap) + len(http_gap)
        txt = txt[start_of_content:]
        for line in txt.split(camcops_linesplit):
            if not line:
                continue
            colon_pos = line.index(camcops_k_v_sep)
            key = line[:colon_pos]
            value = line[colon_pos + len(camcops_k_v_sep) :]
            key = key.strip()
            value = value.strip()
            d[key] = value
        return d
    except ValueError:
        return {}


class ClientApiTests(DemoRequestTestCase):
    def test_client_api_basics(self) -> None:
        with self.assertRaises(UserErrorException):
            fail_user_error("testmsg")
        with self.assertRaises(ServerErrorException):
            fail_server_error("testmsg")
        with self.assertRaises(UserErrorException):
            fail_unsupported_operation("duffop")

        # Encoding/decoding tests
        # data = bytearray("hello")
        data = b"hello"
        enc_b64data = base64_64format_encode(data)
        enc_hexdata = hex_xformat_encode(data)
        not_enc_1 = "X'012345'"
        not_enc_2 = "64'aGVsbG8='"
        teststring = """one, two, 3, 4.5, NULL, 'hello "hi
            with linebreak"', 'NULL', 'quote''s here', {b}, {h}, {s1}, {s2}"""
        sql_csv_testdict = {
            teststring.format(
                b=enc_b64data,
                h=enc_hexdata,
                s1=sql_quote_string(not_enc_1),
                s2=sql_quote_string(not_enc_2),
            ): [
                "one",
                "two",
                3,
                4.5,
                None,
                'hello "hi\n            with linebreak"',
                "NULL",
                "quote's here",
                data,
                data,
                not_enc_1,
                not_enc_2,
            ],
            "": [],
        }
        for k, v in sql_csv_testdict.items():
            r = decode_values(k)
            self.assertEqual(
                r,
                v,
                "Mismatch! Result: {r!s}\n"
                "Should have been: {v!s}\n"
                "Key was: {k!s}".format(r=r, v=v, k=k),
            )

        # Newline encoding/decodine
        ts2 = (
            "slash \\ newline \n ctrl_r \r special \\n other special \\r "
            "quote ' doublequote \" "
        )
        self.assertEqual(
            unescape_newlines(escape_newlines(ts2)),
            ts2,
            "Bug in escape_newlines() or unescape_newlines()",
        )

        # TODO: client_api.ClientApiTests: more tests here... ?

    def test_non_existent_table_rejected(self) -> None:
        device = DeviceFactory()

        self.req.fake_request_post_from_dict(
            {
                TabletParam.CAMCOPS_VERSION: MINIMUM_TABLET_VERSION,
                TabletParam.DEVICE: device.name,
                TabletParam.OPERATION: Operations.WHICH_KEYS_TO_SEND,
                TabletParam.TABLE: "nonexistent_table",
            }
        )
        response = client_api(self.req)
        d = get_reply_dict_from_response(response)
        self.assertEqual(d[TabletParam.SUCCESS], FAILURE_CODE)

    def test_client_api_validators(self) -> None:
        for x in class_attribute_names(Operations):
            try:
                validate_alphanum_underscore(x, self.req)
            except ValueError:
                self.fail(f"Operations.{x} fails validate_alphanum_underscore")


class RegisterPatientTests(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.device = DeviceFactory()

    def test_returns_patient_info(self) -> None:
        patient = ServerCreatedPatientFactory()
        idnum = ServerCreatedNHSPatientIdNumFactory(patient=patient)

        proquint = patient.uuid_as_proquint

        # For type checker
        assert proquint is not None
        assert self.device is not None

        self.req.fake_request_post_from_dict(
            {
                TabletParam.CAMCOPS_VERSION: MINIMUM_TABLET_VERSION,
                TabletParam.DEVICE: self.device.name,
                TabletParam.OPERATION: Operations.REGISTER_PATIENT,
                TabletParam.PATIENT_PROQUINT: proquint,
            }
        )
        response = client_api(self.req)
        reply_dict = get_reply_dict_from_response(response)

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

        patient_dict = json.loads(reply_dict[TabletParam.PATIENT_INFO])[0]

        self.assertEqual(patient_dict[TabletParam.SURNAME], patient.surname)
        self.assertEqual(patient_dict[TabletParam.FORENAME], patient.forename)
        self.assertEqual(patient_dict[TabletParam.SEX], patient.sex)
        self.assertEqual(
            patient_dict[TabletParam.DOB], patient.dob.isoformat()
        )
        self.assertEqual(patient_dict[TabletParam.ADDRESS], patient.address)
        self.assertEqual(patient_dict[TabletParam.GP], patient.gp)
        self.assertEqual(patient_dict[TabletParam.OTHER], patient.other)
        self.assertEqual(
            patient_dict[f"idnum{idnum.which_idnum}"], idnum.idnum_value
        )

    def test_creates_user(self) -> None:
        patient = ServerCreatedPatientFactory()
        idnum = ServerCreatedNHSPatientIdNumFactory(patient=patient)
        PatientIdNumIndexEntry.index_idnum(idnum, self.dbsession)

        proquint = patient.uuid_as_proquint

        # For type checker
        assert proquint is not None
        assert self.device.name is not None

        self.req.fake_request_post_from_dict(
            {
                TabletParam.CAMCOPS_VERSION: MINIMUM_TABLET_VERSION,
                TabletParam.DEVICE: self.device.name,
                TabletParam.OPERATION: Operations.REGISTER_PATIENT,
                TabletParam.PATIENT_PROQUINT: proquint,
            }
        )
        response = client_api(self.req)
        reply_dict = get_reply_dict_from_response(response)

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

        username = reply_dict[TabletParam.USER]
        self.assertEqual(
            username,
            make_single_user_mode_username(self.device.name, patient._pk),
        )
        password = reply_dict[TabletParam.PASSWORD]
        self.assertEqual(len(password), 32)

        valid_chars = string.ascii_letters + string.digits + string.punctuation
        self.assertTrue(all(c in valid_chars for c in password))

        user = (
            self.req.dbsession.query(User)
            .filter(User.username == username)
            .one_or_none()
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.upload_group, patient.group)
        self.assertTrue(user.auto_generated)
        self.assertTrue(user.may_register_devices)
        self.assertTrue(user.may_upload)

    def test_does_not_create_user_when_name_exists(self) -> None:
        patient = ServerCreatedPatientFactory()
        idnum = ServerCreatedNHSPatientIdNumFactory(patient=patient)
        PatientIdNumIndexEntry.index_idnum(idnum, self.dbsession)

        proquint = patient.uuid_as_proquint

        single_user_username = make_single_user_mode_username(
            self.device.name, patient._pk
        )

        user = UserFactory(
            username=single_user_username,
            password="old password",
            password__request=self.req,
        )

        self.req.fake_request_post_from_dict(
            {
                TabletParam.CAMCOPS_VERSION: MINIMUM_TABLET_VERSION,
                TabletParam.DEVICE: self.device.name,
                TabletParam.OPERATION: Operations.REGISTER_PATIENT,
                TabletParam.PATIENT_PROQUINT: proquint,
            }
        )
        response = client_api(self.req)
        reply_dict = get_reply_dict_from_response(response)

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

        username = reply_dict[TabletParam.USER]
        self.assertEqual(
            username,
            make_single_user_mode_username(self.device.name, patient._pk),
        )
        password = reply_dict[TabletParam.PASSWORD]
        self.assertEqual(len(password), 32)

        valid_chars = string.ascii_letters + string.digits + string.punctuation
        self.assertTrue(all(c in valid_chars for c in password))

        user = (
            self.req.dbsession.query(User)
            .filter(User.username == username)
            .one_or_none()
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.upload_group, patient.group)
        self.assertTrue(user.auto_generated)
        self.assertTrue(user.may_register_devices)
        self.assertTrue(user.may_upload)

    def test_raises_for_invalid_proquint(self) -> None:
        # For type checker
        assert self.device.name is not None

        self.req.fake_request_post_from_dict(
            {
                TabletParam.CAMCOPS_VERSION: MINIMUM_TABLET_VERSION,
                TabletParam.DEVICE: self.device.name,
                TabletParam.OPERATION: Operations.REGISTER_PATIENT,
                TabletParam.PATIENT_PROQUINT: "invalid",
            }
        )
        response = client_api(self.req)
        reply_dict = get_reply_dict_from_response(response)

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "no patient with access key 'invalid'",
            reply_dict[TabletParam.ERROR],
        )

    def test_raises_for_missing_valid_proquint(self) -> None:
        valid_proquint = "sazom-diliv-navol-hubot-mufur-mamuv-kojus-loluv-v"

        # Error message is same as for invalid proquint so make sure our
        # test proquint really is valid (should not raise)
        uuid_from_proquint(valid_proquint)

        assert self.device.name is not None

        self.req.fake_request_post_from_dict(
            {
                TabletParam.CAMCOPS_VERSION: MINIMUM_TABLET_VERSION,
                TabletParam.DEVICE: self.device.name,
                TabletParam.OPERATION: Operations.REGISTER_PATIENT,
                TabletParam.PATIENT_PROQUINT: valid_proquint,
            }
        )
        response = client_api(self.req)
        reply_dict = get_reply_dict_from_response(response)

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            f"no patient with access key '{valid_proquint}'",
            reply_dict[TabletParam.ERROR],
        )

    def test_raises_when_no_patient_idnums(self) -> None:
        # In theory this shouldn't be possible in normal operation as the
        # patient cannot be created without any idnums
        patient = ServerCreatedPatientFactory()

        proquint = patient.uuid_as_proquint
        self.req.fake_request_post_from_dict(
            {
                TabletParam.CAMCOPS_VERSION: MINIMUM_TABLET_VERSION,
                TabletParam.DEVICE: self.device.name,
                TabletParam.OPERATION: Operations.REGISTER_PATIENT,
                TabletParam.PATIENT_PROQUINT: proquint,
            }
        )

        response = client_api(self.req)
        reply_dict = get_reply_dict_from_response(response)
        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Patient has no ID numbers", reply_dict[TabletParam.ERROR]
        )

    def test_raises_when_patient_not_created_on_server(self) -> None:
        patient = PatientFactory()

        proquint = patient.uuid_as_proquint
        self.req.fake_request_post_from_dict(
            {
                TabletParam.CAMCOPS_VERSION: MINIMUM_TABLET_VERSION,
                TabletParam.DEVICE: self.device.name,
                TabletParam.OPERATION: Operations.REGISTER_PATIENT,
                TabletParam.PATIENT_PROQUINT: proquint,
            }
        )

        response = client_api(self.req)
        reply_dict = get_reply_dict_from_response(response)
        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            f"no patient with access key '{proquint}'",
            reply_dict[TabletParam.ERROR],
        )

    def test_returns_ip_use_flags(self) -> None:
        patient = ServerCreatedPatientFactory()
        idnum = ServerCreatedNHSPatientIdNumFactory(patient=patient)
        PatientIdNumIndexEntry.index_idnum(idnum, self.dbsession)
        ip_use = patient.group.ip_use

        proquint = patient.uuid_as_proquint

        # For type checker
        assert proquint is not None
        assert self.device.name is not None

        self.req.fake_request_post_from_dict(
            {
                TabletParam.CAMCOPS_VERSION: MINIMUM_TABLET_VERSION,
                TabletParam.DEVICE: self.device.name,
                TabletParam.OPERATION: Operations.REGISTER_PATIENT,
                TabletParam.PATIENT_PROQUINT: proquint,
            }
        )
        response = client_api(self.req)
        reply_dict = get_reply_dict_from_response(response)

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

        ip_use_info = json.loads(reply_dict[TabletParam.IP_USE_INFO])

        self.assertEqual(
            ip_use_info[TabletParam.IP_USE_COMMERCIAL], ip_use.commercial
        )
        self.assertEqual(
            ip_use_info[TabletParam.IP_USE_CLINICAL], ip_use.clinical
        )
        self.assertEqual(
            ip_use_info[TabletParam.IP_USE_EDUCATIONAL], ip_use.educational
        )
        self.assertEqual(
            ip_use_info[TabletParam.IP_USE_RESEARCH], ip_use.research
        )


class GetTaskSchedulesTests(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.group = GroupFactory()
        user = self.req._debugging_user = UserFactory(
            upload_group_id=self.group.id,
        )

        UserGroupMembershipFactory(
            user_id=user.id,
            group_id=self.group.id,
            may_register_devices=True,
        )

    def test_returns_task_schedules(self) -> None:
        schedule1 = TaskScheduleFactory(group=self.group)
        schedule2 = TaskScheduleFactory(group=self.group)

        TaskScheduleItemFactory(
            task_schedule=schedule1,
            task_table_name="phq9",
            due_from=Duration(days=0),
            due_by=Duration(days=7),
        )
        TaskScheduleItemFactory(
            task_schedule=schedule1,
            task_table_name="bmi",
            due_from=Duration(days=0),
            due_by=Duration(days=8),
        )
        TaskScheduleItemFactory(
            task_schedule=schedule1,
            task_table_name="phq9",
            due_from=Duration(days=30),
            due_by=Duration(days=37),
        )
        TaskScheduleItemFactory(
            task_schedule=schedule1,
            task_table_name="gmcpq",
            due_from=Duration(days=30),
            due_by=Duration(days=38),
        )

        # This is the patient originally created om the server
        server_patient = ServerCreatedPatientFactory(_group=self.group)
        server_idnum = ServerCreatedNHSPatientIdNumFactory(
            patient=server_patient
        )

        # This is the same patient but from the device
        patient = PatientFactory(_group=self.group)
        idnum = NHSPatientIdNumFactory(
            patient=patient,
            which_idnum=server_idnum.which_idnum,
            idnum_value=server_idnum.idnum_value,
        )
        PatientIdNumIndexEntry.index_idnum(idnum, self.dbsession)

        PatientTaskScheduleFactory(
            patient=server_patient,
            task_schedule=schedule1,
            settings={
                "bmi": {"bmi_key": "bmi_value"},
                "phq9": {"phq9_key": "phq9_value"},
            },
            start_datetime=local(2020, 7, 31),
        )

        PatientTaskScheduleFactory(
            patient=server_patient,
            task_schedule=schedule2,
        )

        bmi = BmiFactory(
            patient=patient,
            when_created=local(2020, 8, 1),
        )
        self.assertTrue(bmi.is_complete())

        TaskIndexEntry.index_task(
            bmi, self.dbsession, indexed_at_utc=Pendulum.utcnow()
        )

        proquint = server_patient.uuid_as_proquint

        # For type checker
        assert proquint is not None

        self.req.fake_request_post_from_dict(
            {
                TabletParam.CAMCOPS_VERSION: MINIMUM_TABLET_VERSION,
                TabletParam.DEVICE: patient._device.name,
                TabletParam.OPERATION: Operations.GET_TASK_SCHEDULES,
                TabletParam.PATIENT_PROQUINT: proquint,
            }
        )
        response = client_api(self.req)
        reply_dict = get_reply_dict_from_response(response)

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

        task_schedules = json.loads(reply_dict[TabletParam.TASK_SCHEDULES])

        self.assertEqual(len(task_schedules), 2)

        s = task_schedules[0]
        self.assertEqual(s[TabletParam.TASK_SCHEDULE_NAME], schedule1.name)

        schedule_items = s[TabletParam.TASK_SCHEDULE_ITEMS]
        self.assertEqual(len(schedule_items), 4)

        phq9_1_sched = schedule_items[0]
        self.assertEqual(phq9_1_sched[TabletParam.TABLE], "phq9")
        self.assertEqual(
            phq9_1_sched[TabletParam.SETTINGS], {"phq9_key": "phq9_value"}
        )
        self.assertEqual(
            parse(phq9_1_sched[TabletParam.DUE_FROM]), local(2020, 7, 31)
        )
        self.assertEqual(
            parse(phq9_1_sched[TabletParam.DUE_BY]), local(2020, 8, 7)
        )
        self.assertFalse(phq9_1_sched[TabletParam.COMPLETE])
        self.assertFalse(phq9_1_sched[TabletParam.ANONYMOUS])

        bmi_sched = schedule_items[1]
        self.assertEqual(bmi_sched[TabletParam.TABLE], "bmi")
        self.assertEqual(
            bmi_sched[TabletParam.SETTINGS], {"bmi_key": "bmi_value"}
        )
        self.assertEqual(
            parse(bmi_sched[TabletParam.DUE_FROM]), local(2020, 7, 31)
        )
        self.assertEqual(
            parse(bmi_sched[TabletParam.DUE_BY]), local(2020, 8, 8)
        )
        self.assertTrue(bmi_sched[TabletParam.COMPLETE])
        self.assertFalse(bmi_sched[TabletParam.ANONYMOUS])

        phq9_2_sched = schedule_items[2]
        self.assertEqual(phq9_2_sched[TabletParam.TABLE], "phq9")
        self.assertEqual(
            phq9_2_sched[TabletParam.SETTINGS], {"phq9_key": "phq9_value"}
        )
        self.assertEqual(
            parse(phq9_2_sched[TabletParam.DUE_FROM]), local(2020, 8, 30)
        )
        self.assertEqual(
            parse(phq9_2_sched[TabletParam.DUE_BY]), local(2020, 9, 6)
        )
        self.assertFalse(phq9_2_sched[TabletParam.COMPLETE])
        self.assertFalse(phq9_2_sched[TabletParam.ANONYMOUS])

        # GMCPQ
        gmcpq_sched = schedule_items[3]
        self.assertTrue(gmcpq_sched[TabletParam.ANONYMOUS])


class GetOrCreateSingleUserTests(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.patient = PatientFactory()
        self.req._debugging_user = UserFactory()

    def test_user_is_added_to_patient_group(self) -> None:
        user, _ = get_or_create_single_user(self.req, "test", self.patient)
        self.dbsession.flush()

        self.assertIn(self.patient.group.id, user.group_ids)

    def test_user_is_created_with_username(self) -> None:
        user, _ = get_or_create_single_user(self.req, "test", self.patient)
        self.dbsession.flush()

        self.assertEqual(user.username, "test")

    def test_user_is_assigned_password(self) -> None:
        _, password = get_or_create_single_user(self.req, "test", self.patient)
        self.dbsession.flush()

        valid_chars = string.ascii_letters + string.digits + string.punctuation
        self.assertTrue(all(c in valid_chars for c in password))

    def test_user_upload_group_set(self) -> None:
        user, _ = get_or_create_single_user(self.req, "test", self.patient)
        self.dbsession.flush()

        self.assertEqual(user.upload_group, self.patient.group)

    def test_user_auto_generated_flag_set(self) -> None:
        user, _ = get_or_create_single_user(self.req, "test", self.patient)
        self.dbsession.flush()

        self.assertTrue(user.auto_generated)

    def test_user_is_not_superuser(self) -> None:
        user, _ = get_or_create_single_user(self.req, "test", self.patient)
        self.dbsession.flush()

        self.assertFalse(user.superuser)

    def test_single_patient_pk_set(self) -> None:
        user, _ = get_or_create_single_user(self.req, "test", self.patient)
        self.dbsession.flush()

        self.assertEqual(user.single_patient_pk, self.patient._pk)

    def test_user_may_register_devices(self) -> None:
        user, _ = get_or_create_single_user(self.req, "test", self.patient)
        self.dbsession.flush()

        self.assertTrue(user.user_group_memberships[0].may_register_devices)

    def test_user_may_upload(self) -> None:
        user, _ = get_or_create_single_user(self.req, "test", self.patient)
        self.dbsession.flush()

        self.assertTrue(user.user_group_memberships[0].may_upload)

    def test_existing_user_is_updated(self) -> None:
        existing_user = UserFactory(username="test")

        user, _ = get_or_create_single_user(self.req, "test", self.patient)
        self.dbsession.flush()

        self.assertEqual(user, existing_user)


class UploadEntireDatabaseTests(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.group = GroupFactory()
        user = self.req._debugging_user = UserFactory(
            upload_group_id=self.group.id,
        )

        UserGroupMembershipFactory(
            user_id=user.id,
            group_id=self.group.id,
            may_upload=True,
        )
        self.device = DeviceFactory()

        self.post_dict = {
            TabletParam.CAMCOPS_VERSION: MINIMUM_TABLET_VERSION,
            TabletParam.DEVICE: self.device.name,
            TabletParam.OPERATION: Operations.UPLOAD_ENTIRE_DATABASE,
            TabletParam.FINALIZING: 1,
        }

    def test_fails_if_pknameinfo_is_not_a_dict(self) -> None:
        self.post_dict[TabletParam.PKNAMEINFO] = json.dumps(
            [{"key": "valid JSON but list not dict"}]
        )

        self.req.fake_request_post_from_dict(self.post_dict)
        with self.assertLogs(level=logging.WARN) as logging_cm:
            response = client_api(self.req)
            reply_dict = get_reply_dict_from_response(response)

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        logger_name = "camcops_server.cc_modules.client_api"

        self.assertIn(f"WARNING:{logger_name}", logging_cm.output[0])
        self.assertIn("PK name info JSON is not a dict", logging_cm.output[0])

    def test_fails_if_databasedata_is_not_a_dict(self) -> None:
        self.post_dict[TabletParam.PKNAMEINFO] = json.dumps(
            {"key": "valid JSON"}
        )
        self.post_dict[TabletParam.DBDATA] = json.dumps(
            [{"key": "valid JSON but list not dict"}]
        )

        self.req.fake_request_post_from_dict(self.post_dict)
        with self.assertLogs(level=logging.WARN) as logging_cm:
            response = client_api(self.req)
            reply_dict = get_reply_dict_from_response(response)

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        logger_name = "camcops_server.cc_modules.client_api"

        self.assertIn(f"WARNING:{logger_name}", logging_cm.output[0])
        self.assertIn("Database data JSON is not a dict", logging_cm.output[0])

    def test_fails_if_table_names_do_not_match(self) -> None:
        self.post_dict[TabletParam.PKNAMEINFO] = json.dumps(
            {"table1": "", "table2": "", "table3": ""}
        )
        self.post_dict[TabletParam.DBDATA] = json.dumps(
            {"table4": "", "table5": "", "table6": ""}
        )

        self.req.fake_request_post_from_dict(self.post_dict)
        with self.assertLogs(level=logging.WARN) as logging_cm:
            response = client_api(self.req)
            reply_dict = get_reply_dict_from_response(response)

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        logger_name = "camcops_server.cc_modules.client_api"

        self.assertIn(f"WARNING:{logger_name}", logging_cm.output[0])
        self.assertIn("Table names don't match", logging_cm.output[0])

    def test_fails_if_table_names_do_not_exist(self) -> None:
        self.post_dict[TabletParam.PKNAMEINFO] = json.dumps(
            {"table1": "", "table2": "", "table3": ""}
        )
        self.post_dict[TabletParam.DBDATA] = json.dumps(
            {"table1": "", "table2": "", "table3": ""}
        )

        self.req.fake_request_post_from_dict(self.post_dict)
        with self.assertLogs(level=logging.WARN) as logging_cm:
            response = client_api(self.req)
            reply_dict = get_reply_dict_from_response(response)

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        logger_name = "camcops_server.cc_modules.client_api"

        self.assertIn(f"WARNING:{logger_name}", logging_cm.output[0])
        self.assertIn(
            "Attempt to upload nonexistent tables", logging_cm.output[0]
        )

    def test_empty_upload_succeeds(self) -> None:
        pknameinfo = {key: "" for key in CLIENT_TABLE_MAP.keys()}
        dbdata = {key: "" for key in CLIENT_TABLE_MAP.keys()}

        self.post_dict[TabletParam.PKNAMEINFO] = json.dumps(pknameinfo)
        self.post_dict[TabletParam.DBDATA] = json.dumps(dbdata)

        self.req.fake_request_post_from_dict(self.post_dict)

        response = client_api(self.req)
        reply_dict = get_reply_dict_from_response(response)
        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )


class ValidatePatientsTests(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.group = GroupFactory()
        user = self.req._debugging_user = UserFactory(
            upload_group_id=self.group.id,
        )

        UserGroupMembershipFactory(
            user_id=user.id,
            group_id=self.group.id,
            may_upload=True,
        )
        self.device = DeviceFactory()

        self.post_dict = {
            TabletParam.CAMCOPS_VERSION: MINIMUM_TABLET_VERSION,
            TabletParam.DEVICE: self.device.name,
            TabletParam.OPERATION: Operations.VALIDATE_PATIENTS,
        }

    def test_fails_if_patient_info_is_not_a_list(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps({})

        self.req.fake_request_post_from_dict(self.post_dict)

        with self.assertLogs(level=logging.WARN) as logging_cm:
            response = client_api(self.req)
            reply_dict = get_reply_dict_from_response(response)

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        logger_name = "camcops_server.cc_modules.client_api"

        self.assertIn(f"WARNING:{logger_name}", logging_cm.output[0])
        self.assertIn("Top-level JSON is not a list", logging_cm.output[0])
