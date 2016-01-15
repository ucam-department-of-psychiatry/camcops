#!/usr/bin/env python3
# ace3.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import matplotlib.pyplot as plt
import numpy
import pythonlib.rnc_web as ws
from cc_modules.cc_constants import (
    CTV_DICTLIST_INCOMPLETE,
    CLINICIAN_FIELDSPECS,
    FULLWIDTH_PLOT_WIDTH,
    PV,
    STANDARD_TASK_FIELDSPECS,
)
from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    get_html_from_pyplot_figure,
    italic,
    subheading_spanning_two_columns,
    tr,
    tr_qa,
    tr_span_col,
)
from cc_modules.cc_task import Task


# =============================================================================
# Constants
# =============================================================================

ADDRESS_PARTS = ["forename", "surname", "number", "street_1",
                 "street_2", "town", "county"]
RECALL_WORDS = ["lemon", "key", "ball"]


# =============================================================================
# Ancillary functions
# =============================================================================

def score_zero_for_absent(x):
    """0 if x is None else x"""
    return 0 if x is None else x


# =============================================================================
# ACE-III
# =============================================================================

class Ace3(Task):
    FIELDSPECS = (
        STANDARD_TASK_FIELDSPECS +
        CLINICIAN_FIELDSPECS +
        [
            dict(name="age_at_leaving_full_time_education",
                 cctype="INT",
                 comment="Age at leaving full time education"),
            dict(name="occupation", cctype="TEXT",
                 comment="Occupation"),
            dict(name="handedness", cctype="TEXT",
                 comment="Handedness (L or R)",
                 pv=["L", "R"]),
        ] +
        repeat_fieldspec(
            "attn_time", 1, 5, pv=PV.BIT,
            comment_fmt="Attention, time, {n}/5, {s} (0 or 1)",
            comment_strings=["day", "date", "month", "year", "season"],
        ) +
        repeat_fieldspec(
            "attn_place", 1, 5, pv=PV.BIT,
            comment_fmt="Attention, place, {n}/5, {s} (0 or 1)",
            comment_strings=["house number/floor", "street/hospital",
                             "town", "county", "country"],
        ) +
        repeat_fieldspec(
            "attn_repeat_word", 1, 3, pv=PV.BIT,
            comment_fmt="Attention, repeat word, {n}/3, {s} (0 or 1)",
            comment_strings=RECALL_WORDS,
        ) +
        [
            dict(name="attn_num_registration_trials", cctype="INT",
                 comment="Attention, repetition, number of trials "
                 "(not scored)"),
        ] +
        repeat_fieldspec(
            "attn_serial7_subtraction", 1, 5, pv=PV.BIT,
            comment_fmt="Attention, serial sevens, {n}/5 (0 or 1)",
        ) +
        repeat_fieldspec(
            "mem_recall_word", 1, 3, pv=PV.BIT,
            comment_fmt="Memory, recall word, {n}/3, {s} (0 or 1",
            comment_strings=RECALL_WORDS,
        ) +
        [
            dict(name="fluency_letters_score", cctype="INT",
                 comment="Fluency, words beginning with P, score 0-7",
                 min=0, max=7),
            dict(name="fluency_animals_score", cctype="INT",
                 comment="Fluency, animals, score 0-7",
                 min=0, max=7),
        ] +
        repeat_fieldspec(
            "mem_repeat_address_trial1_", 1, 7, pv=PV.BIT,
            comment_fmt="Memory, address registration trial 1/3 "
            "(not scored), {s} (0 or 1)", comment_strings=ADDRESS_PARTS,
        ) +
        repeat_fieldspec(
            "mem_repeat_address_trial2_", 1, 7, pv=PV.BIT,
            comment_fmt="Memory, address registration trial 2/3 "
            "(not scored), {s} (0 or 1)", comment_strings=ADDRESS_PARTS,
        ) +
        repeat_fieldspec(
            "mem_repeat_address_trial3_", 1, 7, pv=PV.BIT,
            comment_fmt="Memory, address registration trial 3/3 "
            "(scored), {s} (0 or 1)", comment_strings=ADDRESS_PARTS,
        ) +
        repeat_fieldspec(
            "mem_famous", 1, 4, pv=PV.BIT,
            comment_fmt="Memory, famous people, {n}/4, {s} (0 or 1)",
            comment_strings=["current PM", "woman PM", "USA president",
                             "JFK"],
        ) +
        [
            dict(name="lang_follow_command_practice", cctype="INT",
                 comment="Language, command, practice trial (not scored)",
                 pv=PV.BIT),
        ] +
        repeat_fieldspec(
            "lang_follow_command", 1, 3, pv=PV.BIT,
            comment_fmt="Language, command {n}/3 (0 or 1)",
        ) +
        repeat_fieldspec(
            "lang_write_sentences_point", 1, 2, pv=PV.BIT,
            comment_fmt="Language, write sentences, {n}/2, {s} (0 or 1)",
            comment_strings=["two sentences on same topic",
                             "grammar/spelling"],
        ) +
        repeat_fieldspec(
            "lang_repeat_word", 1, 4, pv=PV.BIT,
            comment_fmt="Language, repeat word, {n}/4, {s} (0 or 1)",
            comment_strings=["caterpillar", "eccentricity",
                             "unintelligible", "statistician"],
        ) +
        repeat_fieldspec(
            "lang_repeat_sentence", 1, 2, pv=PV.BIT,
            comment_fmt="Language, repeat sentence, {n}/2, {s} (0 or 1)",
            comment_strings=["glitters_gold", "stitch_time"],
        ) +
        repeat_fieldspec(
            "lang_name_picture", 1, 12, pv=PV.BIT,
            comment_fmt="Language, name picture, {n}/12, {s} (0 or 1)",
            comment_strings=["spoon", "book", "kangaroo/wallaby",
                             "penguin", "anchor", "camel/dromedary",
                             "harp", "rhinoceros", "barrel/keg/tub",
                             "crown", "alligator/crocodile",
                             "accordion/piano accordion/squeeze box"],
        ) +
        repeat_fieldspec(
            "lang_identify_concept", 1, 4, pv=PV.BIT,
            comment_fmt="Language, identify concept, {n}/4, {s} (0 or 1)",
            comment_strings=["monarchy", "marsupial", "Antarctic", "nautical"],
        ) +
        [
            dict(name="lang_read_words_aloud", cctype="INT", pv=PV.BIT,
                 comment="Language, read five irregular words (0 or 1)"),
            dict(name="vsp_copy_infinity", cctype="INT", pv=PV.BIT,
                 comment="Visuospatial, copy infinity (0-1)"),
            dict(name="vsp_copy_cube", cctype="INT",
                 comment="Visuospatial, copy cube (0-2)",
                 min=0, max=2),
            dict(name="vsp_draw_clock", cctype="INT",
                 comment="Visuospatial, draw clock (0-5)",
                 min=0, max=5),
        ] +
        repeat_fieldspec(
            "vsp_count_dots", 1, 4, pv=PV.BIT,
            comment_fmt="Visuospatial, count dots {n}/4, {s} dots (0-1)",
            comment_strings=["8", "10", "7", "9"],
        ) +
        repeat_fieldspec(
            "vsp_identify_letter", 1, 4, pv=PV.BIT,
            comment_fmt="Visuospatial, identify letter {n}/4, {s} (0-1)",
            comment_strings=["K", "M", "A", "T"],
        ) +
        repeat_fieldspec(
            "mem_recall_address", 1, 7, pv=PV.BIT,
            comment_fmt="Memory, recall address {n}/7, {s} (0-1)",
            comment_strings=ADDRESS_PARTS,
        ) +
        repeat_fieldspec(
            "mem_recognize_address", 1, 5, pv=PV.BIT,
            comment_fmt="Memory, recognize address {n}/5 (if "
            "applicable) ({s}) (0-1)",
            comment_strings=["name", "number", "street", "town", "county"],
        ) +
        [
            dict(name="picture1_blobid", cctype="INT",
                 comment="Photo 1/2 PNG BLOB ID"),
            dict(name="picture1_rotation", cctype="INT",
                 comment="Photo 1/2 rotation (degrees clockwise)"),
            dict(name="picture2_blobid", cctype="INT",
                 comment="Photo 2/2 PNG BLOB ID"),
            dict(name="picture2_rotation", cctype="INT",
                 comment="Photo 2/2 rotation (degrees clockwise)"),
            dict(name="comments", cctype="TEXT",
                 comment="Clinician's comments"),
        ]
    )

    @classmethod
    def get_tablename(cls):
        return "ace3"

    @classmethod
    def get_taskshortname(cls):
        return "ACE-III"

    @classmethod
    def get_tasklongname(cls):
        return "Addenbrooke’s Cognitive Examination III"

    @classmethod
    def get_fieldspecs(cls):
        return cls.FIELDSPECS

    @classmethod
    def get_pngblob_name_idfield_rotationfield_list(self):
        return [
            ("picture1", "picture1_blobid", "picture1_rotation"),
            ("picture2", "picture2_blobid", "picture2_rotation"),
        ]

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "ACE-III total score",
                "axis_label": "Total score (out of 100)",
                "axis_min": -0.5,
                "axis_max": 100.5,
                "horizontal_lines": [
                    82.5,
                    88.5,
                ],
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        a = self.attn_score()
        m = self.mem_score()
        f = self.fluency_score()
        l = self.lang_score()
        v = self.vsp_score()
        t = a + m + f + l + v
        text = (
            "ACE-III total: {}/100 (attention {}/18, memory {}/26, "
            "fluency {}/14, language {}/26, visuospatial {}/16)"
        ).format(t, a, m, f, l, v)
        return [{"content": text}]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT",
                 value=self.total_score(), comment="Total score (/100)"),
            dict(name="attn", cctype="INT",
                 value=self.attn_score(), comment="Attention (/18)"),
            dict(name="mem", cctype="INT",
                 value=self.mem_score(), comment="Memory (/26)"),
            dict(name="fluency", cctype="INT",
                 value=self.fluency_score(), comment="Fluency (/14)"),
            dict(name="lang", cctype="INT",
                 value=self.lang_score(), comment="Language (/26)"),
            dict(name="vsp", cctype="INT",
                 value=self.vsp_score(), comment="Visuospatial (/16)"),
        ]

    def attn_score(self):
        fields = (repeat_fieldname("attn_time", 1, 5) +
                  repeat_fieldname("attn_place", 1, 5) +
                  repeat_fieldname("attn_repeat_word", 1, 3) +
                  repeat_fieldname("attn_serial7_subtraction", 1, 5))
        return self.sum_fields(fields)

    def get_recog_score(self, recalled, recognized):
        if recalled == 1:
            return 1
        return score_zero_for_absent(recognized)

    def get_recog_text(self, recalled, recognized):
        if recalled:
            return "<i>1 (already recalled)</i>"
        return answer(recognized)

    def get_mem_recognition_score(self):
        score = 0
        score += self.get_recog_score(
            (self.mem_recall_address1 == 1 and self.mem_recall_address2 == 1),
            self.mem_recognize_address1)
        score += self.get_recog_score(
            (self.mem_recall_address3 == 1),
            self.mem_recognize_address2)
        score += self.get_recog_score(
            (self.mem_recall_address4 == 1 and self.mem_recall_address5 == 1),
            self.mem_recognize_address3)
        score += self.get_recog_score(
            (self.mem_recall_address6 == 1),
            self.mem_recognize_address4)
        score += self.get_recog_score(
            (self.mem_recall_address7 == 1),
            self.mem_recognize_address5)
        return score

    def mem_score(self):
        fields = (repeat_fieldname("mem_recall_word", 1, 3) +
                  repeat_fieldname("mem_repeat_address_trial3_", 1, 7) +
                  repeat_fieldname("mem_famous", 1, 4) +
                  repeat_fieldname("mem_recall_address", 1, 7))
        return self.sum_fields(fields) + self.get_mem_recognition_score()

    def fluency_score(self):
        return (
            score_zero_for_absent(self.fluency_letters_score) +
            score_zero_for_absent(self.fluency_animals_score)
        )

    def get_follow_command_score(self):
        if self.lang_follow_command_practice != 1:
            return 0
        return self.sum_fields(repeat_fieldname("lang_follow_command", 1, 3))

    def get_repeat_word_score(self):
        n = self.sum_fields(repeat_fieldname("lang_repeat_word", 1, 4))
        return 2 if n >= 4 else (1 if n == 3 else 0)

    def lang_score(self):
        fields = (repeat_fieldname("lang_write_sentences_point", 1, 2) +
                  repeat_fieldname("lang_repeat_sentence", 1, 2) +
                  repeat_fieldname("lang_name_picture", 1, 12) +
                  repeat_fieldname("lang_identify_concept", 1, 4))
        return (self.sum_fields(fields) +
                self.get_follow_command_score() +
                self.get_repeat_word_score() +
                score_zero_for_absent(self.lang_read_words_aloud))

    def vsp_score(self):
        fields = (repeat_fieldname("vsp_count_dots", 1, 4) +
                  repeat_fieldname("vsp_identify_letter", 1, 4))
        return (self.sum_fields(fields) +
                score_zero_for_absent(self.vsp_copy_infinity) +
                score_zero_for_absent(self.vsp_copy_cube) +
                score_zero_for_absent(self.vsp_draw_clock))

    def total_score(self):
        return (self.attn_score() +
                self.mem_score() +
                self.fluency_score() +
                self.lang_score() +
                self.vsp_score())

    def is_recognition_complete(self):
        return (
            ((self.mem_recall_address1 == 1 and self.mem_recall_address2 == 1)
                or self.mem_recognize_address1 is not None)
            and (self.mem_recall_address3 == 1
                 or self.mem_recognize_address2 is not None)
            and ((self.mem_recall_address4 == 1
                  and self.mem_recall_address5 == 1)
                 or self.mem_recognize_address3 is not None)
            and (self.mem_recall_address6 == 1
                 or self.mem_recognize_address4 is not None)
            and (self.mem_recall_address7 == 1
                 or self.mem_recognize_address5 is not None)
        )

    def is_complete(self):
        if not self.field_contents_valid():
            return False
        if not self.are_all_fields_complete(
                repeat_fieldname("attn_place", 1, 5) +
                repeat_fieldname("attn_repeat_word", 1, 3) +
                # not scored: # ["attn_num_registration_trials"] +
                repeat_fieldname("attn_serial7_subtraction", 1, 5) +
                repeat_fieldname("mem_recall_word", 1, 3) +
                [
                    "fluency_letters_score",
                    "fluency_animals_score"
                ] +
                repeat_fieldname("mem_repeat_address_trial3_", 1, 7) +
                repeat_fieldname("mem_famous", 1, 4) +
                [
                    "lang_follow_command_practice"
                ] +
                repeat_fieldname("lang_follow_command", 1, 3) +
                repeat_fieldname("lang_repeat_word", 1, 4) +
                repeat_fieldname("lang_repeat_sentence", 1, 2) +
                repeat_fieldname("lang_name_picture", 1, 12) +
                repeat_fieldname("lang_identify_concept", 1, 4) +
                [
                    "lang_read_words_aloud",
                    "vsp_copy_infinity",
                    "vsp_copy_cube",
                    "vsp_draw_clock"
                ] +
                repeat_fieldname("vsp_count_dots", 1, 4) +
                repeat_fieldname("vsp_identify_letter", 1, 4) +
                repeat_fieldname("mem_recall_address", 1, 7)):
            return False
        if self.lang_follow_command_practice == 1 \
                and not self.are_all_fields_complete(
                    repeat_fieldname("lang_write_sentences_point", 1, 2)):
            return False
        return self.is_recognition_complete()

    def get_task_html(self):
        a = self.attn_score()
        m = self.mem_score()
        f = self.fluency_score()
        l = self.lang_score()
        v = self.vsp_score()
        t = a + m + f + l + v
        figurehtml = ""
        if self.is_complete():
            FIGSIZE = (FULLWIDTH_PLOT_WIDTH/3, FULLWIDTH_PLOT_WIDTH/4)
            WIDTH = 0.9
            fig = plt.figure(figsize=FIGSIZE)
            ax = fig.add_subplot(1, 1, 1)
            scores = numpy.array([a, m, f, l, v])
            maxima = numpy.array([18, 26, 14, 26, 16])
            y = 100 * scores/maxima
            x_labels = ["Attn", "Mem", "Flu", "Lang", "VSp"]
            N = len(y)
            xvar = numpy.arange(N)
            ax.bar(xvar, y, WIDTH, color="b")
            ax.set_ylabel("%")
            ax.set_xticks(xvar + WIDTH/2)
            ax.set_xticklabels(x_labels)
            ax.set_xlim(0 - (1 - WIDTH), len(scores))
            plt.tight_layout()  # or the ylabel drops off the figure
            # fig.autofmt_xdate()
            figurehtml = get_html_from_pyplot_figure(fig)
        return (
            self.get_standard_clinician_block(True, self.comments)
            + """
                <div class="summary">
                    <table class="summary">
                        <tr>
                            {is_complete}
                            <td class="figure" rowspan="7">{figure}</td>
                        </td>
            """.format(is_complete=self.get_is_complete_td_pair(),
                       figure=figurehtml)
            + tr("Total ACE-III score <sup>[1]</sup>", answer(t) + " / 100")
            + tr("Attention", answer(a) + " / 18 ({}%)".format(100*a/18))
            + tr("Memory", answer(m) + " / 26 ({}%)".format(100*m/26))
            + tr("Fluency", answer(f) + " / 14 ({}%)".format(100*f/14))
            + tr("Language", answer(l) + " / 26 ({}%)".format(100*l/26))
            + tr("Visuospatial", answer(v) + " / 16 ({}%)".format(100*v/16))
            + """
                    </table>
                </div>
                <table class="taskdetail">
                    <tr>
                        <th width="75%">Question</th>
                        <th width="25%">Answer/score</td>
                    </tr>
            """
            + tr_qa("Age on leaving full-time education",
                    self.age_at_leaving_full_time_education)
            + tr_qa("Occupation", ws.webify(self.occupation))
            + tr_qa("Handedness", ws.webify(self.handedness))

            + subheading_spanning_two_columns("Attention")
            + tr("Day? Date? Month? Year? Season?",
                 ", ".join([answer(x) for x in [self.attn_time1,
                                                self.attn_time2,
                                                self.attn_time3,
                                                self.attn_time4,
                                                self.attn_time5]]))
            + tr("House number/floor? Street/hospital? Town? County? Country?",
                 ", ".join([answer(x) for x in [self.attn_place1,
                                                self.attn_place2,
                                                self.attn_place3,
                                                self.attn_place4,
                                                self.attn_place5]]))
            + tr("Repeat: Lemon? Key? Ball?",
                 ", ".join([answer(x) for x in [self.attn_repeat_word1,
                                                self.attn_repeat_word2,
                                                self.attn_repeat_word3]]))
            + tr("Repetition: number of trials <i>(not scored)</i>",
                 answer(self.attn_num_registration_trials,
                        formatter_answer=italic))
            + tr(
                "Serial subtractions: First correct? Second? Third? Fourth? "
                "Fifth?",
                ", ".join([answer(x) for x in [
                    self.attn_serial7_subtraction1,
                    self.attn_serial7_subtraction2,
                    self.attn_serial7_subtraction3,
                    self.attn_serial7_subtraction4,
                    self.attn_serial7_subtraction5]]))

            + subheading_spanning_two_columns("Memory (1)")
            + tr("Recall: Lemon? Key? Ball?",
                 ", ".join([answer(x) for x in [self.mem_recall_word1,
                                                self.mem_recall_word2,
                                                self.mem_recall_word3]]))

            + subheading_spanning_two_columns("Fluency")
            + tr("Score for words beginning with ‘P’ <i>(≥18 scores 7, 14–17 "
                 "scores 6, 11–13 scores 5, 8–10 scores 4, 6–7 scores 3, "
                 "4–5 scores 2, 2–3 scores 1, 0–1 scores 0)</i>",
                 answer(self.fluency_letters_score) + " / 7")
            + tr("Score for animals <i>(≥22 scores 7, 17–21 scores 6, "
                 "14–16 scores 5, 11–13 scores 4, 9–10 scores 3, "
                 "7–8 scores 2, 5–6 scores 1, &lt;5 scores 0)</i>",
                 answer(self.fluency_animals_score) + " / 7")

            + subheading_spanning_two_columns("Memory (2)")
            + tr(
                "Third trial of address registration: Harry? Barnes? 73? "
                "Orchard? Close? Kingsbridge? Devon?",
                ", ".join([answer(x) for x in [
                    self.mem_repeat_address_trial3_1,
                    self.mem_repeat_address_trial3_2,
                    self.mem_repeat_address_trial3_3,
                    self.mem_repeat_address_trial3_4,
                    self.mem_repeat_address_trial3_5,
                    self.mem_repeat_address_trial3_6,
                    self.mem_repeat_address_trial3_7]]))
            + tr("Current PM? Woman who was PM? USA president? USA president "
                 "assassinated in 1960s?",
                 ", ".join([answer(x) for x in [self.mem_famous1,
                                                self.mem_famous2,
                                                self.mem_famous3,
                                                self.mem_famous4]]))

            + subheading_spanning_two_columns("Language")
            + tr("<i>Practice trial (“Pick up the pencil and then the "
                 "paper”)</i>",
                 answer(self.lang_follow_command_practice,
                        formatter_answer=italic))
            + tr_qa("“Place the paper on top of the pencil”",
                    self.lang_follow_command1)
            + tr_qa("“Pick up the pencil but not the paper”",
                    self.lang_follow_command2)
            + tr_qa("“Pass me the pencil after touching the paper”",
                    self.lang_follow_command3)
            + tr(
                "Sentence-writing: point for ≥2 complete sentences about "
                "the one topic? Point for correct grammar and spelling?",
                ", ".join([answer(x) for x in [
                    self.lang_write_sentences_point1,
                    self.lang_write_sentences_point2]]))
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
                ))
            + tr_qa("Repeat: “All that glitters is not gold”?",
                    self.lang_repeat_sentence1)
            + tr_qa("Repeat: “A stitch in time saves nine”?",
                    self.lang_repeat_sentence2)
            + tr("Name pictures: spoon, book, kangaroo/wallaby",
                 ", ".join([answer(x) for x in [self.lang_name_picture1,
                                                self.lang_name_picture2,
                                                self.lang_name_picture3]]))
            + tr("Name pictures: penguin, anchor, camel/dromedary",
                 ", ".join([answer(x) for x in [self.lang_name_picture4,
                                                self.lang_name_picture5,
                                                self.lang_name_picture6]]))
            + tr("Name pictures: harp, rhinoceros/rhino, barrel/keg/tub",
                 ", ".join([answer(x) for x in [self.lang_name_picture7,
                                                self.lang_name_picture8,
                                                self.lang_name_picture9]]))
            + tr("Name pictures: crown, alligator/crocodile, "
                 "accordion/piano accordion/squeeze box",
                 ", ".join([answer(x) for x in [self.lang_name_picture10,
                                                self.lang_name_picture11,
                                                self.lang_name_picture12]]))
            + tr(
                "Identify pictures: monarchy? marsupial? Antarctic? nautical?",
                ", ".join([answer(x) for x in [self.lang_identify_concept1,
                                               self.lang_identify_concept2,
                                               self.lang_identify_concept3,
                                               self.lang_identify_concept4]]))
            + tr_qa("Read all successfully: sew, pint, soot, dough, height",
                    self.lang_read_words_aloud)

            + subheading_spanning_two_columns("Visuospatial")
            + tr("Copy infinity", answer(self.vsp_copy_infinity) + " / 1")
            + tr("Copy cube", answer(self.vsp_copy_cube) + " / 2")
            + tr("Draw clock with numbers and hands at 5:10",
                 answer(self.vsp_draw_clock) + " / 5")
            + tr("Count dots: 8, 10, 7, 9",
                 ", ".join([answer(x) for x in [self.vsp_count_dots1,
                                                self.vsp_count_dots2,
                                                self.vsp_count_dots3,
                                                self.vsp_count_dots4]]))
            + tr("Identify letters: K, M, A, T",
                 ", ".join([answer(x) for x in [self.vsp_identify_letter1,
                                                self.vsp_identify_letter2,
                                                self.vsp_identify_letter3,
                                                self.vsp_identify_letter4]]))

            + subheading_spanning_two_columns("Memory (3)")
            + tr("Recall address: Harry? Barnes? 73? Orchard? Close? "
                 "Kingsbridge? Devon?",
                 ", ".join([answer(x) for x in [self.mem_recall_address1,
                                                self.mem_recall_address2,
                                                self.mem_recall_address3,
                                                self.mem_recall_address4,
                                                self.mem_recall_address5,
                                                self.mem_recall_address6,
                                                self.mem_recall_address7]]))
            + tr("Recognize address: Jerry Barnes/Harry Barnes/Harry "
                 "Bradford?",
                 self.get_recog_text((self.mem_recall_address1 == 1
                                      and self.mem_recall_address2 == 1),
                                     self.mem_recognize_address1))
            + tr("Recognize address: 37/73/76?",
                 self.get_recog_text((self.mem_recall_address3 == 1),
                                     self.mem_recognize_address2))
            + tr(
                "Recognize address: Orchard Place/Oak Close/Orchard "
                "Close?",
                self.get_recog_text(
                    (self.mem_recall_address4 == 1
                     and self.mem_recall_address5 == 1),
                    self.mem_recognize_address3))
            + tr("Recognize address: Oakhampton/Kingsbridge/Dartington?",
                 self.get_recog_text((self.mem_recall_address6 == 1),
                                     self.mem_recognize_address4))
            + tr("Recognize address: Devon/Dorset/Somerset?",
                 self.get_recog_text((self.mem_recall_address7 == 1),
                                     self.mem_recognize_address5))

            + subheading_spanning_two_columns("Photos of test sheet")
            + tr_span_col(self.get_blob_png_html(self.picture1_blobid,
                                                 self.picture1_rotation),
                          td_class="photo")
            + tr_span_col(self.get_blob_png_html(self.picture2_blobid,
                                                 self.picture2_rotation),
                          td_class="photo")
            + """
                </table>
                <div class="footnotes">
                    [1] In the ACE-R (the predecessor of the ACE-III),
                    scores ≤82 had sensitivity 0.84 and specificity 1.0 for
                    dementia, and scores ≤88 had sensitivity 0.94 and
                    specificity 0.89 for dementia, in a context of patients
                    with AlzD, FTD, LBD, MCI, and controls
                    (Mioshi et al., 2006, PMID 16977673).
                </div>
                <div class="copyright">
                    ACE-III: Copyright © 2012, John Hodges.
                    “The ACE-III is available for free. The copyright is held
                    by Professor John Hodges who is happy for the test to be
                    used in clinical practice and research projects. There is
                    no need to contact us if you wish to use the ACE-III in
                    clinical practice.”
                    (ACE-III FAQ, 7 July 2013, www.neura.edu.au).
                </div>
            """
        )
