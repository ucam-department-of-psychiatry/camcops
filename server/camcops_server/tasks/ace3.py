#!/usr/bin/env python

"""
camcops_server/tasks/ace3.py

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

ACE-III and Mini-ACE.

"""

from typing import Any, Dict, List, Optional, Tuple, Type, TYPE_CHECKING

from cardinal_pythonlib.stringfunc import strseq
import cardinal_pythonlib.rnc_web as ws
import numpy
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Boolean, Integer, String, UnicodeText
from typing import Iterable

from camcops_server.cc_modules.cc_blob import (
    blob_relationship,
    get_blob_img_html,
)
from camcops_server.cc_modules.cc_constants import CssClass, PlotDefaults, PV
from camcops_server.cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import (
    answer,
    get_yes_no_none,
    italic,
    subheading_spanning_two_columns,
    tr,
    tr_qa,
    tr_span_col,
)
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_snomed import SnomedExpression, SnomedLookup
from camcops_server.cc_modules.cc_sqla_coltypes import (
    BIT_CHECKER,
    CamcopsColumn,
    PermittedValueChecker,
)
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    Task,
    TaskHasClinicianMixin,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import TrackerInfo

if TYPE_CHECKING:
    from camcops_server.cc_modules.cc_blob import Blob


# =============================================================================
# Constants
# =============================================================================

ADDRESS_PARTS = [
    "forename",
    "surname",
    "number",
    "street_1",
    "street_2",
    "town",
    "county",
]
RECALL_WORDS = ["lemon", "key", "ball"]
PERCENT_DP = 1

TOTAL_MAX = 100
ATTN_MAX = 18
MEMORY_MAX = 26
FLUENCY_MAX = 14
LANG_MAX = 26
VSP_MAX = 16

ATTN_MINIACE_MAX = 4
MEM_MINIACE_MAX = 14
FLUENCY_MINIACE_MAX = 7
VSP_MINIACE_MAX = 5
MINI_ACE_MAX = 30

AGE_FTE = "Age on leaving full-time education"
OCCUPATION = "Occupation"
HANDEDNESS = "Handedness"
N_ATTN_TIME_ACE = 5
N_ATTN_TIME_MINIACE = 4
N_MEM_REPEAT_RECALL_ADDR = 7
ANIMAL_FLUENCY_SCORING_HTML = (
    "Score for animals <i>(≥22 scores 7, 17–21 scores 6, 14–16 scores 5, "
    "11–13 scores 4, 9–10 scores 3, 7–8 scores 2, 5–6 scores 1, "
    "&lt;5 scores 0)</i>"
)
ACE3_COPYRIGHT = """
ACE-III: Copyright © 2012, John Hodges. “The ACE-III is available for free. The
copyright is held by Professor John Hodges who is happy for the test to be used
in clinical practice and research projects. There is no need to contact us if
you wish to use the ACE-III in clinical practice.” (ACE-III FAQ, 7 July 2013,
www.neura.edu.au).
"""
MINI_ACE_THRESHOLDS = """
In the mini-ACE, scores ≤21 had sensitivity 0.61 and specificity 1.0 for
dementia, and scores ≤25 had sensitivity 0.85 and specificity 0.87 for
dementia, in a context of patients with Alzheimer’s disease, behavioural
variant frontotemporal dementia, corticobasal syndrome, primary progressive
aphasia, and controls (Hsieh et al., 2015, PMID 25227877).
"""


# =============================================================================
# Ancillary functions
# =============================================================================


def score_zero_for_absent(x: Optional[int]) -> int:
    """0 if x is None else x"""
    return 0 if x is None else x


def percent(score: int, maximum: int) -> str:
    return ws.number_to_dp(100 * score / maximum, PERCENT_DP)


def tr_score_with_pct(title: str, score: int, maximum: int) -> str:
    return tr(
        title,
        answer(score) + f" / {maximum} ({percent(score, maximum)}%)",
    )


def qsequence(target_addr_parts: Iterable[str]) -> str:
    """
    For e.g. "Harry? Barnes? ..."
    """
    return " ".join(f"{x}?" for x in target_addr_parts)


def tr_heading(left: str, right: str) -> str:
    """
    HTML for header row of most tables.
    """
    return f"""
        <tr>
            <th width="67%">{left}</th>
            <th width="33%">{right}</th>
        </tr>
    """


# =============================================================================
# ACE-III
# =============================================================================


class Ace3Metaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(
        cls: Type["Ace3"],
        name: str,
        bases: Tuple[Type, ...],
        classdict: Dict[str, Any],
    ) -> None:
        add_multiple_columns(
            cls,
            "attn_time",
            1,
            5,
            pv=PV.BIT,
            comment_fmt="Attention, time, {n}/5, {s} (0 or 1)",
            comment_strings=["day", "date", "month", "year", "season"],
        )
        add_multiple_columns(
            cls,
            "attn_place",
            1,
            5,
            pv=PV.BIT,
            comment_fmt="Attention, place, {n}/5, {s} (0 or 1)",
            comment_strings=[
                "house number/floor",
                "street/hospital",
                "town",
                "county",
                "country",
            ],
        )
        add_multiple_columns(
            cls,
            "attn_repeat_word",
            1,
            3,
            pv=PV.BIT,
            comment_fmt="Attention, repeat word, {n}/3, {s} (0 or 1)",
            comment_strings=RECALL_WORDS,
        )
        add_multiple_columns(
            cls,
            "attn_serial7_subtraction",
            1,
            5,
            pv=PV.BIT,
            comment_fmt="Attention, serial sevens, {n}/5 (0 or 1)",
        )

        add_multiple_columns(
            cls,
            "mem_recall_word",
            1,
            3,
            pv=PV.BIT,
            comment_fmt="Memory, recall word, {n}/3, {s} (0 or 1)",
            comment_strings=RECALL_WORDS,
        )
        add_multiple_columns(
            cls,
            "mem_repeat_address_trial1_",
            1,
            N_MEM_REPEAT_RECALL_ADDR,
            pv=PV.BIT,
            comment_fmt="Memory, address registration trial 1/3 "
            "(not scored), {s} (0 or 1)",
            comment_strings=ADDRESS_PARTS,
        )
        add_multiple_columns(
            cls,
            "mem_repeat_address_trial2_",
            1,
            N_MEM_REPEAT_RECALL_ADDR,
            pv=PV.BIT,
            comment_fmt="Memory, address registration trial 2/3 "
            "(not scored), {s} (0 or 1)",
            comment_strings=ADDRESS_PARTS,
        )
        add_multiple_columns(
            cls,
            "mem_repeat_address_trial3_",
            1,
            N_MEM_REPEAT_RECALL_ADDR,
            pv=PV.BIT,
            comment_fmt="Memory, address registration trial 3/3 "
            "(scored), {s} (0 or 1)",
            comment_strings=ADDRESS_PARTS,
        )
        add_multiple_columns(
            cls,
            "mem_famous",
            1,
            4,
            pv=PV.BIT,
            comment_fmt="Memory, famous people, {n}/4, {s} (0 or 1)",
            comment_strings=["current PM", "woman PM", "USA president", "JFK"],
        )

        add_multiple_columns(
            cls,
            "lang_follow_command",
            1,
            3,
            pv=PV.BIT,
            comment_fmt="Language, command {n}/3 (0 or 1)",
        )
        add_multiple_columns(
            cls,
            "lang_write_sentences_point",
            1,
            2,
            pv=PV.BIT,
            comment_fmt="Language, write sentences, {n}/2, {s} (0 or 1)",
            comment_strings=[
                "two sentences on same topic",
                "grammar/spelling",
            ],
        )
        add_multiple_columns(
            cls,
            "lang_repeat_word",
            1,
            4,
            pv=PV.BIT,
            comment_fmt="Language, repeat word, {n}/4, {s} (0 or 1)",
            comment_strings=[
                "caterpillar",
                "eccentricity",
                "unintelligible",
                "statistician",
            ],
        )
        add_multiple_columns(
            cls,
            "lang_repeat_sentence",
            1,
            2,
            pv=PV.BIT,
            comment_fmt="Language, repeat sentence, {n}/2, {s} (0 or 1)",
            comment_strings=["glitters_gold", "stitch_time"],
        )
        add_multiple_columns(
            cls,
            "lang_name_picture",
            1,
            12,
            pv=PV.BIT,
            comment_fmt="Language, name picture, {n}/12, {s} (0 or 1)",
            comment_strings=[
                "spoon",
                "book",
                "kangaroo/wallaby",
                "penguin",
                "anchor",
                "camel/dromedary",
                "harp",
                "rhinoceros",
                "barrel/keg/tub",
                "crown",
                "alligator/crocodile",
                "accordion/piano accordion/squeeze box",
            ],
        )
        add_multiple_columns(
            cls,
            "lang_identify_concept",
            1,
            4,
            pv=PV.BIT,
            comment_fmt="Language, identify concept, {n}/4, {s} (0 or 1)",
            comment_strings=["monarchy", "marsupial", "Antarctic", "nautical"],
        )

        add_multiple_columns(
            cls,
            "vsp_count_dots",
            1,
            4,
            pv=PV.BIT,
            comment_fmt="Visuospatial, count dots {n}/4, {s} dots (0-1)",
            comment_strings=["8", "10", "7", "9"],
        )
        add_multiple_columns(
            cls,
            "vsp_identify_letter",
            1,
            4,
            pv=PV.BIT,
            comment_fmt="Visuospatial, identify letter {n}/4, {s} (0-1)",
            comment_strings=["K", "M", "A", "T"],
        )
        add_multiple_columns(
            cls,
            "mem_recall_address",
            1,
            N_MEM_REPEAT_RECALL_ADDR,
            pv=PV.BIT,
            comment_fmt="Memory, recall address {n}/7, {s} (0-1)",
            comment_strings=ADDRESS_PARTS,
        )
        add_multiple_columns(
            cls,
            "mem_recognize_address",
            1,
            5,
            pv=PV.BIT,
            comment_fmt="Memory, recognize address {n}/5 (if "
            "applicable) ({s}) (0-1)",
            comment_strings=["name", "number", "street", "town", "county"],
        )
        add_multiple_columns(  # tablet version 2.0.0 onwards
            cls,
            "mem_recognize_address_choice",
            1,
            5,
            coltype=String(length=1),  # was Text
            comment_fmt="Memory, recognize address {n}/5, CHOICE (if "
            "applicable) ({s}) (A/B/C)",
            comment_strings=["name", "number", "street", "town", "county"],
        )

        super().__init__(name, bases, classdict)


class Ace3(
    TaskHasPatientMixin, TaskHasClinicianMixin, Task, metaclass=Ace3Metaclass
):
    """
    Server implementation of the ACE-III task.
    """

    __tablename__ = "ace3"
    shortname = "ACE-III"
    provides_trackers = True

    prohibits_commercial = True

    task_edition = CamcopsColumn(
        "task_edition",
        String(length=255),
        comment="Task edition. Older task instances will have NULL and that "
        "indicates UK English, 2012 version.",
    )
    task_address_version = CamcopsColumn(
        "task_address_version",
        String(length=1),
        comment="Task version, determining the address for recall (A/B/C). "
        "Older task instances will have NULL and that indicates version A.",
        permitted_value_checker=PermittedValueChecker(
            permitted_values=["A", "B", "C"]
        ),
    )  # type: str
    remote_administration = CamcopsColumn(
        "remote_administration",
        Boolean,
        permitted_value_checker=BIT_CHECKER,
        comment="Task performed using remote (videoconferencing) "
        "administration?",
    )
    age_at_leaving_full_time_education = Column(
        "age_at_leaving_full_time_education",
        Integer,
        comment="Age at leaving full time education",
    )
    occupation = Column("occupation", UnicodeText, comment="Occupation")
    handedness = CamcopsColumn(
        "handedness",
        String(length=1),  # was Text
        comment="Handedness (L or R)",
        permitted_value_checker=PermittedValueChecker(
            permitted_values=["L", "R"]
        ),
    )
    attn_num_registration_trials = Column(
        "attn_num_registration_trials",
        Integer,
        comment="Attention, repetition, number of trials (not scored)",
    )
    fluency_letters_score = CamcopsColumn(
        "fluency_letters_score",
        Integer,
        comment="Fluency, words beginning with P, score 0-7",
        permitted_value_checker=PermittedValueChecker(minimum=0, maximum=7),
    )  # type: Optional[int]
    fluency_animals_score = CamcopsColumn(
        "fluency_animals_score",
        Integer,
        comment="Fluency, animals, score 0-7",
        permitted_value_checker=PermittedValueChecker(minimum=0, maximum=7),
    )  # type: Optional[int]
    lang_follow_command_practice = CamcopsColumn(
        "lang_follow_command_practice",
        Integer,
        comment="Language, command, practice trial (not scored)",
        permitted_value_checker=BIT_CHECKER,
    )
    lang_read_words_aloud = CamcopsColumn(
        "lang_read_words_aloud",
        Integer,
        comment="Language, read five irregular words (0 or 1)",
        permitted_value_checker=BIT_CHECKER,
    )  # type: Optional[int]
    vsp_copy_infinity = CamcopsColumn(
        "vsp_copy_infinity",
        Integer,
        comment="Visuospatial, copy infinity (0-1)",
        permitted_value_checker=BIT_CHECKER,
    )  # type: Optional[int]
    vsp_copy_cube = CamcopsColumn(
        "vsp_copy_cube",
        Integer,
        comment="Visuospatial, copy cube (0-2)",
        permitted_value_checker=PermittedValueChecker(minimum=0, maximum=2),
    )  # type: Optional[int]
    vsp_draw_clock = CamcopsColumn(
        "vsp_draw_clock",
        Integer,
        comment="Visuospatial, draw clock (0-5)",
        permitted_value_checker=PermittedValueChecker(minimum=0, maximum=5),
    )  # type: Optional[int]
    picture1_blobid = CamcopsColumn(
        "picture1_blobid",
        Integer,
        comment="Photo 1/2 PNG BLOB ID",
        is_blob_id_field=True,
        blob_relationship_attr_name="picture1",
    )
    picture2_blobid = CamcopsColumn(
        "picture2_blobid",
        Integer,
        comment="Photo 2/2 PNG BLOB ID",
        is_blob_id_field=True,
        blob_relationship_attr_name="picture2",
    )
    comments = Column("comments", UnicodeText, comment="Clinician's comments")

    picture1 = blob_relationship(
        "Ace3", "picture1_blobid"
    )  # type: Optional[Blob]
    picture2 = blob_relationship(
        "Ace3", "picture2_blobid"
    )  # type: Optional[Blob]

    ATTN_SCORE_FIELDS = (
        strseq("attn_time", 1, N_ATTN_TIME_ACE)
        + strseq("attn_place", 1, 5)
        + strseq("attn_repeat_word", 1, 3)
        + strseq("attn_serial7_subtraction", 1, 5)
    )
    MEM_NON_RECOG_SCORE_FIELDS = (
        strseq("mem_recall_word", 1, 3)
        + strseq("mem_repeat_address_trial3_", 1, N_MEM_REPEAT_RECALL_ADDR)
        + strseq("mem_famous", 1, 4)
        + strseq("mem_recall_address", 1, N_MEM_REPEAT_RECALL_ADDR)
    )
    LANG_SIMPLE_SCORE_FIELDS = (
        strseq("lang_write_sentences_point", 1, 2)
        + strseq("lang_repeat_sentence", 1, 2)
        + strseq("lang_name_picture", 1, 12)
        + strseq("lang_identify_concept", 1, 4)
    )
    LANG_FOLLOW_CMD_FIELDS = strseq("lang_follow_command", 1, 3)
    LANG_REPEAT_WORD_FIELDS = strseq("lang_repeat_word", 1, 4)
    VSP_SIMPLE_SCORE_FIELDS = strseq("vsp_count_dots", 1, 4) + strseq(
        "vsp_identify_letter", 1, 4
    )
    BASIC_COMPLETENESS_FIELDS = (
        ATTN_SCORE_FIELDS
        + MEM_NON_RECOG_SCORE_FIELDS
        + ["fluency_letters_score", "fluency_animals_score"]
        + ["lang_follow_command_practice"]
        + LANG_SIMPLE_SCORE_FIELDS
        + LANG_REPEAT_WORD_FIELDS
        + [
            "lang_read_words_aloud",
            "vsp_copy_infinity",
            "vsp_copy_cube",
            "vsp_draw_clock",
        ]
        + VSP_SIMPLE_SCORE_FIELDS
        + strseq("mem_recall_address", 1, N_MEM_REPEAT_RECALL_ADDR)
    )
    MINI_ACE_FIELDS = (
        strseq("attn_time", 1, N_ATTN_TIME_MINIACE)  # 4 points; not season
        + ["fluency_animals_score"]  # 7 points
        + strseq("mem_repeat_address_trial3_", 1, N_MEM_REPEAT_RECALL_ADDR)
        # ... 7 points
        + ["vsp_draw_clock"]  # 5 points
        + strseq("mem_recall_address", 1, N_MEM_REPEAT_RECALL_ADDR)  # 7 points
    )

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Addenbrooke’s Cognitive Examination III")

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [
            TrackerInfo(
                value=self.total_score(),
                plot_label="ACE-III total score",
                axis_label=f"Total score (out of {TOTAL_MAX})",
                axis_min=-0.5,
                axis_max=TOTAL_MAX + 0.5,
                # Traditional cutoffs: ≤82, ≤88
                horizontal_lines=[82.5, 88.5],
            ),
            TrackerInfo(
                value=self.mini_ace_score(),
                plot_label="Mini-ACE score",
                axis_label=f"Mini-ACE score (out of {MINI_ACE_MAX})",
                axis_min=-0.5,
                axis_max=MINI_ACE_MAX + 0.5,
                # Traditional cutoffs: ≤21, ≤25
                horizontal_lines=[21.5, 25.5],
            ),
        ]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        a = self.attn_score()
        m = self.mem_score()
        f = self.fluency_score()
        lang = self.lang_score()
        v = self.vsp_score()
        t = a + m + f + lang + v
        mini = self.mini_ace_score()
        text = (
            f"ACE-III total: {t}/{TOTAL_MAX} "
            f"(attention {a}/{ATTN_MAX}, memory {m}/{MEMORY_MAX}, "
            f"fluency {f}/{FLUENCY_MAX}, language {lang}/{LANG_MAX}, "
            f"visuospatial {v}/{VSP_MAX}, "
            f"mini-ACE score {mini}/{MINI_ACE_MAX})"
        )
        return [CtvInfo(content=text)]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="total",
                coltype=Integer(),
                value=self.total_score(),
                comment=f"Total score (/{TOTAL_MAX})",
            ),
            SummaryElement(
                name="attn",
                coltype=Integer(),
                value=self.attn_score(),
                comment=f"Attention (/{ATTN_MAX})",
            ),
            SummaryElement(
                name="mem",
                coltype=Integer(),
                value=self.mem_score(),
                comment=f"Memory (/{MEMORY_MAX})",
            ),
            SummaryElement(
                name="fluency",
                coltype=Integer(),
                value=self.fluency_score(),
                comment=f"Fluency (/{FLUENCY_MAX})",
            ),
            SummaryElement(
                name="lang",
                coltype=Integer(),
                value=self.lang_score(),
                comment=f"Language (/{LANG_MAX})",
            ),
            SummaryElement(
                name="vsp",
                coltype=Integer(),
                value=self.vsp_score(),
                comment=f"Visuospatial (/{VSP_MAX})",
            ),
            SummaryElement(
                name="mini_ace",
                coltype=Integer(),
                value=self.mini_ace_score(),
                comment=f"Mini-ACE (/{MINI_ACE_MAX})",
            ),
        ]

    def attn_score(self) -> int:
        return self.sum_fields(self.ATTN_SCORE_FIELDS)

    @staticmethod
    def get_recog_score(
        recalled: Optional[int], recognized: Optional[int]
    ) -> int:
        if recalled == 1:
            return 1
        return score_zero_for_absent(recognized)

    @staticmethod
    def get_recog_text(
        recalled: Optional[int], recognized: Optional[int]
    ) -> str:
        if recalled:
            return "<i>1 (already recalled)</i>"
        return answer(recognized)

    # noinspection PyUnresolvedReferences
    def get_mem_recognition_score(self) -> int:
        score = 0
        score += self.get_recog_score(
            (self.mem_recall_address1 == 1 and self.mem_recall_address2 == 1),
            self.mem_recognize_address1,
        )
        score += self.get_recog_score(
            (self.mem_recall_address3 == 1), self.mem_recognize_address2
        )
        score += self.get_recog_score(
            (self.mem_recall_address4 == 1 and self.mem_recall_address5 == 1),
            self.mem_recognize_address3,
        )
        score += self.get_recog_score(
            (self.mem_recall_address6 == 1), self.mem_recognize_address4
        )
        score += self.get_recog_score(
            (self.mem_recall_address7 == 1), self.mem_recognize_address5
        )
        return score

    def mem_score(self) -> int:
        return (
            self.sum_fields(self.MEM_NON_RECOG_SCORE_FIELDS)
            + self.get_mem_recognition_score()
        )

    def fluency_score(self) -> int:
        return score_zero_for_absent(
            self.fluency_letters_score
        ) + score_zero_for_absent(self.fluency_animals_score)

    def get_follow_command_score(self) -> int:
        if self.lang_follow_command_practice != 1:
            return 0
        return self.sum_fields(self.LANG_FOLLOW_CMD_FIELDS)

    def get_repeat_word_score(self) -> int:
        n = self.sum_fields(self.LANG_REPEAT_WORD_FIELDS)
        return 2 if n >= 4 else (1 if n == 3 else 0)

    def lang_score(self) -> int:
        return (
            self.sum_fields(self.LANG_SIMPLE_SCORE_FIELDS)
            + self.get_follow_command_score()
            + self.get_repeat_word_score()
            + score_zero_for_absent(self.lang_read_words_aloud)
        )

    def vsp_score(self) -> int:
        return (
            self.sum_fields(self.VSP_SIMPLE_SCORE_FIELDS)
            + score_zero_for_absent(self.vsp_copy_infinity)
            + score_zero_for_absent(self.vsp_copy_cube)
            + score_zero_for_absent(self.vsp_draw_clock)
        )

    def total_score(self) -> int:
        return (
            self.attn_score()
            + self.mem_score()
            + self.fluency_score()
            + self.lang_score()
            + self.vsp_score()
        )

    def mini_ace_score(self) -> int:
        return self.sum_fields(self.MINI_ACE_FIELDS)

    # noinspection PyUnresolvedReferences
    def is_recognition_complete(self) -> bool:
        return (
            (
                (
                    self.mem_recall_address1 == 1
                    and self.mem_recall_address2 == 1
                )
                or self.mem_recognize_address1 is not None
            )
            and (
                self.mem_recall_address3 == 1
                or self.mem_recognize_address2 is not None
            )
            and (
                (
                    self.mem_recall_address4 == 1
                    and self.mem_recall_address5 == 1
                )
                or self.mem_recognize_address3 is not None
            )
            and (
                self.mem_recall_address6 == 1
                or self.mem_recognize_address4 is not None
            )
            and (
                self.mem_recall_address7 == 1
                or self.mem_recognize_address5 is not None
            )
        )

    def is_complete(self) -> bool:
        if self.any_fields_none(self.BASIC_COMPLETENESS_FIELDS):
            return False
        if not self.field_contents_valid():
            return False
        if self.lang_follow_command_practice == 1 and self.any_fields_none(
            self.LANG_FOLLOW_CMD_FIELDS
        ):
            return False
        return self.is_recognition_complete()

    @classmethod
    def get_target_address_parts(
        cls, req: CamcopsRequest, task_address_version: str
    ) -> List[str]:
        """
        Returns the target address components (7 of them). This requires an
        xstring (via a request also embodying the currently selected locale)
        and the version selected for the task.

        We do this as a classmethod so it (a) saves duplication and (b) knows
        about the xstrings for ACE-III (which are shared with the Mini-ACE). A
        superclass/mixin would be an alternative.
        """
        parts = []  # type: List[str]
        for i in range(1, N_MEM_REPEAT_RECALL_ADDR + 1):
            xstringname = f"task_{task_address_version}_target_address_{i}"
            part = cls.xstring(req, xstringname)
            parts.append(part)
        return parts

    # noinspection PyUnresolvedReferences
    def get_task_html(self, req: CamcopsRequest) -> str:
        a = self.attn_score()
        m = self.mem_score()
        f = self.fluency_score()
        lang = self.lang_score()
        v = self.vsp_score()
        t = a + m + f + lang + v
        mini = self.mini_ace_score()
        target_addr = qsequence(
            self.get_target_address_parts(req, self.task_address_version)
        )
        lkb = qsequence(RECALL_WORDS)  # lemon, key, ball

        if self.is_complete():
            figsize = (
                PlotDefaults.FULLWIDTH_PLOT_WIDTH / 3,
                PlotDefaults.FULLWIDTH_PLOT_WIDTH / 4,
            )
            width = 0.9
            fig = req.create_figure(figsize=figsize)
            ax = fig.add_subplot(1, 1, 1)
            scores = numpy.array([a, m, f, lang, v])
            maxima = numpy.array(
                [ATTN_MAX, MEMORY_MAX, FLUENCY_MAX, LANG_MAX, VSP_MAX]
            )
            y = 100 * scores / maxima
            x_labels = ["Attn", "Mem", "Flu", "Lang", "VSp"]
            # noinspection PyTypeChecker
            n = len(y)
            xvar = numpy.arange(n)
            ax.bar(xvar, y, width, color="b")
            ax.set_ylabel("%", fontdict=req.fontdict)
            ax.set_xticks(xvar)
            x_offset = -0.5
            ax.set_xlim(0 + x_offset, len(scores) + x_offset)
            ax.set_xticklabels(x_labels, fontdict=req.fontdict)
            fig.tight_layout()  # or the ylabel drops off the figure
            # fig.autofmt_xdate()
            req.set_figure_font_sizes(ax)
            figurehtml = req.get_html_from_pyplot_figure(fig)
        else:
            figurehtml = "<i>Incomplete; not plotted</i>"

        return (
            self.get_standard_clinician_comments_block(req, self.comments)
            + f"""
                <div class="{CssClass.SUMMARY}">
                    <table class="{CssClass.SUMMARY}">
                        <tr>
                            {self.get_is_complete_td_pair(req)}
                            <td class="{CssClass.FIGURE}"
                                rowspan="8">{figurehtml}</td>
                        </tr>
            """
            + tr(
                "Total ACE-III score <sup>[1]</sup>",
                answer(t) + f" / {TOTAL_MAX}",
            )
            + tr_score_with_pct("Attention", a, ATTN_MAX)
            + tr_score_with_pct("Memory", m, MEMORY_MAX)
            + tr_score_with_pct("Fluency", f, FLUENCY_MAX)
            + tr_score_with_pct("Language", lang, LANG_MAX)
            + tr_score_with_pct("Visuospatial", v, VSP_MAX)
            + tr_score_with_pct(
                "Mini-ACE score <sup>[2]</sup>", mini, MINI_ACE_MAX
            )
            + f"""
                    </table>
                </div>
                <table class="{CssClass.TASKCONFIG}">
            """
            + tr_heading("Task aspect", "Setting")
            + tr_qa("Edition", self.task_edition)
            + tr_qa("Version", self.task_address_version)
            + tr_qa(
                "Remote administration?",
                get_yes_no_none(req, self.remote_administration),
            )
            + f"""
                <table class="{CssClass.TASKDETAIL}">
            """
            + tr_heading("Question", "Answer/score")
            + tr_qa(
                AGE_FTE,
                self.age_at_leaving_full_time_education,
            )
            + tr_qa(OCCUPATION, ws.webify(self.occupation))
            + tr_qa(HANDEDNESS, ws.webify(self.handedness))
            + subheading_spanning_two_columns("Attention")
            + tr(
                "Day? Date? Month? Year? Season?",
                ", ".join(
                    answer(x)
                    for x in (
                        self.attn_time1,
                        self.attn_time2,
                        self.attn_time3,
                        self.attn_time4,
                        self.attn_time5,
                    )
                ),
            )
            + tr(
                "House number/floor? Street/hospital? Town? County? Country?",
                ", ".join(
                    answer(x)
                    for x in (
                        self.attn_place1,
                        self.attn_place2,
                        self.attn_place3,
                        self.attn_place4,
                        self.attn_place5,
                    )
                ),
            )
            + tr(
                "Repeat: " + lkb,
                ", ".join(
                    answer(x)
                    for x in (
                        self.attn_repeat_word1,
                        self.attn_repeat_word2,
                        self.attn_repeat_word3,
                    )
                ),
            )
            + tr(
                "Repetition: number of trials <i>(not scored)</i>",
                answer(
                    self.attn_num_registration_trials, formatter_answer=italic
                ),
            )
            + tr(
                "Serial subtractions: First correct? Second? Third? Fourth? "
                "Fifth?",
                ", ".join(
                    answer(x)
                    for x in (
                        self.attn_serial7_subtraction1,
                        self.attn_serial7_subtraction2,
                        self.attn_serial7_subtraction3,
                        self.attn_serial7_subtraction4,
                        self.attn_serial7_subtraction5,
                    )
                ),
            )
            + subheading_spanning_two_columns("Memory (1)")
            + tr(
                "Recall: " + lkb,
                ", ".join(
                    answer(x)
                    for x in (
                        self.mem_recall_word1,
                        self.mem_recall_word2,
                        self.mem_recall_word3,
                    )
                ),
            )
            + subheading_spanning_two_columns("Fluency")
            + tr(
                "Score for words beginning with ‘P’ <i>(≥18 scores 7, 14–17 "
                "scores 6, 11–13 scores 5, 8–10 scores 4, 6–7 scores 3, "
                "4–5 scores 2, 2–3 scores 1, 0–1 scores 0)</i>",
                answer(self.fluency_letters_score) + " / 7",
            )
            + tr(
                ANIMAL_FLUENCY_SCORING_HTML,
                answer(self.fluency_animals_score) + " / 7",
            )
            + subheading_spanning_two_columns("Memory (2)")
            + tr(
                "Third trial of address registration: " + target_addr,
                ", ".join(
                    answer(x)
                    for x in (
                        self.mem_repeat_address_trial3_1,
                        self.mem_repeat_address_trial3_2,
                        self.mem_repeat_address_trial3_3,
                        self.mem_repeat_address_trial3_4,
                        self.mem_repeat_address_trial3_5,
                        self.mem_repeat_address_trial3_6,
                        self.mem_repeat_address_trial3_7,
                    )
                ),
            )
            + tr(
                "Current PM? First female PM? USA president? USA president "
                "assassinated in 1960s?",
                ", ".join(
                    answer(x)
                    for x in (
                        self.mem_famous1,
                        self.mem_famous2,
                        self.mem_famous3,
                        self.mem_famous4,
                    )
                ),
            )
            + subheading_spanning_two_columns("Language")
            + tr(
                "<i>Practice trial (“Pick up the pencil and then the "
                "paper”)</i>",
                answer(
                    self.lang_follow_command_practice, formatter_answer=italic
                ),
            )
            + tr_qa(
                "“Place the paper on top of the pencil”",
                self.lang_follow_command1,
            )
            + tr_qa(
                "“Pick up the pencil but not the paper”",
                self.lang_follow_command2,
            )
            + tr_qa(
                "“Pass me the pencil after touching the paper”",
                self.lang_follow_command3,
            )
            + tr(
                "Sentence-writing: point for 2 complete sentences? "
                "Point for correct grammar and spelling?",
                ", ".join(
                    answer(x)
                    for x in (
                        self.lang_write_sentences_point1,
                        self.lang_write_sentences_point2,
                    )
                ),
            )
            + tr(
                "Repeat: caterpillar? eccentricity? unintelligible? "
                "statistician? <i>(score 2 if all correct, 1 if 3 correct, "
                "0 if ≤2 correct)</i>",
                "<i>{}, {}, {}, {}</i> (score <b>{}</b> / 2)".format(
                    answer(self.lang_repeat_word1, formatter_answer=italic),
                    answer(self.lang_repeat_word2, formatter_answer=italic),
                    answer(self.lang_repeat_word3, formatter_answer=italic),
                    answer(self.lang_repeat_word4, formatter_answer=italic),
                    self.get_repeat_word_score(),
                ),
            )
            + tr_qa(
                "Repeat: “All that glitters is not gold”?",
                self.lang_repeat_sentence1,
            )
            + tr_qa(
                "Repeat: “A stitch in time saves nine”?",
                self.lang_repeat_sentence2,
            )
            + tr(
                "Name pictures: spoon, book, kangaroo/wallaby",
                ", ".join(
                    answer(x)
                    for x in (
                        self.lang_name_picture1,
                        self.lang_name_picture2,
                        self.lang_name_picture3,
                    )
                ),
            )
            + tr(
                "Name pictures: penguin, anchor, camel/dromedary",
                ", ".join(
                    answer(x)
                    for x in (
                        self.lang_name_picture4,
                        self.lang_name_picture5,
                        self.lang_name_picture6,
                    )
                ),
            )
            + tr(
                "Name pictures: harp, rhinoceros/rhino, barrel/keg/tub",
                ", ".join(
                    answer(x)
                    for x in (
                        self.lang_name_picture7,
                        self.lang_name_picture8,
                        self.lang_name_picture9,
                    )
                ),
            )
            + tr(
                "Name pictures: crown, alligator/crocodile, "
                "accordion/piano accordion/squeeze box",
                ", ".join(
                    answer(x)
                    for x in (
                        self.lang_name_picture10,
                        self.lang_name_picture11,
                        self.lang_name_picture12,
                    )
                ),
            )
            + tr(
                "Identify pictures: monarchy? marsupial? Antarctic? nautical?",
                ", ".join(
                    answer(x)
                    for x in (
                        self.lang_identify_concept1,
                        self.lang_identify_concept2,
                        self.lang_identify_concept3,
                        self.lang_identify_concept4,
                    )
                ),
            )
            + tr_qa(
                "Read all successfully: sew, pint, soot, dough, height",
                self.lang_read_words_aloud,
            )
            + subheading_spanning_two_columns("Visuospatial")
            + tr("Copy infinity", answer(self.vsp_copy_infinity) + " / 1")
            + tr("Copy cube", answer(self.vsp_copy_cube) + " / 2")
            + tr(
                "Draw clock with numbers and hands at 5:10",
                answer(self.vsp_draw_clock) + " / 5",
            )
            + tr(
                "Count dots: 8, 10, 7, 9",
                ", ".join(
                    answer(x)
                    for x in (
                        self.vsp_count_dots1,
                        self.vsp_count_dots2,
                        self.vsp_count_dots3,
                        self.vsp_count_dots4,
                    )
                ),
            )
            + tr(
                "Identify letters: K, M, A, T",
                ", ".join(
                    answer(x)
                    for x in (
                        self.vsp_identify_letter1,
                        self.vsp_identify_letter2,
                        self.vsp_identify_letter3,
                        self.vsp_identify_letter4,
                    )
                ),
            )
            + subheading_spanning_two_columns("Memory (3)")
            + tr(
                "Recall address: " + target_addr,
                ", ".join(
                    answer(x)
                    for x in (
                        self.mem_recall_address1,
                        self.mem_recall_address2,
                        self.mem_recall_address3,
                        self.mem_recall_address4,
                        self.mem_recall_address5,
                        self.mem_recall_address6,
                        self.mem_recall_address7,
                    )
                ),
            )
            + tr(
                "Recognize address: forename and surname?",
                self.get_recog_text(
                    (
                        self.mem_recall_address1 == 1
                        and self.mem_recall_address2 == 1
                    ),
                    self.mem_recognize_address1,
                ),
            )
            + tr(
                "Recognize address: house number?",
                self.get_recog_text(
                    (self.mem_recall_address3 == 1),
                    self.mem_recognize_address2,
                ),
            )
            + tr(
                "Recognize address: street?",
                self.get_recog_text(
                    (
                        self.mem_recall_address4 == 1
                        and self.mem_recall_address5 == 1
                    ),
                    self.mem_recognize_address3,
                ),
            )
            + tr(
                "Recognize address: town?",
                self.get_recog_text(
                    (self.mem_recall_address6 == 1),
                    self.mem_recognize_address4,
                ),
            )
            + tr(
                "Recognize address: county?",
                self.get_recog_text(
                    (self.mem_recall_address7 == 1),
                    self.mem_recognize_address5,
                ),
            )
            + subheading_spanning_two_columns("Photos of test sheet")
            + tr_span_col(
                get_blob_img_html(self.picture1), td_class=CssClass.PHOTO
            )
            + tr_span_col(
                get_blob_img_html(self.picture2), td_class=CssClass.PHOTO
            )
            + f"""
                </table>
                <div class="{CssClass.FOOTNOTES}">
                    [1] In the ACE-III, scores ≤82 had sensitivity 0.93 and
                    specificity 1.0 for dementia, and scores ≤88 had
                    sensitivity 1.0 and specificity 0.98 for dementia, in a
                    context of patients with Alzheimer’s disease,
                    frontotemporal dementia, and controls (Hsieh et al., 2013,
                    PMID 23949210).

                    [2] {MINI_ACE_THRESHOLDS}
                </div>
                <div class="{CssClass.COPYRIGHT}">
                    {ACE3_COPYRIGHT}
                </div>
            """
        )

    def get_snomed_codes(self, req: CamcopsRequest) -> List[SnomedExpression]:
        codes = [
            SnomedExpression(
                req.snomed(SnomedLookup.ACE_R_PROCEDURE_ASSESSMENT)
            )
        ]
        # add(SnomedLookup.ACE_R_PROCEDURE_ASSESSMENT_SUBSCALE_ATTENTION_ORIENTATION)  # noqa
        # add(SnomedLookup.ACE_R_PROCEDURE_ASSESSMENT_SUBSCALE_MEMORY)
        # add(SnomedLookup.ACE_R_PROCEDURE_ASSESSMENT_SUBSCALE_FLUENCY)
        # add(SnomedLookup.ACE_R_PROCEDURE_ASSESSMENT_SUBSCALE_LANGUAGE)
        # add(SnomedLookup.ACE_R_PROCEDURE_ASSESSMENT_SUBSCALE_VISUOSPATIAL)
        if self.is_complete():  # could refine: is each subscale complete?
            a = self.attn_score()
            m = self.mem_score()
            f = self.fluency_score()
            lang = self.lang_score()
            v = self.vsp_score()
            t = a + m + f + lang + v
            codes.append(
                SnomedExpression(
                    req.snomed(SnomedLookup.ACE_R_SCALE),
                    {
                        req.snomed(SnomedLookup.ACE_R_SCORE): t,
                        req.snomed(
                            SnomedLookup.ACE_R_SUBSCORE_ATTENTION_ORIENTATION
                        ): a,  # noqa
                        req.snomed(SnomedLookup.ACE_R_SUBSCORE_MEMORY): m,
                        req.snomed(SnomedLookup.ACE_R_SUBSCORE_FLUENCY): f,
                        req.snomed(SnomedLookup.ACE_R_SUBSCORE_LANGUAGE): lang,
                        req.snomed(
                            SnomedLookup.ACE_R_SUBSCORE_VISUOSPATIAL
                        ): v,
                    },
                )
            )
        # There's no mini-ACE code in SNOMED-CT yet, as of 2022-12-01.
        return codes


# =============================================================================
# Mini-ACE
# =============================================================================


class MiniAceMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(
        cls: Type["MiniAce"],
        name: str,
        bases: Tuple[Type, ...],
        classdict: Dict[str, Any],
    ) -> None:
        add_multiple_columns(
            cls,
            "attn_time",
            1,
            N_ATTN_TIME_MINIACE,  # 4, not 5
            pv=PV.BIT,
            comment_fmt="Attention, time, {n}/4, {s} (0 or 1)",
            comment_strings=["day", "date", "month", "year"],  # not season
        )
        add_multiple_columns(
            cls,
            "mem_repeat_address_trial1_",
            1,
            N_MEM_REPEAT_RECALL_ADDR,
            pv=PV.BIT,
            comment_fmt="Memory, address registration trial 1/3 "
            "(not scored), {s} (0 or 1)",
            comment_strings=ADDRESS_PARTS,
        )
        add_multiple_columns(
            cls,
            "mem_repeat_address_trial2_",
            1,
            N_MEM_REPEAT_RECALL_ADDR,
            pv=PV.BIT,
            comment_fmt="Memory, address registration trial 2/3 "
            "(not scored), {s} (0 or 1)",
            comment_strings=ADDRESS_PARTS,
        )
        add_multiple_columns(
            cls,
            "mem_repeat_address_trial3_",
            1,
            N_MEM_REPEAT_RECALL_ADDR,
            pv=PV.BIT,
            comment_fmt="Memory, address registration trial 3/3 "
            "(scored), {s} (0 or 1)",
            comment_strings=ADDRESS_PARTS,
        )
        add_multiple_columns(
            cls,
            "mem_recall_address",
            1,
            N_MEM_REPEAT_RECALL_ADDR,
            pv=PV.BIT,
            comment_fmt="Memory, recall address {n}/7, {s} (0-1)",
            comment_strings=ADDRESS_PARTS,
        )

        super().__init__(name, bases, classdict)


class MiniAce(
    TaskHasPatientMixin,
    TaskHasClinicianMixin,
    Task,
    metaclass=MiniAceMetaclass,
):
    """
    Server implementation of the Mini-ACE task.
    """

    __tablename__ = "miniace"
    shortname = "Mini-ACE"
    extrastring_taskname = "ace3"  # shares strings with ACE-III
    provides_trackers = True

    prohibits_commercial = True

    task_edition = CamcopsColumn(
        "task_edition",
        String(length=255),
        comment="Task edition.",
    )
    task_address_version = CamcopsColumn(
        "task_address_version",
        String(length=1),
        comment="Task version, determining the address for recall (A/B/C).",
        permitted_value_checker=PermittedValueChecker(
            permitted_values=["A", "B", "C"]
        ),
    )  # type: str
    remote_administration = CamcopsColumn(
        "remote_administration",
        Boolean,
        permitted_value_checker=BIT_CHECKER,
        comment="Task performed using remote (videoconferencing) "
        "administration?",
    )
    age_at_leaving_full_time_education = Column(
        "age_at_leaving_full_time_education",
        Integer,
        comment="Age at leaving full time education",
    )
    occupation = Column("occupation", UnicodeText, comment=OCCUPATION)
    handedness = CamcopsColumn(
        "handedness",
        String(length=1),  # was Text
        comment="Handedness (L or R)",
        permitted_value_checker=PermittedValueChecker(
            permitted_values=["L", "R"]
        ),
    )
    fluency_animals_score = CamcopsColumn(
        "fluency_animals_score",
        Integer,
        comment="Fluency, animals, score 0-7",
        permitted_value_checker=PermittedValueChecker(minimum=0, maximum=7),
    )  # type: Optional[int]
    vsp_draw_clock = CamcopsColumn(
        "vsp_draw_clock",
        Integer,
        comment="Visuospatial, draw clock (0-5)",
        permitted_value_checker=PermittedValueChecker(minimum=0, maximum=5),
    )  # type: Optional[int]
    picture1_blobid = CamcopsColumn(
        "picture1_blobid",
        Integer,
        comment="Photo 1/2 PNG BLOB ID",
        is_blob_id_field=True,
        blob_relationship_attr_name="picture1",
    )
    picture2_blobid = CamcopsColumn(
        "picture2_blobid",
        Integer,
        comment="Photo 2/2 PNG BLOB ID",
        is_blob_id_field=True,
        blob_relationship_attr_name="picture2",
    )
    comments = Column("comments", UnicodeText, comment="Clinician's comments")

    picture1 = blob_relationship(
        "MiniAce", "picture1_blobid"
    )  # type: Optional[Blob]
    picture2 = blob_relationship(
        "MiniAce", "picture2_blobid"
    )  # type: Optional[Blob]

    MACE_ATTN_FIELDS = strseq("attn_time", 1, N_ATTN_TIME_MINIACE)  # 4 points
    MACE_MEMORY_FIELDS = strseq("mem_repeat_address_trial3_", 1, 7) + strseq(
        "mem_recall_address", 1, 7
    )  # 14 points
    MACE_FLUENCY_FIELDS = ["fluency_animals_score"]  # 7 points
    MACE_VSP_FIELDS = ["vsp_draw_clock"]  # 5 points
    MINI_ACE_FIELDS = (
        MACE_ATTN_FIELDS
        + MACE_MEMORY_FIELDS
        + MACE_FLUENCY_FIELDS
        + MACE_VSP_FIELDS
    )

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Mini-Addenbrooke’s Cognitive Examination")

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [
            TrackerInfo(
                value=self.mini_ace_score(),
                plot_label="Mini-ACE score",
                axis_label=f"Mini-ACE score (out of {MINI_ACE_MAX})",
                axis_min=-0.5,
                axis_max=MINI_ACE_MAX + 0.5,
                # Traditional cutoffs: ≤21, ≤25
                horizontal_lines=[21.5, 25.5],
            ),
        ]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        a = self.attn_score()
        m = self.mem_score()
        f = self.fluency_score()
        v = self.vsp_score()
        mini = a + m + f + v
        text = (
            f"Mini-ACE score: {mini}/{MINI_ACE_MAX} "
            f"(attention {a}/{ATTN_MINIACE_MAX}, "
            f"memory {m}/{MEM_MINIACE_MAX}, "
            f"fluency {f}/{FLUENCY_MINIACE_MAX}, "
            f"visuospatial {v}/{VSP_MINIACE_MAX})"
        )
        return [CtvInfo(content=text)]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="mini_ace",
                coltype=Integer(),
                value=self.mini_ace_score(),
                comment=f"Mini-ACE (/{MINI_ACE_MAX})",
            ),
        ]

    def attn_score(self) -> int:
        return self.sum_fields(self.MACE_ATTN_FIELDS)

    def mem_score(self) -> int:
        return self.sum_fields(self.MACE_MEMORY_FIELDS)

    def fluency_score(self) -> int:
        return self.sum_fields(self.MACE_FLUENCY_FIELDS)

    def vsp_score(self) -> int:
        return self.sum_fields(self.MACE_VSP_FIELDS)

    def mini_ace_score(self) -> int:
        return self.sum_fields(self.MINI_ACE_FIELDS)

    def is_complete(self) -> bool:
        return (
            self.all_fields_not_none(self.MINI_ACE_FIELDS)
            and self.field_contents_valid()
        )

    def get_task_html(self, req: CamcopsRequest) -> str:
        a = self.attn_score()
        m = self.mem_score()
        f = self.fluency_score()
        v = self.vsp_score()
        mini = a + m + f + v
        target_addr = qsequence(
            Ace3.get_target_address_parts(req, self.task_address_version)
        )

        if self.is_complete():
            figsize = (
                PlotDefaults.FULLWIDTH_PLOT_WIDTH / 3,
                PlotDefaults.FULLWIDTH_PLOT_WIDTH / 4,
            )
            width = 0.9
            fig = req.create_figure(figsize=figsize)
            ax = fig.add_subplot(1, 1, 1)
            scores = numpy.array([a, m, f, v])
            maxima = numpy.array(
                [
                    ATTN_MINIACE_MAX,
                    MEM_MINIACE_MAX,
                    FLUENCY_MINIACE_MAX,
                    VSP_MINIACE_MAX,
                ]
            )
            y = 100 * scores / maxima
            x_labels = ["Attn", "Mem", "Flu", "VSp"]
            # noinspection PyTypeChecker
            n = len(y)
            xvar = numpy.arange(n)
            ax.bar(xvar, y, width, color="g")
            ax.set_ylabel("%", fontdict=req.fontdict)
            ax.set_xticks(xvar)
            x_offset = -0.5
            ax.set_xlim(0 + x_offset, len(scores) + x_offset)
            ax.set_xticklabels(x_labels, fontdict=req.fontdict)
            fig.tight_layout()  # or the ylabel drops off the figure
            # fig.autofmt_xdate()
            req.set_figure_font_sizes(ax)
            figurehtml = req.get_html_from_pyplot_figure(fig)
        else:
            figurehtml = "<i>Incomplete; not plotted</i>"

        return (
            self.get_standard_clinician_comments_block(req, self.comments)
            + f"""
                <div class="{CssClass.SUMMARY}">
                    <table class="{CssClass.SUMMARY}">
                        <tr>
                            {self.get_is_complete_td_pair(req)}
                            <td class="{CssClass.FIGURE}"
                                rowspan="6">{figurehtml}</td>
                        </tr>
            """
            + tr_score_with_pct(
                "Mini-ACE score <sup>[1]</sup>", mini, MINI_ACE_MAX
            )
            + tr_score_with_pct("Attention", a, ATTN_MINIACE_MAX)
            + tr_score_with_pct("Memory", m, MEM_MINIACE_MAX)
            + tr_score_with_pct("Fluency", f, FLUENCY_MINIACE_MAX)
            + tr_score_with_pct("Visuospatial", v, VSP_MINIACE_MAX)
            + f"""
                    </table>
                </div>
                <table class="{CssClass.TASKCONFIG}">
            """
            + tr_heading("Task aspect", "Setting")
            + tr_qa("Edition", self.task_edition)
            + tr_qa("Version", self.task_address_version)
            + tr_qa(
                "Remote administration?",
                get_yes_no_none(req, self.remote_administration),
            )
            + f"""
                <table class="{CssClass.TASKDETAIL}">
            """
            + tr_heading("Question", "Answer/score")
            + tr_qa(
                AGE_FTE,
                self.age_at_leaving_full_time_education,
            )
            + tr_qa(OCCUPATION, ws.webify(self.occupation))
            + tr_qa(HANDEDNESS, ws.webify(self.handedness))
            + subheading_spanning_two_columns("Attention")
            + tr(
                "Day? Date? Month? Year?",  # not season
                ", ".join(
                    answer(x)
                    for x in (
                        self.attn_time1,
                        self.attn_time2,
                        self.attn_time3,
                        self.attn_time4,
                    )
                ),
            )
            + subheading_spanning_two_columns("Memory")
            + tr(
                "Third trial of address registration: " + target_addr,
                ", ".join(
                    answer(x)
                    for x in (
                        self.mem_repeat_address_trial3_1,
                        self.mem_repeat_address_trial3_2,
                        self.mem_repeat_address_trial3_3,
                        self.mem_repeat_address_trial3_4,
                        self.mem_repeat_address_trial3_5,
                        self.mem_repeat_address_trial3_6,
                        self.mem_repeat_address_trial3_7,
                    )
                ),
            )
            + subheading_spanning_two_columns("Fluency – animals")
            + tr(
                ANIMAL_FLUENCY_SCORING_HTML,
                answer(self.fluency_animals_score) + " / 7",
            )
            + subheading_spanning_two_columns("Clock drawing")
            + tr(
                "Draw clock with numbers and hands at 5:10",
                answer(self.vsp_draw_clock) + " / 5",
            )
            + subheading_spanning_two_columns("Memory recall")
            + tr(
                "Recall address: " + target_addr,
                ", ".join(
                    answer(x)
                    for x in (
                        self.mem_recall_address1,
                        self.mem_recall_address2,
                        self.mem_recall_address3,
                        self.mem_recall_address4,
                        self.mem_recall_address5,
                        self.mem_recall_address6,
                        self.mem_recall_address7,
                    )
                ),
            )
            + subheading_spanning_two_columns("Photos of test sheet")
            + tr_span_col(
                get_blob_img_html(self.picture1), td_class=CssClass.PHOTO
            )
            + tr_span_col(
                get_blob_img_html(self.picture2), td_class=CssClass.PHOTO
            )
            + f"""
                </table>
                <div class="{CssClass.FOOTNOTES}">
                    [1] {MINI_ACE_THRESHOLDS}
                </div>
                <div class="{CssClass.COPYRIGHT}">
                    {ACE3_COPYRIGHT}
                </div>
            """
        )
