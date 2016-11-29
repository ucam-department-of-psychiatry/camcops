#!/usr/bin/env python3
# CardinalExpDetThreshold.py

"""
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
"""

import math
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy
import cardinal_pythonlib.rnc_plot as rnc_plot
import cardinal_pythonlib.rnc_web as ws

from ..cc_modules.cc_constants import (
    FULLWIDTH_PLOT_WIDTH,
)
from ..cc_modules.cc_html import (
    get_html_from_pyplot_figure,
    get_yes_no_none,
    tr_qa,
)
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import Ancillary, Task


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

class CardinalExpDetThresholdTrial(Ancillary):
    tablename = "cardinal_expdetthreshold_trials"
    fkname = "cardinal_expdetthreshold_id"
    fieldspecs = [
        dict(name="cardinal_expdetthreshold_id", notnull=True,
             cctype="INT",
             comment="FK to CardinalExpDetThreshold"),
        dict(name="trial", notnull=True, cctype="INT",
             comment="Trial number"),
        # Results
        dict(name="trial_ignoring_catch_trials", cctype="INT",
             comment="Trial number, ignoring catch trials"),
        dict(name="target_presented", cctype="INT",
             comment="Target presented? (0 no, 1 yes)"),
        dict(name="target_time", cctype="ISO8601",
             comment="Target presentation time (ISO-8601)"),
        dict(name="intensity", cctype="FLOAT",
             comment="Target intensity (0.0-1.0)"),
        dict(name="choice_time", cctype="ISO8601",
             comment="Time choice offered (ISO-8601)"),
        dict(name="responded", cctype="INT",
             comment="Responded? (0 no, 1 yes)"),
        dict(name="response_time", cctype="ISO8601",
             comment="Time of response (ISO-8601)"),
        dict(name="response_latency_ms", cctype="INT",
             comment="Response latency (ms)"),
        dict(name="yes", cctype="INT",
             comment="Subject chose YES? (0 didn't, 1 did)"),
        dict(name="no", cctype="INT",
             comment="Subject chose NO? (0 didn't, 1 did)"),
        dict(name="caught_out_reset", cctype="INT",
             comment="Caught out on catch trial, thus reset? (0 no, "
             "1 yes)"),
        dict(name="trial_num_in_calculation_sequence", cctype="INT",
             comment="Trial number as used for threshold calculation"),
    ]
    sortfield = "trial"

    @classmethod
    def get_html_table_header(cls) -> str:
        return """
            <table class="extradetail">
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
        """

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


class CardinalExpDetThreshold(Task):
    tablename = "cardinal_expdetthreshold"
    shortname = "Cardinal_ExpDetThreshold"
    longname = ("Cardinal RN – Threshold determination for "
                "Expectation–Detection task")
    fieldspecs = [
        # Config
        dict(name="modality", cctype="INT",
             comment="Modality (0 auditory, 1 visual)"),
        dict(name="target_number", cctype="INT",
             comment="Target number (within available targets of that "
             "modality)"),
        dict(name="background_filename", cctype="TEXT",
             comment="Filename of media used for background"),
        dict(name="target_filename", cctype="TEXT",
             comment="Filename of media used for target"),
        dict(name="visual_target_duration_s", cctype="FLOAT",
             comment="Visual target duration (s)"),
        dict(name="background_intensity", cctype="FLOAT",
             comment="Intensity of background (0.0-1.0)"),
        dict(name="start_intensity_min", cctype="FLOAT",
             comment="Minimum starting intensity (0.0-1.0)"),
        dict(name="start_intensity_max", cctype="FLOAT",
             comment="Maximum starting intensity (0.0-1.0)"),
        dict(name="initial_large_intensity_step", cctype="FLOAT",
             comment="Initial, large, intensity step (0.0-1.0)"),
        dict(name="main_small_intensity_step", cctype="FLOAT",
             comment="Main, small, intensity step (0.0-1.0)"),
        dict(name="num_trials_in_main_sequence", cctype="INT",
             comment="Number of trials required in main sequence"),
        dict(name="p_catch_trial", cctype="FLOAT",
             comment="Probability of catch trial"),
        dict(name="prompt", cctype="TEXT",
             comment="Prompt given to subject"),
        dict(name="iti_s", cctype="FLOAT",
             comment="Intertrial interval (s)"),
        # Results
        dict(name="finished", cctype="INT",
             comment="Subject finished successfully (0 no, 1 yes)"),
        dict(name="intercept", cctype="FLOAT",
             comment=EQUATION_COMMENT),
        dict(name="slope", cctype="FLOAT",
             comment=EQUATION_COMMENT),
        dict(name="k", cctype="FLOAT",
             comment=EQUATION_COMMENT + "; k = slope"),
        dict(name="theta", cctype="FLOAT",
             comment=EQUATION_COMMENT +
             "; theta = -intercept/k = -intercept/slope "),
    ]
    use_landscape_for_pdf = True
    dependent_classes = [CardinalExpDetThresholdTrial]

    def is_complete(self) -> bool:
        return bool(self.finished)

    def get_trial_array(self) -> List[CardinalExpDetThresholdTrial]:
        return self.get_ancillary_items(CardinalExpDetThresholdTrial)

    def get_trial_html(self) -> str:
        # Fetch trial details
        trialarray = self.get_trial_array()

        # Provide HTML
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
        trialfig = plt.figure(figsize=figsize)
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
        plt.plot(all_x,              all_y,              marker="",
                 color="0.9", linestyle="-", label=None)
        plt.plot(notcalc_missed_x,   notcalc_missed_y,   marker="o",
                 color="k",   linestyle="None", label="miss")
        plt.plot(notcalc_detected_x, notcalc_detected_y, marker="+",
                 color="k",   linestyle="None", label="hit")
        plt.plot(calc_missed_x,      calc_missed_y,      marker="o",
                 color="r",   linestyle="None", label="miss, scored")
        plt.plot(calc_detected_x,    calc_detected_y,    marker="+",
                 color="b",   linestyle="None", label="hit, scored")
        plt.plot(catch_missed_x,     catch_missed_y,     marker="o",
                 color="w",   linestyle="None", label="CR")
        plt.plot(catch_detected_x,   catch_detected_y,   marker="*",
                 color="w",   linestyle="None", label="FA")
        leg = plt.legend(
            numpoints=1,
            fancybox=True,  # for set_alpha (below)
            loc="best",  # bbox_to_anchor=(0.75, 1.05)
            labelspacing=0,
            handletextpad=0
        )
        leg.get_frame().set_alpha(0.5)
        plt.xlabel("Trial number")
        plt.ylabel("Intensity")
        plt.ylim(0 - y_extra_space, 1 + y_extra_space)
        plt.xlim(-0.5, len(trialarray) - 0.5)

        fitfig = None
        if self.k is not None and self.theta is not None:
            fitfig = plt.figure(figsize=figsize)
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
            fit_x = numpy.arange(0.0 - x_extra_space, 1.0 + x_extra_space,
                                 0.001)
            fit_y = rnc_plot.logistic(fit_x, self.k, self.theta)
            plt.plot(fit_x,      fit_y,
                     color="g", linestyle="-")
            plt.plot(missed_x,   missed_y,   marker="o",
                     color="r", linestyle="None")
            plt.plot(detected_x, detected_y, marker="+",
                     color="b", linestyle="None")
            plt.ylim(0 - y_extra_space, 1 + y_extra_space)
            plt.xlim(numpy.amin(all_x) - x_extra_space,
                     numpy.amax(all_x) + x_extra_space)
            marker_points = []
            for y in (LOWER_MARKER, 0.5, UPPER_MARKER):
                x = rnc_plot.inv_logistic(y, self.k, self.theta)
                marker_points.append((x, y))
            for p in marker_points:
                plt.plot([p[0], p[0]], [-1, p[1]], color="0.5", linestyle=":")
                plt.plot([-1, p[0]], [p[1], p[1]], color="0.5", linestyle=":")
            plt.xlabel("Intensity")
            plt.ylabel("Detected? (0=no, 1=yes; jittered)")

        html += """
            <table class="noborder">
                <tr>
                    <td class="noborderphoto">{}</td>
                    <td class="noborderphoto">{}</td>
                </tr>
            </table>
        """.format(
            get_html_from_pyplot_figure(trialfig),
            get_html_from_pyplot_figure(fitfig)
        )

        return html

    def logistic_x_from_p(self, p: Optional[float]) -> Optional[float]:
        try:
            return (math.log(p / (1 - p)) - self.intercept) / self.slope
        except (TypeError, ValueError):
            return None

    def get_task_html(self) -> str:
        if self.modality == MODALITY_AUDITORY:
            modality = WSTRING("auditory")
        elif self.modality == MODALITY_VISUAL:
            modality = WSTRING("visual")
        else:
            modality = None
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                </table>
            </div>
            <div class="explanation">
                The ExpDet-Threshold task measures visual and auditory
                thresholds for stimuli on a noisy background, using a
                single-interval up/down method. It is intended as a prequel to
                the Expectation–Detection task.
            </div>
            <table class="taskconfig">
                <tr>
                    <th width="50%">Configuration variable</th>
                    <th width="50%">Value</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
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
            <table class="taskdetail">
                <tr><th width="50%">Measure</th><th width="50%">Value</th></tr>
        """
        h += tr_qa("Finished?", get_yes_no_none(self.finished))
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
        h += self.get_trial_html()
        return h
