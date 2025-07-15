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
import string
from typing import Dict
from unittest import mock, TestCase

from cardinal_pythonlib.classes import class_attribute_names
from cardinal_pythonlib.convert import (
    base64_64format_encode,
    hex_xformat_encode,
)
from cardinal_pythonlib.nhs import generate_random_nhs_number
from cardinal_pythonlib.sql.literals import sql_quote_string
from cardinal_pythonlib.text import escape_newlines, unescape_newlines
from pendulum import DateTime as Pendulum, Duration, local, now, parse
from pyramid.response import Response
from semantic_version import Version
from sqlalchemy import select

from camcops_server.cc_modules.cc_all_models import CLIENT_TABLE_MAP
from camcops_server.cc_modules.cc_cache import cache_region_static
from camcops_server.cc_modules.cc_client_api_core import (
    AllowedTablesFieldNames,
    ExtraStringFieldNames,
    fail_server_error,
    fail_unsupported_operation,
    fail_user_error,
    ServerErrorException,
    TabletParam,
    UserErrorException,
)
from camcops_server.cc_modules.cc_constants import ERA_NOW
from camcops_server.cc_modules.cc_convert import decode_values
from camcops_server.cc_modules.cc_device import Device
from camcops_server.cc_modules.cc_dirtytables import DirtyTable
from camcops_server.cc_modules.cc_patientidnum import PatientIdNum
from camcops_server.cc_modules.cc_proquint import uuid_from_proquint
from camcops_server.cc_modules.cc_taskindex import (
    PatientIdNumIndexEntry,
    TaskIndexEntry,
)
from camcops_server.cc_modules.cc_testfactories import (
    DeviceFactory,
    DirtyTableFactory,
    Fake,
    GroupFactory,
    NHSIdNumDefinitionFactory,
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
from camcops_server.cc_modules.cc_version import (
    FIRST_TABLET_VER_WITH_EXPLICIT_PKNAME_IN_UPLOAD_TABLE,
)
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
from camcops_server.tasks import Bmi
from camcops_server.tasks.tests.factories import BmiFactory, Phq9Factory

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


class ExceptionTests(TestCase):
    def test_fail_user_error_raises(self) -> None:
        with self.assertRaises(UserErrorException):
            fail_user_error("testmsg")

    def test_fail_server_error_raises(self) -> None:
        with self.assertRaises(ServerErrorException):
            fail_server_error("testmsg")

    def test_fail_unsupported_operation_raises(self) -> None:
        with self.assertRaises(UserErrorException):
            fail_unsupported_operation("duffop")


class EncodeDecodeValuesTests(TestCase):
    def test_values_decoded_correctly(self) -> None:
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


class EscapeUnescapeNewlinesTests(TestCase):
    def test_escapes_and_unescapes_correctly(self) -> None:

        # Newline encoding/decodine
        test_string = (
            "slash \\ newline \n ctrl_r \r special \\n other special \\r "
            "quote ' doublequote \" "
        )
        self.assertEqual(
            unescape_newlines(escape_newlines(test_string)),
            test_string,
            "Bug in escape_newlines() or unescape_newlines()",
        )


class ValidateAlphanumUnderscoreTests(TestCase):
    def test_class_attribute_names_validate(self) -> None:
        for x in class_attribute_names(Operations):
            try:
                request = None
                validate_alphanum_underscore(x, request)
            except ValueError:
                self.fail(f"Operations.{x} fails validate_alphanum_underscore")


class ClientApiTestCase(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.group = GroupFactory()
        self.user = self.req._debugging_user = UserFactory(
            upload_group_id=self.group.id,
        )

        UserGroupMembershipFactory(
            user_id=self.user.id,
            group_id=self.group.id,
            may_upload=True,
            may_register_devices=True,
        )
        # Ensure the server device exists so that we don't get ID clashes
        Device.get_server_device(self.dbsession)
        self.device = DeviceFactory()

        self.post_dict = {
            TabletParam.CAMCOPS_VERSION: (
                FIRST_TABLET_VER_WITH_EXPLICIT_PKNAME_IN_UPLOAD_TABLE
            ),
            TabletParam.DEVICE: self.device.name,
        }
        # To prevent test failures when mocking cached functions
        cache_region_static.configure(
            backend="dogpile.cache.null", replace_existing_backend=True
        )

    def call_api(self) -> Dict[str, str]:
        self.req.fake_request_post_from_dict(self.post_dict)
        response = client_api(self.req)
        return get_reply_dict_from_response(response)


class MalformedRequestTests(ClientApiTestCase):
    def test_returns_400_bad_request(self) -> None:
        self.req.set_post_body(b"rubbish")
        response = client_api(self.req)

        self.assertEqual(response.status, "400 Bad Request")
        self.assertIn(b"Not a valid CamCOPS API request", response.body)


class OpRegisterPatientTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.patient = ServerCreatedPatientFactory()
        self.idnum = ServerCreatedNHSPatientIdNumFactory(patient=self.patient)
        PatientIdNumIndexEntry.index_idnum(self.idnum, self.dbsession)

        proquint = self.patient.uuid_as_proquint

        self.post_dict[TabletParam.OPERATION] = Operations.REGISTER_PATIENT
        self.post_dict[TabletParam.PATIENT_PROQUINT] = proquint

    def test_returns_patient_info(self) -> None:
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

        patient_dict = json.loads(reply_dict[TabletParam.PATIENT_INFO])[0]

        self.assertEqual(
            patient_dict[TabletParam.SURNAME], self.patient.surname
        )
        self.assertEqual(
            patient_dict[TabletParam.FORENAME], self.patient.forename
        )
        self.assertEqual(patient_dict[TabletParam.SEX], self.patient.sex)
        self.assertEqual(
            patient_dict[TabletParam.DOB], self.patient.dob.isoformat()
        )
        self.assertEqual(
            patient_dict[TabletParam.ADDRESS], self.patient.address
        )
        self.assertEqual(patient_dict[TabletParam.GP], self.patient.gp)
        self.assertEqual(patient_dict[TabletParam.OTHER], self.patient.other)
        self.assertEqual(
            patient_dict[f"idnum{self.idnum.which_idnum}"],
            self.idnum.idnum_value,
        )

    def test_creates_user(self) -> None:
        reply_dict = self.call_api()
        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

        username = reply_dict[TabletParam.USER]
        self.assertEqual(
            username,
            make_single_user_mode_username(self.device.name, self.patient._pk),
        )
        password = reply_dict[TabletParam.PASSWORD]
        self.assertEqual(len(password), 32)

        valid_chars = string.ascii_letters + string.digits + string.punctuation
        self.assertTrue(all(c in valid_chars for c in password))

        user = self.dbsession.execute(
            select(User).where(User.username == username)
        ).scalar_one()
        self.assertEqual(user.upload_group, self.patient.group)
        self.assertTrue(user.auto_generated)
        self.assertTrue(user.may_register_devices)
        self.assertTrue(user.may_upload)

    def test_does_not_create_user_when_name_exists(self) -> None:
        single_user_username = make_single_user_mode_username(
            self.device.name, self.patient._pk
        )

        UserFactory(
            username=single_user_username,
            password="old password",
            password__request=self.req,
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

        username = reply_dict[TabletParam.USER]
        self.assertEqual(
            username,
            make_single_user_mode_username(self.device.name, self.patient._pk),
        )
        password = reply_dict[TabletParam.PASSWORD]
        self.assertEqual(len(password), 32)

        valid_chars = string.ascii_letters + string.digits + string.punctuation
        self.assertTrue(all(c in valid_chars for c in password))

        user = self.dbsession.execute(
            select(User).where(User.username == username)
        ).scalar_one()
        self.assertEqual(user.upload_group, self.patient.group)
        self.assertTrue(user.auto_generated)
        self.assertTrue(user.may_register_devices)
        self.assertTrue(user.may_upload)

    def test_raises_for_invalid_proquint(self) -> None:
        self.post_dict[TabletParam.PATIENT_PROQUINT] = "invalid"
        reply_dict = self.call_api()
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

        self.post_dict[TabletParam.PATIENT_PROQUINT] = valid_proquint
        reply_dict = self.call_api()

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
        self.post_dict[TabletParam.PATIENT_PROQUINT] = proquint
        reply_dict = self.call_api()
        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Patient has no ID numbers", reply_dict[TabletParam.ERROR]
        )

    def test_raises_when_patient_not_created_on_server(self) -> None:
        patient = PatientFactory()

        proquint = patient.uuid_as_proquint
        self.post_dict[TabletParam.PATIENT_PROQUINT] = proquint
        reply_dict = self.call_api()
        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            f"no patient with access key '{proquint}'",
            reply_dict[TabletParam.ERROR],
        )

    def test_returns_ip_use_flags(self) -> None:
        ip_use = self.patient.group.ip_use

        reply_dict = self.call_api()

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


class OpGetTaskSchedulesTests(ClientApiTestCase):
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

        self.post_dict[TabletParam.OPERATION] = Operations.GET_TASK_SCHEDULES
        self.post_dict[TabletParam.PATIENT_PROQUINT] = proquint

        reply_dict = self.call_api()

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


class OpGetOrCreateSingleUserTests(DemoRequestTestCase):
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


class OpUploadEntireDatabaseTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.post_dict[TabletParam.OPERATION] = (
            Operations.UPLOAD_ENTIRE_DATABASE
        )
        self.post_dict[TabletParam.FINALIZING] = 1

    def test_fails_if_pknameinfo_is_not_a_dict(self) -> None:
        self.post_dict[TabletParam.PKNAMEINFO] = json.dumps(
            [{"key": "valid JSON but list not dict"}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "PK name info JSON is not a dict", reply_dict[TabletParam.ERROR]
        )

    def test_fails_if_databasedata_is_not_a_dict(self) -> None:
        self.post_dict[TabletParam.PKNAMEINFO] = json.dumps(
            {"key": "valid JSON"}
        )
        self.post_dict[TabletParam.DBDATA] = json.dumps(
            [{"key": "valid JSON but list not dict"}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Database data JSON is not a dict", reply_dict[TabletParam.ERROR]
        )

    def test_fails_if_table_names_do_not_match(self) -> None:
        self.post_dict[TabletParam.PKNAMEINFO] = json.dumps(
            {"table1": "", "table2": "", "table3": ""}
        )
        self.post_dict[TabletParam.DBDATA] = json.dumps(
            {"table4": "", "table5": "", "table6": ""}
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("Table names don't match", reply_dict[TabletParam.ERROR])

    def test_fails_if_table_names_do_not_exist(self) -> None:
        self.post_dict[TabletParam.PKNAMEINFO] = json.dumps(
            {"table1": "", "table2": "", "table3": ""}
        )
        self.post_dict[TabletParam.DBDATA] = json.dumps(
            {"table1": "", "table2": "", "table3": ""}
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Attempt to upload nonexistent tables",
            reply_dict[TabletParam.ERROR],
        )

    def test_empty_upload_succeeds(self) -> None:
        pknameinfo = {key: "" for key in CLIENT_TABLE_MAP.keys()}
        dbdata = {key: "" for key in CLIENT_TABLE_MAP.keys()}

        self.post_dict[TabletParam.PKNAMEINFO] = json.dumps(pknameinfo)
        self.post_dict[TabletParam.DBDATA] = json.dumps(dbdata)

        reply_dict = self.call_api()
        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

    def test_upload_row_succeeds(self) -> None:
        now_utc_string = now("UTC").isoformat()
        patient = PatientFactory(_device=self.device)
        bmi_data = {
            "id": "1",
            "height_m": "1.83",
            "mass_kg": "67",
            "when_created": now_utc_string,
            "when_last_modified": now_utc_string,
            "_move_off_tablet": "1",
            "patient_id": str(patient.id),
        }

        pknameinfo = {"bmi": "id"}
        dbdata = {"bmi": [bmi_data]}

        self.post_dict[TabletParam.PKNAMEINFO] = json.dumps(pknameinfo)
        self.post_dict[TabletParam.DBDATA] = json.dumps(dbdata)

        reply_dict = self.call_api()
        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        bmi = self.dbsession.execute(
            select(Bmi).where(Bmi.id == 1)
        ).scalar_one()

        self.assertAlmostEqual(bmi.height_m, 1.83)
        self.assertAlmostEqual(bmi.mass_kg, 67)

    def test_upload_row_fails_with_no_pkname(self) -> None:
        now_utc_string = now("UTC").isoformat()
        patient = PatientFactory(_device=self.device)
        bmi_data = {
            "id": "1",
            "height_m": "1.83",
            "mass_kg": "67",
            "when_created": now_utc_string,
            "when_last_modified": now_utc_string,
            "_move_off_tablet": "1",
            "patient_id": str(patient.id),
        }

        pknameinfo = {"bmi": ""}
        dbdata = {"bmi": [bmi_data]}

        self.post_dict[TabletParam.PKNAMEINFO] = json.dumps(pknameinfo)
        self.post_dict[TabletParam.DBDATA] = json.dumps(dbdata)

        reply_dict = self.call_api()
        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Client-side PK name not specified by client for non-empty table",
            reply_dict[TabletParam.ERROR],
            msg=reply_dict,
        )

    def test_empty_upload_flags_existing_for_deletion(self) -> None:
        patient = PatientFactory(_device=self.device)
        bmi = BmiFactory(
            patient=patient,
            _removal_pending=True,
            _era=ERA_NOW,
            _current=True,
        )

        pknameinfo = {key: "" for key in CLIENT_TABLE_MAP.keys()}
        dbdata = {key: "" for key in CLIENT_TABLE_MAP.keys()}

        self.post_dict[TabletParam.PKNAMEINFO] = json.dumps(pknameinfo)
        self.post_dict[TabletParam.DBDATA] = json.dumps(dbdata)

        reply_dict = self.call_api()
        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.dbsession.commit()

        self.assertFalse(bmi._current)
        self.assertFalse(bmi._removal_pending)
        self.assertTrue(bmi._removing_user_id, self.user.id)
        self.assertIsNotNone(bmi._when_removed_exact)
        self.assertIsNotNone(bmi._when_removed_batch_utc)


class OpValidatePatientsTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.post_dict[TabletParam.OPERATION] = Operations.VALIDATE_PATIENTS

    def test_fails_if_patient_info_is_not_a_list(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps({})

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Top-level JSON is not a list", reply_dict[TabletParam.ERROR]
        )

    def test_succeeds_for_empty_list(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps([])

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

    def test_fails_if_one_patients_info_is_not_a_dict(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps([[]])

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Patient JSON is not a dict", reply_dict[TabletParam.ERROR]
        )

    def test_fails_if_one_patients_info_is_empty(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps([{}])

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("Patient JSON is empty", reply_dict[TabletParam.ERROR])

    def test_fails_if_forename_is_not_a_string(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{TabletParam.FORENAME: 1}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("non-string: 1", reply_dict[TabletParam.ERROR])

    def test_fails_if_surname_is_not_a_string(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{TabletParam.SURNAME: 2}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("non-string: 2", reply_dict[TabletParam.ERROR])

    def test_fails_if_sex_is_not_valid(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{TabletParam.SEX: "Q"}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("Bad sex value: 'Q'", reply_dict[TabletParam.ERROR])

    def test_fails_if_dob_is_not_a_string(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{TabletParam.DOB: 3}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("non-string: 3", reply_dict[TabletParam.ERROR])

    def test_fails_if_dob_fails_to_parse(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{TabletParam.DOB: "Yesterday"}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Invalid DOB: 'Yesterday'", reply_dict[TabletParam.ERROR]
        )

    def test_fails_if_email_is_not_a_string(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{TabletParam.EMAIL: 4}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("non-string: 4", reply_dict[TabletParam.ERROR])

    def test_fails_if_email_invalid(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{TabletParam.EMAIL: "email"}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Bad e-mail address: 'email'", reply_dict[TabletParam.ERROR]
        )

    def test_fails_if_address_is_not_a_string(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{TabletParam.ADDRESS: 5}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("non-string: 5", reply_dict[TabletParam.ERROR])

    def test_fails_if_gp_is_not_a_string(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{TabletParam.GP: 6}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("non-string: 6", reply_dict[TabletParam.ERROR])

    def test_fails_if_other_is_not_a_string(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{TabletParam.OTHER: 7}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("non-string: 7", reply_dict[TabletParam.ERROR])

    def test_fails_if_which_idnum_is_not_an_int(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{f"{TabletParam.IDNUM_PREFIX}foo": 12345}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Bad idnum key: 'idnumfoo'", reply_dict[TabletParam.ERROR]
        )

    def test_fails_if_which_idnum_is_not_valid(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{f"{TabletParam.IDNUM_PREFIX}2": 12345}]
        )

        self.req.valid_which_idnums = [1]

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("Bad ID number type: 2", reply_dict[TabletParam.ERROR])

    def test_fails_if_which_idnum_already_seen(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [
                {
                    f"{TabletParam.IDNUM_PREFIX}1": 12345,
                    f"{TabletParam.IDNUM_PREFIX}01": 12345,
                }
            ]
        )

        self.req.valid_which_idnums = [1]

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "More than one ID number supplied for ID number type 1",
            reply_dict[TabletParam.ERROR],
        )

    def test_fails_if_idnum_not_an_int(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{f"{TabletParam.IDNUM_PREFIX}1": "foo"}]
        )

        self.req.valid_which_idnums = [1]

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Bad ID number value: 'foo'", reply_dict[TabletParam.ERROR]
        )

    def test_fails_if_idref_invalid(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{f"{TabletParam.IDNUM_PREFIX}1": 0}]
        )

        self.req.valid_which_idnums = [1]

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Bad ID number: IdNumReference(idnum_value=0, which_idnum=1)",
            reply_dict[TabletParam.ERROR],
        )

    def test_fails_if_finalizing_is_not_a_bool(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{TabletParam.FINALIZING: 123}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Bad 'finalizing' value: 123", reply_dict[TabletParam.ERROR]
        )

    def test_fails_for_unknown_json_key(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{"foobar": 123}]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Unknown JSON key: 'foobar'", reply_dict[TabletParam.ERROR]
        )

    def test_fails_for_missing_finalizing_key(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [{TabletParam.SURNAME: "Valid"}]  # Needs to have something
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Missing 'finalizing' JSON key", reply_dict[TabletParam.ERROR]
        )

    def test_fails_when_candidate_invalid_for_group(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [
                {
                    TabletParam.SURNAME: "Valid",  # Needs to have something
                    TabletParam.FINALIZING: True,
                }
            ]
        )

        mock_invalid = mock.Mock(return_value=(False, "Mock reason"))

        with mock.patch.multiple(
            "camcops_server.cc_modules.client_api",
            is_candidate_patient_valid_for_group=mock_invalid,
        ):
            reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("Invalid patient", reply_dict[TabletParam.ERROR])
        self.assertIn("Mock reason", reply_dict[TabletParam.ERROR])

    def test_fails_when_candidate_invalid_for_restricted_user(self) -> None:
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [
                {
                    TabletParam.SURNAME: "Valid",  # Needs to have something
                    TabletParam.FINALIZING: True,
                }
            ]
        )

        mock_valid = mock.Mock(return_value=(True, ""))
        mock_invalid = mock.Mock(return_value=(False, "Mock reason"))

        with mock.patch.multiple(
            "camcops_server.cc_modules.client_api",
            is_candidate_patient_valid_for_group=mock_valid,
            is_candidate_patient_valid_for_restricted_user=mock_invalid,
        ):
            reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("Invalid patient", reply_dict[TabletParam.ERROR])
        self.assertIn("Mock reason", reply_dict[TabletParam.ERROR])

    def test_succeeds_for_valid_patient(self) -> None:
        sex = Fake.en_gb.sex()
        dob = Fake.en_gb.consistent_date_of_birth().isoformat()

        # All values set for maximum test coverage
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [
                {
                    TabletParam.FORENAME: Fake.en_gb.forename(sex),
                    TabletParam.SURNAME: Fake.en_gb.last_name(),
                    TabletParam.SEX: sex,
                    TabletParam.DOB: dob,
                    TabletParam.ADDRESS: Fake.en_gb.address(),
                    TabletParam.GP: Fake.en_gb.name(),
                    TabletParam.OTHER: Fake.en_us.paragraph(),
                    TabletParam.EMAIL: Fake.en_gb.email(),
                    TabletParam.FINALIZING: True,
                }
            ]
        )

        mock_valid = mock.Mock(return_value=(True, ""))

        with mock.patch.multiple(
            "camcops_server.cc_modules.client_api",
            is_candidate_patient_valid_for_group=mock_valid,
            is_candidate_patient_valid_for_restricted_user=mock_valid,
        ):
            reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

    def test_succeeds_for_empty_dob(self) -> None:
        # All values set for maximum test coverage
        self.post_dict[TabletParam.PATIENT_INFO] = json.dumps(
            [
                {
                    TabletParam.DOB: "",
                    TabletParam.FINALIZING: True,
                }
            ]
        )

        mock_valid = mock.Mock(return_value=(True, ""))

        with mock.patch.multiple(
            "camcops_server.cc_modules.client_api",
            is_candidate_patient_valid_for_group=mock_valid,
            is_candidate_patient_valid_for_restricted_user=mock_valid,
        ):
            reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )


class OpWhichKeysToSendTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.post_dict[TabletParam.OPERATION] = Operations.WHICH_KEYS_TO_SEND
        self.post_dict[TabletParam.PKNAME] = "id"

    def test_non_existent_table_rejected(self) -> None:
        self.post_dict[TabletParam.TABLE] = "nonexistent_table"
        reply_dict = self.call_api()
        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict[TabletParam.ERROR],
            "Invalid client table name: nonexistent_table",
            msg=reply_dict,
        )

    def test_table_rejected_if_client_too_old(self) -> None:
        self.post_dict[TabletParam.CAMCOPS_VERSION] = "2.0.0"
        self.post_dict[TabletParam.TABLE] = "table_1"
        mock_tables = mock.Mock(
            return_value={
                "table_1": Version("2.0.1"),
            }
        )
        mock_client_table_map = {"table_1": mock.Mock()}
        with mock.patch.multiple(
            "camcops_server.cc_modules.client_api",
            all_tables_with_min_client_version=mock_tables,
            CLIENT_TABLE_MAP=mock_client_table_map,
        ):
            reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Client CamCOPS version 2.0.0 is less than the version (2.0.1)",
            reply_dict[TabletParam.ERROR],
            msg=reply_dict,
        )

    def test_fails_for_pk_value_date_count_mismatch(self) -> None:
        self.post_dict[TabletParam.TABLE] = "bmi"
        self.post_dict[TabletParam.PKVALUES] = "1"
        self.post_dict[TabletParam.DATEVALUES] = ""

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("Number of PK values", reply_dict[TabletParam.ERROR])
        self.assertIn(
            "doesn't match number of dates", reply_dict[TabletParam.ERROR]
        )

    def test_fails_for_pk_value_move_off_tablet_count_mismatch(self) -> None:
        self.post_dict[TabletParam.TABLE] = "bmi"
        self.post_dict[TabletParam.PKVALUES] = "1,2"
        self.post_dict[TabletParam.DATEVALUES] = "2025-01-23,2025-01-24"
        self.post_dict[TabletParam.MOVE_OFF_TABLET_VALUES] = "1"

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Number of move-off-tablet values", reply_dict[TabletParam.ERROR]
        )
        self.assertIn(
            "doesn't match number of PKs", reply_dict[TabletParam.ERROR]
        )

    def test_fails_for_non_integer_client_pk(self) -> None:
        self.post_dict[TabletParam.TABLE] = "bmi"
        self.post_dict[TabletParam.PKVALUES] = "1,strawberry"
        self.post_dict[TabletParam.DATEVALUES] = "2025-01-23,2025-01-24"
        self.post_dict[TabletParam.MOVE_OFF_TABLET_VALUES] = "1,1"

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Bad (non-integer) client PK", reply_dict[TabletParam.ERROR]
        )

    def test_fails_for_missing_date_time(self) -> None:
        self.post_dict[TabletParam.TABLE] = "bmi"
        self.post_dict[TabletParam.PKVALUES] = "1"
        self.post_dict[TabletParam.DATEVALUES] = "null"
        self.post_dict[TabletParam.MOVE_OFF_TABLET_VALUES] = "1"

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("Missing date/time", reply_dict[TabletParam.ERROR])

    def test_fails_for_bad_date_time(self) -> None:
        self.post_dict[TabletParam.TABLE] = "bmi"
        self.post_dict[TabletParam.PKVALUES] = "1"
        self.post_dict[TabletParam.DATEVALUES] = "Tuesday"
        self.post_dict[TabletParam.MOVE_OFF_TABLET_VALUES] = "1"

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn("Bad date/time", reply_dict[TabletParam.ERROR])

    def test_succeeds_for_valid_values(self) -> None:
        self.post_dict[TabletParam.TABLE] = "bmi"
        self.post_dict[TabletParam.PKVALUES] = "123"
        self.post_dict[TabletParam.DATEVALUES] = "2025-01-23"
        self.post_dict[TabletParam.MOVE_OFF_TABLET_VALUES] = "1"

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(reply_dict[TabletParam.RESULT], "123", msg=reply_dict)

    def test_succeeds_for_existing_record(self) -> None:
        self.post_dict[TabletParam.TABLE] = "bmi"
        patient = PatientFactory(_device=self.device)
        bmi = BmiFactory(id=123, patient=patient, _era=ERA_NOW)

        self.post_dict[TabletParam.PKVALUES] = f"{bmi.id}"
        self.post_dict[TabletParam.DATEVALUES] = "2025-01-23"
        self.post_dict[TabletParam.MOVE_OFF_TABLET_VALUES] = "1"

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(reply_dict[TabletParam.RESULT], "123", msg=reply_dict)

    def test_succeeds_for_unmodified_record_marked_for_preservation(
        self,
    ) -> None:
        time_now = local(2025, 1, 26)

        patient = PatientFactory(_device=self.device)
        bmi = BmiFactory(
            id=123,
            patient=patient,
            _era=ERA_NOW,
            when_last_modified=time_now,
            _move_off_tablet=False,
        )

        self.post_dict[TabletParam.TABLE] = "bmi"
        self.post_dict[TabletParam.PKVALUES] = f"{bmi.id}"
        self.post_dict[TabletParam.DATEVALUES] = time_now.isoformat()
        self.post_dict[TabletParam.MOVE_OFF_TABLET_VALUES] = "1"

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(reply_dict[TabletParam.RESULT], "", msg=reply_dict)
        self.dbsession.commit()

        self.assertTrue(bmi._move_off_tablet)


class OpDeleteWhereKeyNotTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.post_dict[TabletParam.OPERATION] = Operations.DELETE_WHERE_KEY_NOT
        self.post_dict[TabletParam.TABLE] = "bmi"
        self.post_dict[TabletParam.PKNAME] = "id"

    def test_records_not_specified_marked_for_removal(self) -> None:
        patient = PatientFactory(_device=self.device)
        bmis = BmiFactory.create_batch(
            3,
            patient=patient,
            _removal_pending=False,
            _era=ERA_NOW,
        )

        self.post_dict[TabletParam.PKVALUES] = f"{bmis[0].id},{bmis[1].id}"
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict[TabletParam.RESULT], "Trimmed", msg=reply_dict
        )

        self.dbsession.commit()

        self.assertFalse(bmis[0]._removal_pending)
        self.assertFalse(bmis[1]._removal_pending)
        self.assertTrue(bmis[2]._removal_pending)


class OpStartPreservationTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.post_dict[TabletParam.OPERATION] = Operations.START_PRESERVATION
        self.post_dict[TabletParam.TABLE] = "bmi"
        self.post_dict[TabletParam.PKNAME] = "id"

    def test_device_currently_preserving(self) -> None:
        self.assertFalse(self.device.currently_preserving)

        patient = PatientFactory(_device=self.device)
        bmi = BmiFactory(
            id=123,
            patient=patient,
            _era=ERA_NOW,
        )
        self.post_dict[TabletParam.PKVALUES] = f"{bmi.id}"
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict[TabletParam.RESULT], "STARTPRESERVATION", msg=reply_dict
        )

        self.dbsession.commit()
        self.assertTrue(self.device.currently_preserving)

    def test_marks_table_dirty(self) -> None:
        self.assertIsNone(
            self.dbsession.execute(
                select(DirtyTable).where(DirtyTable.tablename == "bmi")
            ).scalar_one_or_none()
        )

        patient = PatientFactory(_device=self.device)
        bmi = BmiFactory(
            id=123,
            patient=patient,
            _era=ERA_NOW,
        )
        self.post_dict[TabletParam.PKVALUES] = f"{bmi.id}"
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict[TabletParam.RESULT], "STARTPRESERVATION", msg=reply_dict
        )

        self.dbsession.commit()

        self.assertIsNotNone(
            self.dbsession.execute(
                select(DirtyTable).where(DirtyTable.tablename == "bmi")
            ).scalar_one_or_none()
        )


class OpUploadEmptyTablesTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.post_dict[TabletParam.OPERATION] = Operations.UPLOAD_EMPTY_TABLES
        self.post_dict[TabletParam.TABLES] = "bmi,phq9"

    def test_all_records_flagged_as_deleted(self) -> None:
        patient = PatientFactory(_device=self.device)
        bmi = BmiFactory(
            patient=patient,
            _era=ERA_NOW,
            _current=True,
            _removal_pending=False,
        )
        phq9 = Phq9Factory(
            patient=patient,
            _era=ERA_NOW,
            _current=True,
            _removal_pending=False,
        )
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict[TabletParam.RESULT],
            "UPLOAD-EMPTY-TABLES",
            msg=reply_dict,
        )
        self.dbsession.commit()

        self.assertTrue(bmi._removal_pending)
        self.assertTrue(phq9._removal_pending)

    def test_tables_marked_dirty_if_records_in_current_era(self) -> None:
        self.assertIsNone(
            self.dbsession.execute(
                select(DirtyTable).where(DirtyTable.tablename == "bmi")
            ).scalar_one_or_none()
        )
        self.assertIsNone(
            self.dbsession.execute(
                select(DirtyTable).where(DirtyTable.tablename == "phq9")
            ).scalar_one_or_none()
        )

        patient = PatientFactory(_device=self.device)
        BmiFactory(
            patient=patient,
            _era=ERA_NOW,
            _current=True,
        )
        Phq9Factory(
            patient=patient,
            _era=ERA_NOW,
            _current=True,
        )
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.dbsession.commit()
        self.assertIsNotNone(
            self.dbsession.execute(
                select(DirtyTable).where(DirtyTable.tablename == "bmi")
            ).scalar_one_or_none()
        )
        self.assertIsNotNone(
            self.dbsession.execute(
                select(DirtyTable).where(DirtyTable.tablename == "phq9")
            ).scalar_one_or_none()
        )

    def test_tables_marked_clean_if_no_records_in_current_era(self) -> None:
        DirtyTableFactory(tablename="bmi", device_id=self.device.id)
        DirtyTableFactory(tablename="phq9", device_id=self.device.id)
        self.device.currently_preserving = True
        self.device.ongoing_upload_batch_utc = now("UTC")
        self.dbsession.add(self.device)
        self.dbsession.commit()

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.dbsession.commit()
        self.assertIsNone(
            self.dbsession.execute(
                select(DirtyTable).where(DirtyTable.tablename == "bmi")
            ).scalar_one_or_none()
        )
        self.assertIsNone(
            self.dbsession.execute(
                select(DirtyTable).where(DirtyTable.tablename == "phq9")
            ).scalar_one_or_none()
        )


class OpUploadRecordTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.post_dict[TabletParam.OPERATION] = Operations.UPLOAD_RECORD
        self.post_dict[TabletParam.PKNAME] = "id"

    def test_upload_inserts_record(self) -> None:
        now_utc_string = now("UTC").isoformat()
        patient = PatientFactory(_device=self.device)

        self.post_dict[TabletParam.TABLE] = "bmi"
        self.post_dict[TabletParam.PKVALUES] = "1"
        self.post_dict[TabletParam.FIELDS] = ",".join(
            [
                "id",
                "height_m",
                "mass_kg",
                "when_created",
                "when_last_modified",
                "_move_off_tablet",
                "patient_id",
            ]
        )
        self.post_dict[TabletParam.VALUES] = ",".join(
            [
                "1",
                "1.83",
                "67",
                now_utc_string,
                now_utc_string,
                "1",
                str(patient.id),
            ]
        )
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict[TabletParam.RESULT],
            "UPLOAD-INSERT",
            msg=reply_dict,
        )
        bmi = self.dbsession.execute(select(Bmi)).scalar_one_or_none()
        self.assertIsNotNone(bmi)

        self.assertAlmostEqual(bmi.height_m, 1.83)
        self.assertAlmostEqual(bmi.mass_kg, 67)

    def test_upload_updates_record(self) -> None:
        now_utc_string = now("UTC").isoformat()
        patient = PatientFactory(_device=self.device)
        bmi = BmiFactory(
            patient=patient,
            _era=ERA_NOW,
            height_m=1.8,
            mass_kg=70,
        )

        self.post_dict[TabletParam.TABLE] = "bmi"
        self.post_dict[TabletParam.PKVALUES] = "1"
        self.post_dict[TabletParam.FIELDS] = ",".join(
            [
                "id",
                "height_m",
                "mass_kg",
                "when_created",
                "when_last_modified",
                "_move_off_tablet",
                "patient_id",
            ]
        )
        self.post_dict[TabletParam.VALUES] = ",".join(
            [
                str(bmi.id),
                "1.83",
                "67",
                now_utc_string,
                now_utc_string,
                "1",
                str(patient.id),
            ]
        )
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict[TabletParam.RESULT],
            "UPLOAD-UPDATE",
            msg=reply_dict,
        )
        new_bmi = self.dbsession.execute(
            select(Bmi).where(Bmi._predecessor_pk == bmi._pk)
        ).scalar_one_or_none()
        self.assertIsNotNone(new_bmi)

        self.assertAlmostEqual(new_bmi.height_m, 1.83)
        self.assertAlmostEqual(new_bmi.mass_kg, 67)

    def test_fails_if_field_is_reserved(self) -> None:
        self.post_dict[TabletParam.TABLE] = "bmi"
        self.post_dict[TabletParam.PKVALUES] = "1"
        self.post_dict[TabletParam.FIELDS] = ",".join(
            [
                "id",
                "_current",
            ]
        )
        self.post_dict[TabletParam.VALUES] = ",".join(
            [
                "1",
                "0",
            ]
        )
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Reserved field name for table",
            reply_dict[TabletParam.ERROR],
            msg=reply_dict,
        )

    def test_fails_if_field_does_not_exist(self) -> None:
        self.post_dict[TabletParam.TABLE] = "bmi"
        self.post_dict[TabletParam.PKVALUES] = "1"
        self.post_dict[TabletParam.FIELDS] = ",".join(
            [
                "id",
                "nonsense",
            ]
        )
        self.post_dict[TabletParam.VALUES] = ",".join(
            [
                "1",
                "0",
            ]
        )
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "Invalid field name for table",
            reply_dict[TabletParam.ERROR],
            msg=reply_dict,
        )

    def test_upload_inserts_patient_idnum_record(self) -> None:
        now_utc_string = now("UTC").isoformat()
        iddef = NHSIdNumDefinitionFactory()
        patient = PatientFactory(_device=self.device)

        self.post_dict[TabletParam.TABLE] = "patient_idnum"
        self.post_dict[TabletParam.PKVALUES] = "1"
        self.post_dict[TabletParam.FIELDS] = ",".join(
            [
                "id",
                "which_idnum",
                "idnum_value",
                "when_last_modified",
                "_move_off_tablet",
                "patient_id",
            ]
        )
        nhs_number = Fake.en_gb.nhs_number()
        self.post_dict[TabletParam.VALUES] = ",".join(
            [
                "1",
                str(iddef.which_idnum),
                str(nhs_number),
                now_utc_string,
                "1",
                str(patient.id),
            ]
        )
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict[TabletParam.RESULT],
            "UPLOAD-INSERT",
            msg=reply_dict,
        )
        patient_idnum = self.dbsession.execute(
            select(PatientIdNum)
        ).scalar_one_or_none()
        self.assertIsNotNone(patient_idnum)

        self.assertEqual(patient_idnum.which_idnum, iddef.which_idnum)
        self.assertEqual(patient_idnum.idnum_value, nhs_number)

    def test_fails_if_patient_idnum_type_unknown(self) -> None:
        now_utc_string = now("UTC").isoformat()
        patient = PatientFactory(_device=self.device)

        self.post_dict[TabletParam.TABLE] = "patient_idnum"
        self.post_dict[TabletParam.PKVALUES] = "1"
        self.post_dict[TabletParam.FIELDS] = ",".join(
            [
                "id",
                "which_idnum",
                "idnum_value",
                "when_last_modified",
                "_move_off_tablet",
                "patient_id",
            ]
        )
        nhs_number = Fake.en_gb.nhs_number()
        self.post_dict[TabletParam.VALUES] = ",".join(
            [
                "1",
                "1",
                str(nhs_number),
                now_utc_string,
                "1",
                str(patient.id),
            ]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            "No such ID number type: 1",
            reply_dict[TabletParam.ERROR],
            msg=reply_dict,
        )

    def test_fails_if_patient_idnum_invalid(self) -> None:
        now_utc_string = now("UTC").isoformat()
        iddef = NHSIdNumDefinitionFactory()
        patient = PatientFactory(_device=self.device)

        self.post_dict[TabletParam.TABLE] = "patient_idnum"
        self.post_dict[TabletParam.PKVALUES] = "1"
        self.post_dict[TabletParam.FIELDS] = ",".join(
            [
                "id",
                "which_idnum",
                "idnum_value",
                "when_last_modified",
                "_move_off_tablet",
                "patient_id",
            ]
        )
        invalid_nhs_number = 123
        self.post_dict[TabletParam.VALUES] = ",".join(
            [
                "1",
                str(iddef.which_idnum),
                str(invalid_nhs_number),
                now_utc_string,
                "1",
                str(patient.id),
            ]
        )

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            f"For ID type {iddef.which_idnum}, ID number "
            f"{invalid_nhs_number} is invalid",
            reply_dict[TabletParam.ERROR],
            msg=reply_dict,
        )


class OpUploadTableTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.post_dict[TabletParam.OPERATION] = Operations.UPLOAD_TABLE
        self.post_dict[TabletParam.TABLE] = "bmi"
        self.post_dict[TabletParam.PKNAME] = "id"
        self.post_dict[TabletParam.FIELDS] = ",".join(
            [
                "id",
                "height_m",
                "mass_kg",
                "when_created",
                "when_last_modified",
                "_move_off_tablet",
                "patient_id",
            ]
        )

    def test_table_uploaded(self) -> None:
        now_utc_string = now("UTC").isoformat()
        patient1 = PatientFactory(_device=self.device)
        patient2 = PatientFactory(_device=self.device)

        self.post_dict[TabletParam.NRECORDS] = "2"
        self.post_dict["record0"] = ",".join(
            [
                "1",
                "1.83",
                "67",
                now_utc_string,
                now_utc_string,
                "1",
                str(patient1.id),
            ]
        )
        self.post_dict["record1"] = ",".join(
            [
                "2",
                "1.6",
                "50",
                now_utc_string,
                now_utc_string,
                "1",
                str(patient2.id),
            ]
        )
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict[TabletParam.RESULT],
            "Table bmi upload successful",
            msg=reply_dict,
        )

        bmi_1 = self.dbsession.execute(
            select(Bmi).where(Bmi.id == 1)
        ).scalar_one()
        self.assertAlmostEqual(bmi_1.height_m, 1.83)
        self.assertAlmostEqual(bmi_1.mass_kg, 67)

        bmi_2 = self.dbsession.execute(
            select(Bmi).where(Bmi.id == 2)
        ).scalar_one()
        self.assertAlmostEqual(bmi_2.height_m, 1.6)
        self.assertAlmostEqual(bmi_2.mass_kg, 50)

    def test_fails_if_nrecords_less_than_zero(self) -> None:
        self.post_dict[TabletParam.NRECORDS] = "-1"
        reply_dict = self.call_api()
        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            reply_dict[TabletParam.ERROR],
            f"{TabletParam.NRECORDS}=-1: can't be less than 0",
        )

    def test_fails_if_fields_do_not_match_values(self) -> None:
        self.post_dict[TabletParam.NRECORDS] = "1"
        self.post_dict["record0"] = ",".join(["1"])
        reply_dict = self.call_api()
        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], FAILURE_CODE, msg=reply_dict
        )
        self.assertIn(
            reply_dict[TabletParam.ERROR],
            "Number of fields in field list (7) "
            "doesn't match number of values in record 0 (1)",
        )

    def test_record_updated(self) -> None:
        now_utc_string = now("UTC").isoformat()
        patient = PatientFactory(_device=self.device)
        bmi = BmiFactory(
            patient=patient,
            _era=ERA_NOW,
            height_m=1.8,
            mass_kg=70,
        )

        self.post_dict[TabletParam.NRECORDS] = "1"
        self.post_dict["record0"] = ",".join(
            [
                str(bmi.id),
                "1.83",
                "67",
                now_utc_string,
                now_utc_string,
                "1",
                str(patient.id),
            ]
        )
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict[TabletParam.RESULT],
            "Table bmi upload successful",
            msg=reply_dict,
        )

        bmi_1 = self.dbsession.execute(
            select(Bmi).where(Bmi._predecessor_pk == bmi._pk)
        ).scalar_one()
        self.assertAlmostEqual(bmi_1.height_m, 1.83)
        self.assertAlmostEqual(bmi_1.mass_kg, 67)

    def test_record_flagged_for_deletion(self) -> None:
        now_utc_string = now("UTC").isoformat()
        patient = PatientFactory(_device=self.device)
        bmi = BmiFactory(
            patient=patient,
            _era=ERA_NOW,
            height_m=1.8,
            mass_kg=70,
        )

        # No record for this on the tablet
        bmi_to_delete = BmiFactory(
            patient=patient,
            _era=ERA_NOW,
        )
        self.assertFalse(bmi_to_delete._removal_pending)

        self.post_dict[TabletParam.NRECORDS] = "1"
        self.post_dict["record0"] = ",".join(
            [
                str(bmi.id),
                "1.83",
                "67",
                now_utc_string,
                now_utc_string,
                "1",
                str(patient.id),
            ]
        )
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.dbsession.commit()

        self.assertTrue(bmi_to_delete._removal_pending)

    def test_no_records_marks_table_clean(self) -> None:
        self.device.currently_preserving = True
        self.device.ongoing_upload_batch_utc = now("UTC")
        self.dbsession.add(self.device)
        self.dbsession.commit()

        DirtyTableFactory(tablename="bmi", device_id=self.device.id)
        self.assertIsNotNone(
            self.dbsession.execute(
                select(DirtyTable).where(DirtyTable.tablename == "bmi")
            ).scalar_one_or_none()
        )
        self.post_dict[TabletParam.NRECORDS] = "0"
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

        self.assertIsNone(
            self.dbsession.execute(
                select(DirtyTable).where(DirtyTable.tablename == "bmi")
            ).scalar_one_or_none()
        )


class OpEndUploadTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.post_dict[TabletParam.OPERATION] = Operations.END_UPLOAD
        self.device.ongoing_upload_batch_utc = now("UTC")
        self.device.uploading_user_id = self.user.id
        self.dbsession.add(self.device)
        self.dbsession.commit()

    def test_updates_added_records(self) -> None:
        patient = PatientFactory(_device=self.device)
        bmi = BmiFactory(
            patient=patient,
            _era=ERA_NOW,
            _addition_pending=True,
        )

        DirtyTableFactory(tablename="bmi", device_id=self.device.id)

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertFalse(bmi._addition_pending)
        self.assertIsNotNone(bmi._when_added_exact)
        self.assertIsNotNone(bmi._when_added_batch_utc)

    def test_updates_removed_records(self) -> None:
        patient = PatientFactory(_device=self.device)
        bmi = BmiFactory(
            patient=patient,
            _era=ERA_NOW,
            _current=True,
            _removal_pending=True,
        )

        DirtyTableFactory(tablename="bmi", device_id=self.device.id)

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertFalse(bmi._current)
        self.assertFalse(bmi._removal_pending)
        self.assertEqual(bmi._removing_user_id, self.user.id)
        self.assertIsNotNone(bmi._when_removed_exact)
        self.assertIsNotNone(bmi._when_removed_batch_utc)

    def test_updates_preserved_records(self) -> None:
        patient = PatientFactory(_device=self.device)
        bmi = BmiFactory(
            patient=patient,
            _era=ERA_NOW,
            _move_off_tablet=True,
        )

        DirtyTableFactory(tablename="bmi", device_id=self.device.id)

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertFalse(bmi._move_off_tablet)
        self.assertEqual(bmi._preserving_user_id, self.user.id)
        self.assertNotEqual(bmi._era, ERA_NOW)


class OpStartUploadTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.post_dict[TabletParam.OPERATION] = Operations.START_UPLOAD

    def test_updates_device_batch_utc_details(self) -> None:
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.dbsession.commit()
        self.assertIsNotNone(self.device.last_upload_batch_utc)
        self.assertIsNotNone(self.device.ongoing_upload_batch_utc)
        self.uploading_user_id = self.user.id

    def test_deletes_records_with_addition_pending(self) -> None:
        patient = PatientFactory(_device=self.device)
        BmiFactory(
            patient=patient,
            _era=ERA_NOW,
            _addition_pending=True,
        )
        DirtyTableFactory(tablename="bmi", device_id=self.device.id)

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.dbsession.commit()

        self.assertIsNone(
            self.dbsession.execute(select(Bmi)).scalar_one_or_none()
        )

    def test_updates_records_with_removal_pending(self) -> None:
        patient = PatientFactory(_device=self.device)
        BmiFactory(
            patient=patient,
            _era=ERA_NOW,
            _removal_pending=True,
            _when_added_exact=self.req.now,
            _when_removed_batch_utc=self.req.now_utc,
            _removing_user_id=self.user.id,
            _successor_pk=1234,
        )
        DirtyTableFactory(tablename="bmi", device_id=self.device.id)

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.dbsession.commit()

        bmi = self.dbsession.execute(select(Bmi)).scalar_one_or_none()
        self.assertFalse(bmi._removal_pending)
        self.assertIsNone(bmi._when_added_exact)
        self.assertIsNone(bmi._when_removed_batch_utc)
        self.assertIsNone(bmi._removing_user_id)
        self.assertIsNone(bmi._successor_pk)

    def test_sets_move_off_tablet_field_to_false(self) -> None:
        patient = PatientFactory(_device=self.device)
        BmiFactory(
            patient=patient,
            _era=ERA_NOW,
            _move_off_tablet=True,
        )
        DirtyTableFactory(tablename="bmi", device_id=self.device.id)

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.dbsession.commit()

        bmi = self.dbsession.execute(select(Bmi)).scalar_one_or_none()
        self.assertFalse(bmi._move_off_tablet)


class OpGetIdInfoTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.post_dict[TabletParam.OPERATION] = Operations.GET_ID_INFO

    def test_returns_database_title(self) -> None:
        with mock.patch.object(
            self.req,
            "database_title",
            "test database",
        ):
            reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict[TabletParam.DATABASE_TITLE], "test database"
        )

    def test_returns_upload_policy(self) -> None:
        self.group.upload_policy = "sex and anyidnum"
        self.dbsession.add(self.group)
        self.dbsession.commit()

        with mock.patch.object(
            self.req,
            "database_title",
            "test database",
        ):
            reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict[TabletParam.ID_POLICY_UPLOAD], "sex and anyidnum"
        )

    def test_returns_finalize_policy(self) -> None:
        self.group.finalize_policy = "sex and anyidnum"
        self.dbsession.add(self.group)
        self.dbsession.commit()

        with mock.patch.object(
            self.req,
            "database_title",
            "test database",
        ):
            reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict[TabletParam.ID_POLICY_FINALIZE], "sex and anyidnum"
        )

    def test_returns_server_version_string(self) -> None:
        with mock.patch.multiple(
            "camcops_server.cc_modules.client_api",
            CAMCOPS_SERVER_VERSION_STRING="test version",
        ):
            with mock.patch.object(
                self.req,
                "database_title",
                "test database",
            ):
                reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict[TabletParam.SERVER_CAMCOPS_VERSION], "test version"
        )

    def test_returns_idnum_definition(self) -> None:
        mock_idnum_definition = mock.Mock(
            which_idnum=1,
            description="Mock NHS Number",
            short_description="Mock NHS#",
            validation_method="Mock validation method",
        )

        with mock.patch.multiple(
            self.req,
            database_title="test database",
            idnum_definitions=[mock_idnum_definition],
        ):
            reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
        self.assertEqual(
            reply_dict["idDescription1"],
            "Mock NHS Number",
        )
        self.assertEqual(
            reply_dict["idShortDescription1"],
            "Mock NHS#",
        )
        self.assertEqual(
            reply_dict["idValidationMethod1"],
            "Mock validation method",
        )


class OpCheckUploadUserAndDeviceTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.post_dict[TabletParam.OPERATION] = (
            Operations.CHECK_UPLOAD_USER_DEVICE
        )

    def test_succeeds(self) -> None:
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )


class OpGetAllowedTablesTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.post_dict[TabletParam.OPERATION] = Operations.GET_ALLOWED_TABLES

    def test_returns_allowed_tables(self) -> None:
        mock_task_tables = mock.Mock(
            return_value={
                "table_1": Version("2.0.0"),
                "table_2": Version("2.0.1"),
                # These get overridden
                "blobs": Version("1.0.0"),
                "patient": Version("1.0.0"),
                "patient_idnum": Version("1.0.0"),
            }
        )

        with mock.patch.multiple(
            "camcops_server.cc_modules.client_api",
            all_task_tables_with_min_client_version=mock_task_tables,
            MINIMUM_TABLET_VERSION=Version("2.0.2"),
        ):
            reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

        fields = ",".join(
            [
                AllowedTablesFieldNames.TABLENAME,
                AllowedTablesFieldNames.MIN_CLIENT_VERSION,
            ]
        )
        self.assertEqual(reply_dict[TabletParam.NFIELDS], "2")
        self.assertEqual(reply_dict[TabletParam.FIELDS], fields)
        self.assertEqual(reply_dict[TabletParam.NRECORDS], "5")
        self.assertEqual(reply_dict["record0"], "'table_1','2.0.0'")
        self.assertEqual(reply_dict["record1"], "'table_2','2.0.1'")
        self.assertEqual(reply_dict["record2"], "'blobs','2.0.2'")
        self.assertEqual(reply_dict["record3"], "'patient','2.0.2'")
        self.assertEqual(reply_dict["record4"], "'patient_idnum','2.0.2'")


class OpGetExtraStringsTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.post_dict[TabletParam.OPERATION] = Operations.GET_EXTRA_STRINGS

    def test_returns_extra_strings(self) -> None:
        mock_extra_strings = mock.Mock(
            return_value=[
                ("task1", "name1", "language1", "value1"),
                ("task2", "name2", "language2", "value2"),
            ]
        )

        with mock.patch.object(
            self.req,
            "get_all_extra_strings",
            mock_extra_strings,
        ):
            reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

        fields = ",".join(
            [
                ExtraStringFieldNames.TASK,
                ExtraStringFieldNames.NAME,
                ExtraStringFieldNames.LANGUAGE,
                ExtraStringFieldNames.VALUE,
            ]
        )
        self.assertEqual(reply_dict[TabletParam.NFIELDS], "4")
        self.assertEqual(reply_dict[TabletParam.FIELDS], fields)
        self.assertEqual(reply_dict[TabletParam.NRECORDS], "2")
        self.assertEqual(
            reply_dict["record0"], "'task1','name1','language1','value1'"
        )
        self.assertEqual(
            reply_dict["record1"], "'task2','name2','language2','value2'"
        )


class OpRegisterDeviceTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.post_dict[TabletParam.OPERATION] = Operations.REGISTER

    def test_updates_existing_device(self) -> None:
        self.assertIsNone(self.device.when_registered_utc)
        self.assertIsNone(self.device.registered_by_user_id)
        self.post_dict[TabletParam.DEVICE_FRIENDLY_NAME] = "Test device name"

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

        self.dbsession.commit()

        # Server ID info tested elsewhere
        self.assertIn(TabletParam.SERVER_CAMCOPS_VERSION, reply_dict)

        self.assertEqual(self.device.friendly_name, "Test device name")
        self.assertEqual(
            self.device.camcops_version,
            Version(self.req.tabletsession.tablet_version_str),
        )
        self.assertIsNotNone(self.device.when_registered_utc)
        self.assertEqual(self.device.registered_by_user_id, self.user.id)

    def test_registers_new_device(self) -> None:
        self.assertIsNone(self.device.when_registered_utc)
        self.assertIsNone(self.device.registered_by_user_id)
        self.post_dict[TabletParam.DEVICE] = "unregistered"
        self.post_dict[TabletParam.DEVICE_FRIENDLY_NAME] = "Test device name"

        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )

        self.dbsession.commit()

        device = self.dbsession.execute(
            select(Device).where(Device.name == "unregistered")
        ).scalar_one()

        self.assertEqual(device.friendly_name, "Test device name")
        self.assertEqual(
            device.camcops_version,
            Version(self.req.tabletsession.tablet_version_str),
        )
        self.assertIsNotNone(device.when_registered_utc)
        self.assertEqual(device.registered_by_user_id, self.user.id)


class OpCheckDeviceRegisteredTests(ClientApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.post_dict[TabletParam.OPERATION] = (
            Operations.CHECK_DEVICE_REGISTERED
        )

    def test_device_registered(self) -> None:
        reply_dict = self.call_api()

        self.assertEqual(
            reply_dict[TabletParam.SUCCESS], SUCCESS_CODE, msg=reply_dict
        )
