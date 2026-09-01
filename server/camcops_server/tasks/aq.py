"""
camcops_server/tasks/aq.py

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

**Autism Spectrum Quotient (AQ) (Adult) task.**

"""

from typing import Any, Iterable, Type

from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import answer, tr
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_text import SS
from camcops_server.tasks.aqcommon import AqCommon


def to_csv(values: Iterable[Any]) -> str:
    """
    Create a comma-separated string from iterable.
    """
    return ", ".join(str(v) for v in values)


class Aq(AqCommon):
    __tablename__ = "aq"
    shortname = "AQ"

    FIRST_Q = 1
    LAST_Q = 50
    MAX_AREA_SCORE = 10
    MAX_SCORE = 50

    @classmethod
    def extend_columns(cls: Type["Aq"], **kwargs: Any) -> None:
        add_multiple_columns(
            cls,
            cls.PREFIX,
            cls.FIRST_Q,
            cls.LAST_Q,
            coltype=Integer,
            minimum=0,
            maximum=3,
            comment_fmt=cls.PREFIX + "{n} - {s}",
            comment_strings=[
                # 1-5:
                "prefer doing things with others",
                "prefer doing things the same way",
                "can create picture in mind",
                "get strongly absorbed in one thing",
                "notice small sounds",
                # 6-10:
                "notice car number plates",
                "what I’ve said is impolite",
                "can imagine what story characters look like",
                "fascinated by dates",
                "can keep track of conversations",
                # 11-15:
                "find social situations easy",
                "notice details",
                "prefer library to party",
                "find making up stories easy",
                "drawn more strongly to people",
                # 16-20:
                "upset if can't pursue strong interests",
                "enjoy chit-chat",
                "not easy for others to get a word in edgeways",
                "fascinated by numbers",
                "can't work out story characters’ intentions",
                # 21-25:
                "don’t enjoy fiction",
                "hard to make new friends",
                "notice patterns",
                "prefer theatre to museum",
                "not upset if daily routine disturbed",
                # 26-30:
                "don't know how to keep conversation going",
                "easy to read between the lines",
                "concentrate more on whole picture",
                "can't remember phone numbers",
                "don’t notice small changes",
                # 31-35:
                "can tell if person listening is bored",
                "easy to do more than one thing",
                "not sure when to speak on phone",
                "enjoy doing things spontaneously",
                "last to understand joke",
                # 36-40:
                "can work out thinking or feeling from face",
                "can switch back after interruption",
                "good at chit-chat",
                "keep going on and on about the same thing",
                "used to enjoy pretending games with other children",
                # 41-45:
                "like to collect information about categories of things",
                "difficult to imagine being someone else",
                "like to plan activities carefully",
                "enjoy social occasions",
                "difficult to work out people’s intentions",
                # 46-50:
                "new situations make me anxious",
                "enjoy meeting new people",
                "am a good diplomat",
                "not very good at remembering people’s date of birth",
                "easy to play pretending games with children",
            ],
        )

    # Questions where agreement indicates autistic-like traits.
    # As listed in Baron-Cohen et al. (2001) [see refs in aq.rst], p7:
    #   'Scoring the AQ: “Definitely agree” or “slightly agree” responses
    #   scored 1 point, on the following items: 1, 2, 4, 5, 6, 7, 9, 12, 13,
    #   16, 18, 19, 20, 21, 22, 23, 26, 33, 35, 39, 41, 42, 43, 45, 46.
    #   “Definitely disagree” or “slightly disagree” responses scored 1 point,
    #   on the following items: 3, 8, 10, 11, 14, 15, 17, 24, 25, 27, 28, 29,
    #   30, 31, 32, 34, 36, 37, 38, 40, 44, 47, 48, 49, 50.'
    # HOWEVER, there is an error here in the published paper:
    # Baron-Cohen et al. (2001) list Q1 as an "agree" question, but
    # agreement there is a preference for doing things with others versus on
    # one's own, so disagreement would be the more autistic-like answer (e.g.
    # per WHO ICD-10 criteria for F84.1). The ARC's scoring sheet lists Q1 as a
    # "disagree" question.
    # This correction is made explicit in the erratum (see aq.rst).
    AGREE_SCORING_QUESTIONS = [
        2,
        4,
        5,
        6,
        7,
        9,
        12,
        13,
        16,
        18,
        19,
        20,
        21,
        22,
        23,
        26,
        33,
        35,
        39,
        41,
        42,
        43,
        45,
        46,
    ]

    # Areas (domains): see Baron-Cohen et al. (2001), p6.
    SOCIAL_SKILL_QUESTIONS = [1, 11, 13, 15, 22, 36, 44, 45, 47, 48]
    ATTENTION_SWITCHING_QUESTIONS = [2, 4, 10, 16, 25, 32, 34, 37, 43, 46]
    ATTENTION_TO_DETAIL_QUESTIONS = [5, 6, 9, 12, 19, 23, 28, 29, 30, 49]
    COMMUNICATION_QUESTIONS = [7, 17, 18, 26, 27, 31, 33, 35, 38, 39]
    IMAGINATION_QUESTIONS = [3, 8, 14, 20, 21, 24, 40, 41, 42, 50]

    @staticmethod
    def longname(req: CamcopsRequest) -> str:
        _ = req.gettext
        return _("Autism Spectrum Quotient (Adult)")

    def get_summaries(self, req: CamcopsRequest) -> list[SummaryElement]:
        mas = self.MAX_AREA_SCORE
        return self.standard_task_summary_fields() + [
            SummaryElement(
                name="total",
                coltype=Integer(),
                value=self.score(),
                comment=f"Total score (/{self.MAX_SCORE})",
            ),
            SummaryElement(
                name="social_skill",
                coltype=Integer(),
                value=self.social_skill_score(),
                comment=f"Social skill domain score (/{mas})",
            ),
            SummaryElement(
                name="attention_switching",
                coltype=Integer(),
                value=self.attention_switching_score(),
                comment=f"Attention switching domain score (/{mas})",
            ),
            SummaryElement(
                name="attention_to_detail",
                coltype=Integer(),
                value=self.attention_to_detail_score(),
                comment=f"Attention to detail domain score (/{mas})",
            ),
            SummaryElement(
                name="communication",
                coltype=Integer(),
                value=self.communication_score(),
                comment=f"Communication domain score (/{mas})",
            ),
            SummaryElement(
                name="imagination",
                coltype=Integer(),
                value=self.imagination_score(),
                comment=f"Imagination domain score (/{mas})",
            ),
        ]

    def social_skill_score(self) -> int | None:
        return self.questions_score(self.SOCIAL_SKILL_QUESTIONS)

    def attention_switching_score(self) -> int | None:
        return self.questions_score(self.ATTENTION_SWITCHING_QUESTIONS)

    def attention_to_detail_score(self) -> int | None:
        return self.questions_score(self.ATTENTION_TO_DETAIL_QUESTIONS)

    def communication_score(self) -> int | None:
        return self.questions_score(self.COMMUNICATION_QUESTIONS)

    def imagination_score(self) -> int | None:
        return self.questions_score(self.IMAGINATION_QUESTIONS)

    def get_task_html(self, req: CamcopsRequest) -> str:
        rows = self.get_task_html_rows(req)

        html = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                    {total_score}
                    {social_skill_score}
                    {attention_switching_score}
                    {attention_to_detail_score}
                    {communication_score}
                    {imagination_score}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                {rows}
            </table>
            <div class="{CssClass.FOOTNOTES}">
                [1] Questions {social_skill_q_nums}.
                [2] Questions {attention_switching_q_nums}.
                [3] Questions {attention_to_detail_q_nums}.
                [4] Questions {communication_q_nums}.
                [5] Questions {imagination_q_nums}.
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            total_score=tr(
                req.sstring(SS.TOTAL_SCORE),
                answer(self.score()) + f" / {self.MAX_SCORE}",
            ),
            social_skill_score=tr(
                self.wxstring(req, "social_skill_score") + " <sup>[1]</sup>",
                answer(self.social_skill_score())
                + f" / {self.MAX_AREA_SCORE}",
            ),
            attention_switching_score=tr(
                self.wxstring(req, "attention_switching_score")
                + " <sup>[2]</sup>",
                answer(self.attention_switching_score())
                + f" / {self.MAX_AREA_SCORE}",
            ),
            attention_to_detail_score=tr(
                self.wxstring(req, "attention_to_detail_score")
                + " <sup>[3]</sup>",
                answer(self.attention_to_detail_score())
                + f" / {self.MAX_AREA_SCORE}",
            ),
            communication_score=tr(
                self.wxstring(req, "communication_score") + " <sup>[4]</sup>",
                answer(self.communication_score())
                + f" / {self.MAX_AREA_SCORE}",
            ),
            imagination_score=tr(
                self.wxstring(req, "imagination_score") + " <sup>[5]</sup>",
                answer(self.imagination_score()) + f" / {self.MAX_AREA_SCORE}",
            ),
            social_skill_q_nums=to_csv(self.SOCIAL_SKILL_QUESTIONS),
            attention_switching_q_nums=to_csv(
                self.ATTENTION_SWITCHING_QUESTIONS
            ),
            attention_to_detail_q_nums=to_csv(
                self.ATTENTION_TO_DETAIL_QUESTIONS
            ),
            communication_q_nums=to_csv(self.COMMUNICATION_QUESTIONS),
            imagination_q_nums=to_csv(self.IMAGINATION_QUESTIONS),
            rows=rows,
        )
        return html
