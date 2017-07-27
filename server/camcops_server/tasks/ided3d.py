#!/usr/bin/env python
# camcops_server/tasks/ided3d.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

from typing import Any, List

import cardinal_pythonlib.rnc_web as ws

from ..cc_modules.cc_constants import PV
from ..cc_modules.cc_html import (
    answer,
    get_yes_no_none,
    identity,
    tr,
    tr_qa,
)
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_task import Ancillary, Task


def a(x: Any) -> str:
    """Answer formatting for this task."""
    return answer(x, formatter_answer=identity, default="")


# =============================================================================
# IDED3D
# =============================================================================

class IDED3DTrial(Ancillary):
    tablename = "ided3d_trials"
    fkname = "ided3d_id"
    fieldspecs = [
        dict(name="ided3d_id", notnull=True,
             cctype="INT", comment="FK to ided3d"),
        dict(name="trial", notnull=True, cctype="INT",
             comment="Trial number (1-based)"),
        dict(name="stage", cctype="INT", comment="Stage number (1-based)"),
        # Locations
        dict(name="correct_location", cctype="INT",
             comment="Location of correct stimulus "
                     "(0 top, 1 right, 2 bottom, 3 left)"),
        dict(name="incorrect_location", cctype="INT",
             comment="Location of incorrect stimulus "
                     "(0 top, 1 right, 2 bottom, 3 left)"),
        # Stimuli
        dict(name="correct_shape", cctype="INT",
             comment="Shape# of correct stimulus"),
        dict(name="correct_colour", cctype="TEXT",
             comment="HTML colour of correct stimulus"),
        dict(name="correct_number", cctype="INT",
             comment="Number of copies of correct stimulus"),
        dict(name="incorrect_shape", cctype="INT",
             comment="Shape# of incorrect stimulus"),
        dict(name="incorrect_colour", cctype="TEXT",
             comment="HTML colour of incorrect stimulus"),
        dict(name="incorrect_number", cctype="INT",
             comment="Number of copies of incorrect stimulus"),
        # Trial
        dict(name="trial_start_time", cctype="ISO8601",
             comment="Trial start time / stimuli presented at (ISO-8601)"),
        # Response
        dict(name="responded", cctype="BOOL", pv=PV.BIT,
             comment="Trial start time / stimuli presented at (ISO-8601)"),
        dict(name="response_time", cctype="ISO8601",
             comment="Time of response (ISO-8601)"),
        dict(name="response_latency_ms", cctype="INT",
             comment="Response latency (ms)"),
        dict(name="correct", cctype="BOOL", pv=PV.BIT,
             comment="Response was correct"),
        dict(name="incorrect", cctype="BOOL", pv=PV.BIT,
             comment="Response was incorrect"),
    ]
    sortfield = "trial"

    @classmethod
    def get_html_table_header(cls) -> str:
        return """
            <table class="extradetail">
                <tr>
                    <th>Trial</th>
                    <th>Stage</th>
                    <th>Correct location</th>
                    <th>Incorrect location</th>
                    <th>Correct shape</th>
                    <th>Correct colour</th>
                    <th>Correct number</th>
                    <th>Incorrect shape</th>
                    <th>Incorrect colour</th>
                    <th>Incorrect number</th>
                    <th>Trial start time</th>
                    <th>Responded?</th>
                    <th>Response time</th>
                    <th>Response latency (ms)</th>
                    <th>Correct?</th>
                    <th>Incorrect?</th>
                </tr>
        """

    def get_html_table_row(self) -> str:
        return tr(
            a(self.trial),
            a(self.stage),
            a(self.correct_location),
            a(self.incorrect_location),
            a(self.correct_shape),
            a(self.correct_colour),
            a(self.correct_number),
            a(self.incorrect_shape),
            a(self.incorrect_colour),
            a(self.incorrect_number),
            a(self.trial_start_time),
            a(self.responded),
            a(self.response_time),
            a(self.response_latency_ms),
            a(self.correct),
            a(self.incorrect),
        )


class IDED3DStage(Ancillary):
    tablename = "ided3d_stages"
    fkname = "ided3d_id"
    fieldspecs = [
        dict(name="ided3d_id", notnull=True,
             cctype="INT", comment="FK to ided3d"),
        dict(name="stage", notnull=True, cctype="INT",
             comment="Stage number (1-based)"),
        # Config
        dict(name="stage_name", cctype="TEXT",
             comment="Name of the stage (e.g. SD, EDr)"),
        dict(name="relevant_dimension", cctype="TEXT",
             comment="Relevant dimension (e.g. shape, colour, number)"),
        dict(name="correct_exemplar", cctype="TEXT",
             comment="Correct exemplar (from relevant dimension)"),
        dict(name="incorrect_exemplar", cctype="TEXT",
             comment="Incorrect exemplar (from relevant dimension)"),
        dict(name="correct_stimulus_shapes", cctype="TEXT",
             comment="Possible shapes for correct stimulus "
                     "(CSV list of shape numbers)"),
        dict(name="correct_stimulus_colours", cctype="TEXT",
             comment="Possible colours for correct stimulus "
                     "(CSV list of HTML colours)"),
        dict(name="correct_stimulus_numbers", cctype="TEXT",
             comment="Possible numbers for correct stimulus "
                     "(CSV list of numbers)"),
        dict(name="incorrect_stimulus_shapes", cctype="TEXT",
             comment="Possible shapes for incorrect stimulus "
                     "(CSV list of shape numbers)"),
        dict(name="incorrect_stimulus_colours", cctype="TEXT",
             comment="Possible colours for incorrect stimulus "
                     "(CSV list of HTML colours)"),
        dict(name="incorrect_stimulus_numbers", cctype="TEXT",
             comment="Possible numbers for incorrect stimulus "
                     "(CSV list of numbers)"),
        # Results
        dict(name="first_trial_num", cctype="INT",
             comment="Number of the first trial of the stage (1-based)"),
        dict(name="n_completed_trials", cctype="INT",
             comment="Number of trials completed"),
        dict(name="n_correct", cctype="INT",
             comment="Number of trials performed correctly"),
        dict(name="n_incorrect", cctype="INT",
             comment="Number of trials performed incorrectly"),
        dict(name="stage_passed", cctype="BOOL", pv=PV.BIT,
             comment="Subject met criterion and passed stage"),
        dict(name="stage_failed", cctype="BOOL", pv=PV.BIT,
             comment="Subject took too many trials and failed stage"),
    ]
    sortfield = "stage"

    @classmethod
    def get_html_table_header(cls) -> str:
        return """
            <table class="extradetail">
                <tr>
                    <th>Stage#</th>
                    <th>Stage name</th>
                    <th>Relevant dimension</th>
                    <th>Correct exemplar</th>
                    <th>Incorrect exemplar</th>
                    <th>Shapes for correct</th>
                    <th>Colours for correct</th>
                    <th>Numbers for correct</th>
                    <th>Shapes for incorrect</th>
                    <th>Colours for incorrect</th>
                    <th>Numbers for incorrect</th>
                    <th>First trial#</th>
                    <th>#completed trials</th>
                    <th>#correct</th>
                    <th>#incorrect</th>
                    <th>Passed?</th>
                    <th>Failed?</th>
                </tr>
        """

    def get_html_table_row(self) -> str:
        return tr(
            a(self.stage),
            a(self.stage_name),
            a(self.relevant_dimension),
            a(self.correct_exemplar),
            a(self.incorrect_exemplar),
            a(self.correct_stimulus_shapes),
            a(self.correct_stimulus_colours),
            a(self.correct_stimulus_numbers),
            a(self.incorrect_stimulus_shapes),
            a(self.incorrect_stimulus_colours),
            a(self.incorrect_stimulus_numbers),
            a(self.first_trial_num),
            a(self.n_completed_trials),
            a(self.n_correct),
            a(self.n_incorrect),
            a(self.stage_passed),
            a(self.stage_failed),
        )


class IDED3D(Task):
    tablename = "ided3d"
    shortname = "ID/ED-3D"
    longname = "Three-dimensional ID/ED task"
    dependent_classes = [IDED3DTrial, IDED3DStage]

    fieldspecs = [
        # Config
        dict(name="last_stage", cctype="INT",
             comment="Last stage to offer (1 [SD] - 8 [EDR])"),
        dict(name="max_trials_per_stage", cctype="INT",
             comment="Maximum number of trials allowed per stage before "
                     "the task aborts"),
        dict(name="progress_criterion_x", cctype="INT",
             comment='Criterion to proceed to next stage: X correct out of'
                     ' the last Y trials, where this is X'),
        dict(name="progress_criterion_y", cctype="INT",
             comment='Criterion to proceed to next stage: X correct out of'
                     ' the last Y trials, where this is Y'),
        dict(name="min_number", cctype="INT",
             comment="Minimum number of stimulus element to use"),
        dict(name="max_number", cctype="INT",
             comment="Maximum number of stimulus element to use"),
        dict(name="pause_after_beep_ms", cctype="INT",
             comment="Time to continue visual feedback after auditory "
                     "feedback finished (ms)"),
        dict(name="iti_ms", cctype="INT",
             comment="Intertrial interval (ms)"),
        dict(name="counterbalance_dimensions", cctype="INT",
             comment="Dimensional counterbalancing condition (0-5)"),
        dict(name="volume", cctype="FLOAT",
             comment="Sound volume (0.0-1.0)"),
        dict(name="offer_abort", cctype="BOOL", pv=PV.BIT,
             comment="Offer an abort button?"),
        dict(name="debug_display_stimuli_only", cctype="BOOL", pv=PV.BIT,
             comment="DEBUG: show stimuli only, don't run task"),
        # Intrinsic config
        dict(name="shape_definitions_svg", cctype="TEXT",
             comment="JSON-encoded version of shape definition"
                     " array in SVG format (with arbitrary scale of -60 to"
                     " +60 in both X and Y dimensions)"),
        dict(name="colour_definitions_rgb", cctype="TEXT",  # v2.0.0
             comment="JSON-encoded version of colour RGB definitions"),
        # Results
        dict(name="aborted", cctype="INT",
             comment="Was the task aborted? (0 no, 1 yes)"),
        dict(name="finished", cctype="INT",
             comment="Was the task finished? (0 no, 1 yes)"),
        dict(name="last_trial_completed", cctype="INT",
             comment="Number of last trial completed"),
    ]

    def is_complete(self) -> bool:
        return bool(self.debug_display_stimuli_only) or bool(self.finished)

    @staticmethod
    def get_stage_html(stagearray: List[IDED3DStage]) -> str:
        html = IDED3DStage.get_html_table_header()
        for s in stagearray:
            html += s.get_html_table_row()
        html += """</table>"""
        return html

    @staticmethod
    def get_trial_html(trialarray: List[IDED3DTrial]) -> str:
        html = IDED3DTrial.get_html_table_header()
        for t in trialarray:
            html += t.get_html_table_row()
        html += """</table>"""
        return html

    def get_stage_array(self) -> List[IDED3DStage]:
        # Fetch group details
        return self.get_ancillary_items(IDED3DStage)

    def get_trial_array(self) -> List[IDED3DTrial]:
        # Fetch trial details
        return self.get_ancillary_items(IDED3DTrial)

    def get_task_html(self) -> str:
        stagearray = self.get_stage_array()
        trialarray = self.get_trial_array()
        # THIS IS A NON-EDITABLE TASK, so we *ignore* the problem
        # of matching to no-longer-current records.
        # (See PhotoSequence.py for a task that does it properly.)

        # Provide HTML
        # HTML
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                </table>
            </div>
            <div class="explanation">
                1. Simple discrimination (SD), and 2. reversal (SDr);
                3. compound discrimination (CD), and 4. reversal (CDr);
                5. intradimensional shift (ID), and 6. reversal (IDr);
                7. extradimensional shift (ED), and 8. reversal (EDr).
            </div>
            <table class="taskconfig">
                <tr>
                    <th width="50%">Configuration variable</th>
                    <th width="50%">Value</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
        )
        h += tr_qa(self.wxstring("last_stage"), self.last_stage)
        h += tr_qa(self.wxstring("max_trials_per_stage"),
                   self.max_trials_per_stage)
        h += tr_qa(self.wxstring("progress_criterion_x"),
                   self.progress_criterion_x)
        h += tr_qa(self.wxstring("progress_criterion_y"),
                   self.progress_criterion_y)
        h += tr_qa(self.wxstring("min_number"), self.min_number)
        h += tr_qa(self.wxstring("max_number"), self.max_number)
        h += tr_qa(self.wxstring("pause_after_beep_ms"),
                   self.pause_after_beep_ms)
        h += tr_qa(self.wxstring("iti_ms"), self.iti_ms)
        h += tr_qa(
            self.wxstring("counterbalance_dimensions") + "<sup>[1]</sup>",
            self.counterbalance_dimensions)
        h += tr_qa(wappstring("volume_0_to_1"), self.volume)
        h += tr_qa(self.wxstring("offer_abort"), self.offer_abort)
        h += tr_qa(self.wxstring("debug_display_stimuli_only"),
                   self.debug_display_stimuli_only)
        h += tr_qa("Shapes (as a JSON-encoded array of SVG "
                   "definitions; X and Y range both –60 to +60)",
                   ws.webify(self.shape_definitions_svg))
        h += """
            </table>
            <table class="taskdetail">
                <tr><th width="50%">Measure</th><th width="50%">Value</th></tr>
        """
        h += tr_qa("Aborted?", get_yes_no_none(self.aborted))
        h += tr_qa("Finished?", get_yes_no_none(self.finished))
        h += tr_qa("Last trial completed", self.last_trial_completed)
        h += (
            """
                </table>
                <div>Stage specifications and results:</div>
            """ +
            self.get_stage_html(stagearray) +
            "<div>Trial-by-trial results:</div>" +
            self.get_trial_html(trialarray) +
            """
                <div class="footnotes">
                    [1] Counterbalancing of dimensions is as follows, with
                    notation X/Y indicating that X is the first relevant
                    dimension (for stages SD–IDr) and Y is the second relevant
                    dimension (for stages ED–EDr).
                    0: shape/colour.
                    1: colour/number.
                    2: number/shape.
                    3: shape/number.
                    4: colour/shape.
                    5: number/colour.
                </div>
            """
        )
        return h
