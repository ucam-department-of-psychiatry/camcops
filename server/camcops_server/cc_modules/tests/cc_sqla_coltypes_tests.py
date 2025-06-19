"""
camcops_server/cc_modules/tests/cc_sqla_coltypes_tests.py

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

import datetime
from typing import Optional, Union

from cardinal_pythonlib.datetimefunc import coerce_to_pendulum
import pendulum
from pendulum import DateTime as Pendulum, Duration
import phonenumbers
import pytest
from semantic_version import Version
from sqlalchemy import insert
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql.expression import select
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import Column

from camcops_server.cc_modules.cc_sqla_coltypes import (
    COLATTR_IS_BLOB_ID_FIELD,
    COLATTR_IS_CAMCOPS_COLUMN,
    gen_camcops_blob_columns,
    gen_camcops_columns,
    gen_columns_matching_attrnames,
    isotzdatetime_to_utcdatetime,
    mapped_bool_column,
    mapped_camcops_column,
    ONE_TO_THREE_CHECKER,
    PendulumDateTimeAsIsoTextColType,
    PendulumDurationAsIsoTextColType,
    permitted_value_failure_msgs,
    permitted_values_ok,
    PhoneNumberColType,
    SemanticVersionColType,
    unknown_field_to_utcdatetime,
)
from camcops_server.cc_modules.cc_unittest import DemoRequestTestCase


class TestColTypeBase(DeclarativeBase):
    pass


# =============================================================================
# Unit testing
# =============================================================================
class TestColType(TestColTypeBase):
    __tablename__ = "test_coltype"

    id: Mapped[int] = mapped_column(primary_key=True)
    dt_local: Mapped[Optional[datetime.datetime]] = mapped_column()
    dt_utc: Mapped[Optional[datetime.datetime]] = mapped_column()
    dt_iso: Mapped[Optional[Pendulum]] = mapped_column(
        PendulumDateTimeAsIsoTextColType
    )
    duration_iso: Mapped[Optional[Duration]] = mapped_column(
        PendulumDurationAsIsoTextColType
    )
    version: Mapped[Optional[Version]] = mapped_column(SemanticVersionColType)
    phone_number: Mapped[Optional[phonenumbers.PhoneNumber]] = mapped_column(
        PhoneNumberColType
    )
    number_1_to_3: Mapped[Optional[int]] = mapped_camcops_column(
        permitted_value_checker=ONE_TO_THREE_CHECKER
    )
    flag: Mapped[Optional[bool]] = mapped_bool_column("flag")
    blob_id: Mapped[Optional[int]] = mapped_camcops_column(
        is_blob_id_field=True,
        blob_relationship_attr_name="picture",
    )


@pytest.mark.usefixtures("setup_temp_session")
class SqlaColtypesTestCase(DemoRequestTestCase):
    def setUp(self) -> None:
        super().setUp()

        TestColType.metadata.create_all(self.temp_engine)  # type: ignore[attr-defined]  # noqa: E501


class SqlaColtypesTest(SqlaColtypesTestCase):
    def _assert_dt_equal(
        self,
        a: Union[datetime.datetime, Pendulum],
        b: Union[datetime.datetime, Pendulum],
    ) -> None:
        # Accept that one may have been truncated or rounded to milliseconds.
        a = coerce_to_pendulum(a)
        b = coerce_to_pendulum(b)
        diff = a - b

        self.assertTrue(diff.microseconds < 1000, msg=f"{a!r} != {b!r}")

    def test_iso_datetime_field(self) -> None:
        now = Pendulum.now()
        now_utc = now.in_tz(pendulum.UTC)
        yesterday = now.subtract(days=1)
        yesterday_utc = yesterday.in_tz(pendulum.UTC)

        table = TestColType.__table__

        self.temp_session.execute(  # type: ignore[attr-defined]
            insert(table).values(  # type: ignore[arg-type]
                [
                    {
                        "id": 1,
                        "dt_local": now,
                        "dt_utc": now_utc,
                        "dt_iso": now,
                    },
                    {
                        "id": 2,
                        "dt_local": yesterday,
                        "dt_utc": yesterday_utc,
                        "dt_iso": yesterday,
                    },
                ]
            )
        )

        statement = (
            select(
                table.c.id,
                table.c.dt_local,
                table.c.dt_utc,
                table.c.dt_iso,
                func.length(table.c.dt_local).label("len_dt_local_col"),
                func.length(table.c.dt_utc).label("len_dt_utc_col"),
                func.length(table.c.dt_iso).label("len_iso_col"),
                isotzdatetime_to_utcdatetime(table.c.dt_iso).label(
                    "iso_to_utcdt"
                ),
                unknown_field_to_utcdatetime(table.c.dt_utc).label(
                    "uk_utcdt_to_utcdt"
                ),
                unknown_field_to_utcdatetime(table.c.dt_iso).label(
                    "uk_iso_to_utc_dt"
                ),
            )
            .select_from(table)
            .order_by(table.c.id)
        )

        rows = list(self.temp_session.execute(statement).mappings())  # type: ignore[attr-defined]  # noqa: E501

        self._assert_dt_equal(rows[0].dt_local, now)
        self._assert_dt_equal(rows[0].dt_utc, now_utc)
        self._assert_dt_equal(rows[0].dt_iso, now)
        self._assert_dt_equal(rows[0]["iso_to_utcdt"], now_utc)
        self._assert_dt_equal(rows[0]["uk_utcdt_to_utcdt"], now_utc)
        self._assert_dt_equal(rows[0]["uk_iso_to_utc_dt"], now_utc)

        self._assert_dt_equal(rows[1].dt_local, yesterday)
        self._assert_dt_equal(rows[1].dt_utc, yesterday_utc)
        self._assert_dt_equal(rows[1].dt_iso, yesterday)
        self._assert_dt_equal(rows[1]["iso_to_utcdt"], yesterday_utc)
        self._assert_dt_equal(rows[1]["uk_utcdt_to_utcdt"], yesterday_utc)
        self._assert_dt_equal(rows[1]["uk_iso_to_utc_dt"], yesterday_utc)

    def _assert_duration_equal(self, a: Duration, b: Duration) -> None:
        self.assertEqual(a.total_seconds(), b.total_seconds())

    def test_iso_duration_field(self) -> None:
        d1 = Duration(years=1, months=3, seconds=3, microseconds=4)
        d2 = Duration(seconds=987.654321)
        d3 = Duration(days=-5)

        table = TestColType.__table__

        self.temp_session.execute(  # type: ignore[attr-defined]
            insert(table).values(  # type: ignore[arg-type]
                [
                    {"id": 1, "duration_iso": d1},
                    {"id": 2, "duration_iso": d2},
                    {"id": 3, "duration_iso": d3},
                ]
            )
        )

        statement = (
            select(table.c.id, table.c.duration_iso)
            .select_from(table)
            .order_by(table.c.id)
        )

        rows = list(self.temp_session.execute(statement).mappings())  # type: ignore[attr-defined]  # noqa: E501

        self._assert_duration_equal(rows[0].duration_iso, d1)
        self._assert_duration_equal(rows[1].duration_iso, d2)
        self._assert_duration_equal(rows[2].duration_iso, d3)

    def test_semantic_version_field(self) -> None:
        v1 = Version("1.1.0")
        v2 = Version("2.0.1")
        v3 = Version("14.0.0")

        table = TestColType.__table__

        self.temp_session.execute(  # type: ignore[attr-defined]
            insert(table).values(  # type: ignore[arg-type]
                [
                    {"id": 1, "version": v1},
                    {"id": 2, "version": v2},
                    {"id": 3, "version": v3},
                ]
            )
        )

        statement = (
            select(table.c.id, table.c.version)
            .select_from(table)
            .order_by(table.c.id)
        )

        rows = list(self.temp_session.execute(statement).mappings())  # type: ignore[attr-defined]  # noqa: E501

        self.assertEqual(rows[0]["version"], v1)
        self.assertEqual(rows[1]["version"], v2)
        self.assertEqual(rows[2]["version"], v3)

    def test_phone_number_field(self) -> None:
        # https://en.wikipedia.org/wiki/Fictitious_telephone_number
        p1 = phonenumbers.parse("+44 (0)113 496 0123")
        p2 = phonenumbers.parse("+33 1 99 00 12 34 56")
        p3 = phonenumbers.parse("07700 900123", "GB")
        p4 = None

        table = TestColType.__table__

        self.temp_session.execute(  # type: ignore[attr-defined]
            insert(table).values(  # type: ignore[arg-type]
                [
                    {"id": 1, "phone_number": p1},
                    {"id": 2, "phone_number": p2},
                    {"id": 3, "phone_number": p3},
                    {"id": 4, "phone_number": p4},
                ]
            )
        )

        statement = (
            select(table.c.id, table.c.phone_number)
            .select_from(table)
            .order_by(table.c.id)
        )

        rows = list(self.temp_session.execute(statement).mappings())  # type: ignore[attr-defined]  # noqa: E501

        self.assertEqual(rows[0]["phone_number"], p1)
        self.assertEqual(rows[1]["phone_number"], p2)
        self.assertEqual(rows[2]["phone_number"], p3)
        self.assertIsNone(rows[3]["phone_number"])


class GenCamcopsColumnsTests(SqlaColtypesTestCase):
    def test_returns_camcops_columns(self) -> None:
        obj = TestColType(id=1, number_1_to_3=1, flag=True)

        for name, column in gen_camcops_columns(obj):
            if name not in ["number_1_to_3", "flag", "blob_id"]:
                self.fail(
                    f"Unexpected camcops column returned with name '{name}'"
                )
            self.assertTrue(column.info.get(COLATTR_IS_CAMCOPS_COLUMN))


class GenCamcopsBlobColumnsTests(SqlaColtypesTestCase):
    def test_returns_camcops_columns(self) -> None:
        obj = TestColType(id=1, blob_id=2)

        for name, column in gen_camcops_blob_columns(obj):
            if name not in ["blob_id"]:
                self.fail(
                    f"Unexpected blob column returned with name '{name}'"
                )
            self.assertTrue(column.info.get(COLATTR_IS_BLOB_ID_FIELD))


class GenColumnsMatchingAttrnamesTests(SqlaColtypesTestCase):
    def test_returns_matching_columns(self) -> None:
        obj = TestColType(id=1, number_1_to_3=1, flag=True)

        attrnames = ["phone_number", "number_1_to_3", "flag"]

        for name, column in gen_columns_matching_attrnames(obj, attrnames):
            if name not in attrnames:
                self.fail(f"Unexpected column returned with name '{name}'")
            attrnames.remove(name)
            self.assertIsInstance(column, Column)

        self.assertEqual(attrnames, [])


class PermittedValueFailureMsgsTests(SqlaColtypesTestCase):
    def test_returns_failure_messages(self) -> None:
        obj = TestColType(id=1, number_1_to_3=123)

        messages = permitted_value_failure_msgs(obj)
        self.assertEqual(len(messages), 1)

        self.assertIn("Invalid value", messages[0])


class PermittedValuesOkTests(SqlaColtypesTestCase):
    def test_returns_false_if_not_ok(self) -> None:
        obj = TestColType(id=1, number_1_to_3=123)

        self.assertFalse(permitted_values_ok(obj))

    def test_returns_true_if_ok(self) -> None:
        obj = TestColType(id=1, number_1_to_3=1)

        self.assertTrue(permitted_values_ok(obj))
