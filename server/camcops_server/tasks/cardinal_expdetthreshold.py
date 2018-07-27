#!/usr/bin/env python
# camcops_server/tasks/cardinal_expdetthreshold.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

import math
from typing import List, Optional

from cardinal_pythonlib.maths_numpy import inv_logistic, logistic
import cardinal_pythonlib.rnc_web as ws
import numpy as np
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Float, Integer, Text, UnicodeText

from camcops_server.cc_modules.cc_constants import (
    CssClass,
    FULLWIDTH_PLOT_WIDTH,
    WHOLE_PANEL,
)
from camcops_server.cc_modules.cc_db import (
    ancillary_relationship,
    GenericTabletRecordMixin,
)
from camcops_server.cc_modules.cc_html import (
    get_yes_no_none,
    tr_qa,
)
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import PendulumDateTimeAsIsoTextColType  # noqa
from camcops_server.cc_modules.cc_sqlalchemy import Base
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin


LOWER_MARKER = 0.25
UPPER_MARKER = 0.75
EQUATION_COMMENT = (
    "logits: L(X) = intercept + slope * X; "
    "probability: P = 1 / (1 + exp(-intercept - slope * X))"
)
MODALITY_AUDITORY = 0
MODALITY_VISUAL = 1
DP = 3


# =============================================================================
# CardinalExpDetThreshold
# =============================================================================

class CardinalExpDetThresholdTrial(GenericTabletRecordMixin, Base):
    __tablename__ = "cardinal_expdetthreshold_trials"

    cardinal_expdetthreshold_id = Column(
        "cardinal_expdetthreshold_id", Integer,
        nullable=False,
        comment="FK to CardinalExpDetThreshold"
    )
    trial = Column(
        "trial", Integer,
        nullable=False,
        comment="Trial number"
    )
    
    # Results
    trial_ignoring_catch_trials = Column(
        "trial_ignoring_catch_trials", Integer,
        comment="Trial number, ignoring catch trials"
    )
    target_presented = Column(
        "target_presented", Integer,
        comment="Target presented? (0 no, 1 yes)"
    )
    target_time = Column(
        "target_time", PendulumDateTimeAsIsoTextColType,
        comment="Target presentation time (ISO-8601)"
    )
    intensity = Column(
        "intensity", Float,
        comment="Target intensity (0.0-1.0)"
    )
    choice_time = Column(
        "choice_time", PendulumDateTimeAsIsoTextColType,
        comment="Time choice offered (ISO-8601)"
    )
    responded = Column(
        "responded", Integer,
        comment="Responded? (0 no, 1 yes)"
    )
    response_time = Column(
        "response_time", PendulumDateTimeAsIsoTextColType,
        comment="Time of response (ISO-8601)"
    )
    response_latency_ms = Column(
        "response_latency_ms", Integer,
        comment="Response latency (ms)"
    )
    yes = Column(
        "yes", Integer,
        comment="Subject chose YES? (0 didn't, 1 did)"
    )
    no = Column(
        "no", Integer,
        comment="Subject chose NO? (0 didn't, 1 did)"
    )
    caught_out_reset = Column(
        "caught_out_reset", Integer,
        comment="Caught out on catch trial, thus reset? (0 no, 1 yes)"
    )
    trial_num_in_calculation_sequence = Column(
        "trial_num_in_calculation_sequence", Integer,
        comment="Trial number as used for threshold calculation"
    )

    @classmethod
    def get_html_table_header(cls) -> str:
        return """
            <table class="{CssClass.EXTRADETAIL}">
                <tr>
                    <th>Trial</th>
                    <th>Trial (ignoring catch trials)</th>
                    <th>Target presented?</th>
                    <th>Target time</th>
                    <th>Intensity</th>
                    <th>Choice time</th>
                    <th>Responded?</th>
                    <th>Response time</th>
                    <th>Response latency (ms)</th>
                    <th>Yes?</th>
                    <th>No?</th>
                    <th>Caught out (and reset)?</th>
                    <th>Trial# in calculation sequence</th>
                </tr>
        """.format(CssClass=CssClass)

    def get_html_table_row(self) -> str:
        return ("<tr>" + "<td>{}</td>" * 13 + "</th>").format(
            self.trial,
            self.trial_ignoring_catch_trials,
            self.target_presented,
            self.target_time,
            ws.number_to_dp(self.intensity, DP),
            self.choice_time,
            self.responded,
            self.response_time,
            self.response_latency_ms,
            self.yes,
            self.no,
            ws.webify(self.caught_out_reset),
            ws.webify(self.trial_num_in_calculation_sequence)
        )


class CardinalExpDetThreshold(TaskHasPatientMixin, Task):
    __tablename__ = "cardinal_expdetthreshold"
    shortname = "Cardinal_ExpDetThreshold"
    longname = ("Cardinal RN – Threshold determination for "
                "Expectation–Detection task")
    use_landscape_for_pdf = True
    
    # Config
    modality = Column(
        "modality", Integer,
        comment="Modality (0 auditory, 1 visual)"
    )
    target_number = Column(
        "target_number", Integer,
        comment="Target number (within available targets of that modality)"
    )
    background_filename = Column(
        "background_filename", Text,
        comment="Filename of media used for background"
    )
    target_filename = Column(
        "target_filename", Text,
        comment="Filename of media used for target"
    )
    visual_target_duration_s = Column(
        "visual_target_duration_s", Float,
        comment="Visual target duration (s)"
    )
    background_intensity = Column(
        "background_intensity", Float,
        comment="Intensity of background (0.0-1.0)"
    )
    start_intensity_min = Column(
        "start_intensity_min", Float,
        comment="Minimum starting intensity (0.0-1.0)"
    )
    start_intensity_max = Column(
        "start_intensity_max", Float,
        comment="Maximum starting intensity (0.0-1.0)"
    )
    initial_large_intensity_step = Column(
        "initial_large_intensity_step", Float,
        comment="Initial, large, intensity step (0.0-1.0)"
    )
    main_small_intensity_step = Column(
        "main_small_intensity_step", Float,
        comment="Main, small, intensity step (0.0-1.0)"
    )
    num_trials_in_main_sequence = Column(
        "num_trials_in_main_sequence", Integer,
        comment="Number of trials required in main sequence"
    )
    p_catch_trial = Column(
        "p_catch_trial", Float,
        comment="Probability of catch trial"
    )
    prompt = Column(
        "prompt", UnicodeText,
        comment="Prompt given to subject"
    )
    iti_s = Column(
        "iti_s", Float,
        comment="Intertrial interval (s)"
    )
    
    # Results
    finished = Column(
        "finished", Integer,
        comment="Subject finished successfully (0 no, 1 yes)"
    )
    intercept = Column(
        "intercept", Float,
        comment=EQUATION_COMMENT
    )
    slope = Column(
        "slope", Float,
        comment=EQUATION_COMMENT
    )
    k = Column(
        "k", Float,
        comment=EQUATION_COMMENT + "; k = slope"
    )
    theta = Column(
        "theta", Float,
        comment=EQUATION_COMMENT + "; theta = -intercept/k = -intercept/slope"
    )

    # Relationships
    trials = ancillary_relationship(
        parent_class_name="CardinalExpDetThreshold",
        ancillary_class_name="CardinalExpDetThresholdTrial",
        ancillary_fk_to_parent_attr_name="cardinal_expdetthreshold_id",
        ancillary_order_by_attr_name="trial"
    )

    def is_complete(self) -> bool:
        return bool(self.finished)

    def get_trial_html(self, req: CamcopsRequest) -> str:
        trialarray = self.trials  # type: List[CardinalExpDetThresholdTrial]  # for type hinter!  # noqa
        html = CardinalExpDetThresholdTrial.get_html_table_header()
        for t in trialarray:
            html += t.get_html_table_row()
        html += """</table>"""

        # Don't add figures if we're incomplete
        if not self.is_complete():
            return html

        # Add figures

        figsize = (FULLWIDTH_PLOT_WIDTH/2, FULLWIDTH_PLOT_WIDTH/2)
        jitter_step = 0.02
        dp_to_consider_same_for_jitter = 3
        y_extra_space = 0.1
        x_extra_space = 0.02
        trialfig = req.create_figure(figsize=figsize)
        trialax = trialfig.add_subplot(WHOLE_PANEL)
        notcalc_detected_x = []
        notcalc_detected_y = []
        notcalc_missed_x = []
        notcalc_missed_y = []
        calc_detected_x = []
        calc_detected_y = []
        calc_missed_x = []
        calc_missed_y = []
        catch_detected_x = []
        catch_detected_y = []
        catch_missed_x = []
        catch_missed_y = []
        all_x = []
        all_y = []
        for t in trialarray:
            x = t.trial
            y = t.intensity
            all_x.append(x)
            all_y.append(y)
            if t.trial_num_in_calculation_sequence is not None:
                if t.yes:
                    calc_detected_x.append(x)
                    calc_detected_y.append(y)
                else:
                    calc_missed_x.append(x)
                    calc_missed_y.append(y)
            elif t.target_presented:
                if t.yes:
                    notcalc_detected_x.append(x)
                    notcalc_detected_y.append(y)
                else:
                    notcalc_missed_x.append(x)
                    notcalc_missed_y.append(y)
            else:  # catch trial
                if t.yes:
                    catch_detected_x.append(x)
                    catch_detected_y.append(y)
                else:
                    catch_missed_x.append(x)
                    catch_missed_y.append(y)
        trialax.plot(all_x,              all_y,              marker="",
                     color="0.9", linestyle="-", label=None)
        trialax.plot(notcalc_missed_x,   notcalc_missed_y,   marker="o",
                     color="k",   linestyle="None", label="miss")
        trialax.plot(notcalc_detected_x, notcalc_detected_y, marker="+",
                     color="k",   linestyle="None", label="hit")
        trialax.plot(calc_missed_x,      calc_missed_y,      marker="o",
                     color="r",   linestyle="None", label="miss, scored")
        trialax.plot(calc_detected_x,    calc_detected_y,    marker="+",
                     color="b",   linestyle="None", label="hit, scored")
        trialax.plot(catch_missed_x,     catch_missed_y,     marker="o",
                     color="g",   linestyle="None", label="CR")
        trialax.plot(catch_detected_x,   catch_detected_y,   marker="*",
                     color="g",   linestyle="None", label="FA")
        leg = trialax.legend(
            numpoints=1,
            fancybox=True,  # for set_alpha (below)
            loc="best",  # bbox_to_anchor=(0.75, 1.05)
            labelspacing=0,
            handletextpad=0,
            prop=req.fontprops
        )
        leg.get_frame().set_alpha(0.5)
        trialax.set_xlabel("Trial number", fontdict=req.fontdict)
        trialax.set_ylabel("Intensity", fontdict=req.fontdict)
        trialax.set_ylim(0 - y_extra_space, 1 + y_extra_space)
        trialax.set_xlim(-0.5, len(trialarray) - 0.5)
        req.set_figure_font_sizes(trialax)

        fitfig = None
        if self.k is not None and self.theta is not None:
            fitfig = req.create_figure(figsize=figsize)
            fitax = fitfig.add_subplot(WHOLE_PANEL)
            detected_x = []
            detected_x_approx = []
            detected_y = []
            missed_x = []
            missed_x_approx = []
            missed_y = []
            all_x = []
            for t in trialarray:
                if t.trial_num_in_calculation_sequence is not None:
                    all_x.append(t.intensity)
                    approx_x = "{0:.{precision}f}".format(
                        t.intensity,
                        precision=dp_to_consider_same_for_jitter
                    )
                    if t.yes:
                        detected_y.append(
                            1 -
                            detected_x_approx.count(approx_x) * jitter_step)
                        detected_x.append(t.intensity)
                        detected_x_approx.append(approx_x)
                    else:
                        missed_y.append(
                            0 + missed_x_approx.count(approx_x) * jitter_step)
                        missed_x.append(t.intensity)
                        missed_x_approx.append(approx_x)
            fit_x = np.arange(0.0 - x_extra_space, 1.0 + x_extra_space, 0.001)
            fit_y = logistic(fit_x, self.k, self.theta)
            fitax.plot(fit_x,      fit_y,
                       color="g", linestyle="-")
            fitax.plot(missed_x,   missed_y,   marker="o",
                       color="r", linestyle="None")
            fitax.plot(detected_x, detected_y, marker="+",
                       color="b", linestyle="None")
            fitax.set_ylim(0 - y_extra_space, 1 + y_extra_space)
            fitax.set_xlim(np.amin(all_x) - x_extra_space,
                           np.amax(all_x) + x_extra_space)
            marker_points = []
            for y in (LOWER_MARKER, 0.5, UPPER_MARKER):
                x = inv_logistic(y, self.k, self.theta)
                marker_points.append((x, y))
            for p in marker_points:
                fitax.plot([p[0], p[0]], [-1, p[1]], color="0.5", linestyle=":")
                fitax.plot([-1, p[0]], [p[1], p[1]], color="0.5", linestyle=":")
            fitax.set_xlabel("Intensity", fontdict=req.fontdict)
            fitax.set_ylabel("Detected? (0=no, 1=yes; jittered)",
                             fontdict=req.fontdict)
            req.set_figure_font_sizes(fitax)

        html += """
            <table class="{CssClass.NOBORDER}">
                <tr>
                    <td class="{CssClass.NOBORDERPHOTO}">{trialfig}</td>
                    <td class="{CssClass.NOBORDERPHOTO}">{fitfig}</td>
                </tr>
            </table>
        """.format(
            CssClass=CssClass,
            trialfig=req.get_html_from_pyplot_figure(trialfig),
            fitfig=req.get_html_from_pyplot_figure(fitfig)
        )

        return html

    def logistic_x_from_p(self, p: Optional[float]) -> Optional[float]:
        try:
            return (math.log(p / (1 - p)) - self.intercept) / self.slope
        except (TypeError, ValueError):
            return None

    def get_task_html(self, req: CamcopsRequest) -> str:
        if self.modality == MODALITY_AUDITORY:
            modality = req.wappstring("auditory")
        elif self.modality == MODALITY_VISUAL:
            modality = req.wappstring("visual")
        else:
            modality = None
        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                </table>
            </div>
            <div class="{CssClass.EXPLANATION}">
                The ExpDet-Threshold task measures visual and auditory
                thresholds for stimuli on a noisy background, using a
                single-interval up/down method. It is intended as a prequel to
                the Expectation–Detection task.
            </div>
            <table class="{CssClass.TASKCONFIG}">
                <tr>
                    <th width="50%">Configuration variable</th>
                    <th width="50%">Value</th>
                </tr>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
        )
        h += tr_qa("Modality", modality)
        h += tr_qa("Target number", self.target_number)
        h += tr_qa("Background filename", ws.webify(self.background_filename))
        h += tr_qa("Background intensity", self.background_intensity)
        h += tr_qa("Target filename", ws.webify(self.target_filename))
        h += tr_qa("(For visual targets) Target duration (s)",
                   self.visual_target_duration_s)
        h += tr_qa("Start intensity (minimum)", self.start_intensity_min)
        h += tr_qa("Start intensity (maximum)", self.start_intensity_max)
        h += tr_qa("Initial (large) intensity step",
                   self.initial_large_intensity_step)
        h += tr_qa("Main (small) intensity step",
                   self.main_small_intensity_step)
        h += tr_qa("Number of trials in main sequence",
                   self.num_trials_in_main_sequence)
        h += tr_qa("Probability of a catch trial", self.p_catch_trial)
        h += tr_qa("Prompt", self.prompt)
        h += tr_qa("Intertrial interval (ITI) (s)", self.iti_s)
        h += """
            </table>
            <table class="{CssClass.TASKDETAIL}">
                <tr><th width="50%">Measure</th><th width="50%">Value</th></tr>
        """.format(CssClass=CssClass)
        h += tr_qa("Finished?", get_yes_no_none(req, self.finished))
        h += tr_qa("Logistic intercept",
                   ws.number_to_dp(self.intercept,
                                   DP))
        h += tr_qa("Logistic slope",
                   ws.number_to_dp(self.slope, DP))
        h += tr_qa("Logistic k (= slope)",
                   ws.number_to_dp(self.k, DP))
        h += tr_qa("Logistic theta (= –intercept/slope)",
                   ws.number_to_dp(self.theta, DP))
        h += tr_qa("Intensity for {}% detection".format(100*LOWER_MARKER),
                   ws.number_to_dp(self.logistic_x_from_p(LOWER_MARKER),
                                   DP))
        h += tr_qa("Intensity for 50% detection",
                   ws.number_to_dp(self.theta, DP))
        h += tr_qa("Intensity for {}% detection".format(100*UPPER_MARKER),
                   ws.number_to_dp(self.logistic_x_from_p(UPPER_MARKER),
                                   DP))
        h += """
            </table>
        """
        h += self.get_trial_html(req)
        return h
