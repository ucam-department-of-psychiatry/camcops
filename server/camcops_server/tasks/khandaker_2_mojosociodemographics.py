#!/usr/bin/env python

"""
camcops_server/tasks/khandaker_2_mojosociodemographics.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================

"""

from typing import Any, Dict, Tuple, Type


from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
    MIN_ZERO_CHECKER,
    ZERO_TO_10_CHECKER,
    ZERO_TO_FOUR_CHECKER,
    ZERO_TO_SEVEN_CHECKER,
    ZERO_TO_SIX_CHECKER,
    ZERO_TO_TWO_CHECKER,
)
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasPatientMixin,
)


class Khandaker2MojoSociodemographicsMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Khandaker2MojoSociodemographics'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:

        setattr(
            cls, "age",
            CamcopsColumn(
                "age", Integer,
                permitted_value_checker=MIN_ZERO_CHECKER,
                comment="Age, closest full year"
            )
        )

        setattr(
            cls, "gender",
            CamcopsColumn(
                "gender", Integer,
                permitted_value_checker=ZERO_TO_TWO_CHECKER,
                comment="Gender at birth (0 Male, 1 Female, 2 Other (specify)"
            )
        )

        setattr(
            cls, "other_gender",
            CamcopsColumn(
                "other_gender", UnicodeText,
                comment="Other (specify)"
            )
        )

        setattr(
            cls, "ethnicity",
            CamcopsColumn(
                "ethnicity", Integer,
                permitted_value_checker=ZERO_TO_10_CHECKER,
                comment=("Ethnicity (0 White, 1 Mixed, 2 Indian, 3 Pakistani, "
                         "4 Bangladeshi, 5 Other Asian, 6 Black Caribbean, "
                         "7 Black African, 8 Black Other, 9 Chinese, "
                         "10 Other (specify)")
            )
        )

        setattr(
            cls, "other_ethnicity",
            CamcopsColumn(
                "other_ethnicity", UnicodeText,
                comment="Other (specify)"
            )
        )

        setattr(
            cls, "with_whom_live",
            CamcopsColumn(
                "with_whom_live", Integer,
                permitted_value_checker=ZERO_TO_SEVEN_CHECKER,
                comment=("0 Alone, 1 Alone with children, 2 Partner/Spouse, "
                         "3 Partner/Spouse and children, 4 Parents, "
                         "5 Other family, 6 Friends, 7 Other (specify)")
            )
        )

        setattr(
            cls, "other_with_whom_live",
            CamcopsColumn(
                "other_with_whom_live", UnicodeText,
                comment="Other (specify)"
            )
        )

        setattr(
            cls, "relationship_status",
            CamcopsColumn(
                "relationship_status", Integer,
                permitted_value_checker=ZERO_TO_FOUR_CHECKER,
                comment=("0 Single, 1 Married / Civil partnership, "
                         "2 In steady relationship, 3 Divorced / separated, "
                         "4 Widowed")
            )
        )

        setattr(
            cls, "education",
            CamcopsColumn(
                "education", Integer,
                permitted_value_checker=ZERO_TO_FOUR_CHECKER,
                comment=("0 No qualifications, 1 GCSE/O levels, 2 A levels, "
                         "3 Vocational/college (B. Tecs/NVQs etc), "
                         "4 University / Professional Qualifications")
            )
        )

        setattr(
            cls, "employment",
            CamcopsColumn(
                "employment", Integer,
                permitted_value_checker=ZERO_TO_SEVEN_CHECKER,
                comment=("0 No unemployed, 1 No student, 2 Yes full time, "
                         "3 Yes part time, 4 Full time homemaker, "
                         "5 Self employed, 6 Not working for medical reasons, "
                         "7 Other (specify)")
            )
        )

        setattr(
            cls, "other_employment",
            CamcopsColumn(
                "other_employment", UnicodeText,
                comment="Other (specify)"
            )
        )

        setattr(
            cls, "accommodation",
            CamcopsColumn(
                "accommodation", Integer,
                permitted_value_checker=ZERO_TO_SIX_CHECKER,
                comment=("0 Own outright, 1 Own with mortgage, "
                         "2 Rent from local authority etc, "
                         "3 Rent from landlord (private), "
                         "4 Shared ownership (part rent, part mortgage)"
                         "5 Live rent free, 6 Other (specify)")
            )
        )

        setattr(
            cls, "other_accommodation",
            CamcopsColumn(
                "other_accommodation", UnicodeText,
                comment="Other (specify)"
            )
        )

        super().__init__(name, bases, classdict)


class Khandaker2MojoSociodemographics(
        TaskHasPatientMixin, Task,
        metaclass=Khandaker2MojoSociodemographicsMetaclass):
    """
    Server implementation of the Khandaker_2_MOJOSociodemographics task
    """
    __tablename__ = "khandaker_2_mojosociodemographics"
    shortname = "khandaker_2_MOJOSociodemographics"
    provides_trackers = False

    OTHER_FIELD_DICT = {
        "gender": "X",
        "ethnicity": 10,
        "with_whom_live": 7,
        "employment": 7,
        "accommodation": 6,
    }

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Khandaker GM — 2 MOJO Study — Sociodemographics "
                 "Questionnaire")

    def is_complete(self) -> bool:
        if self.any_fields_none(self.MANDATORY_FIELDS):
            return False

        if not self.field_contents_valid():
            return False

        for name, other_option in self.OTHER_FIELD_DICT.items():
            if getattr(self, name) == other_option:
                if getattr(self, f"other_{name}") is None:
                    return False

        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
        return "TODO"
