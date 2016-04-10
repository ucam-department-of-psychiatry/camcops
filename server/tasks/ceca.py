#!/usr/bin/env python3
# ceca.py

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

import cardinal_pythonlib.rnc_web as ws
from cc_modules.cc_constants import (
    PV,
)
from cc_modules.cc_html import (
    answer,
    get_yes_no,
    get_yes_no_none,
    subheading_spanning_two_columns,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import get_from_dict, Task


# =============================================================================
# CECA-Q3
# =============================================================================

FREQUENCY_COMMENT = "Frequency (0 never - 3 often)"


class CecaQ3(Task):
    tablename = "cecaq3"
    shortname = "CECA-Q3"
    longname = "Childhood Experience of Care and Abuse Questionnaire"
    fieldspecs = [
        dict(name="s1a_motherfigure_birthmother", cctype="BOOL",
             pv=PV.BIT, comment="Raised by, maternal, birth mother?"),
        dict(name="s1a_motherfigure_stepmother", cctype="BOOL",
             pv=PV.BIT, comment="Raised by, maternal, stepmother?"),
        dict(name="s1a_motherfigure_femalerelative", cctype="BOOL",
             pv=PV.BIT, comment="Raised by, maternal, female relative?"),
        dict(name="s1a_motherfigure_femalerelative_detail",
             cctype="TEXT",
             comment="Raised by, maternal, female relative, detail"),
        dict(name="s1a_motherfigure_familyfriend", cctype="BOOL",
             pv=PV.BIT, comment="Raised by, maternal, family friend?"),
        dict(name="s1a_motherfigure_fostermother", cctype="BOOL",
             pv=PV.BIT, comment="Raised by, maternal, foster mother?"),
        dict(name="s1a_motherfigure_adoptivemother", cctype="BOOL",
             pv=PV.BIT, comment="Raised by, maternal, adoptive mother?"),
        dict(name="s1a_motherfigure_other", cctype="BOOL",
             pv=PV.BIT, comment="Raised by, maternal, other?"),
        dict(name="s1a_motherfigure_other_detail", cctype="TEXT",
             comment="Raised by, maternal, other, detail"),
        dict(name="s1a_fatherfigure_birthfather", cctype="BOOL",
             pv=PV.BIT, comment="Raised by, paternal, birth father?"),
        dict(name="s1a_fatherfigure_stepfather", cctype="BOOL",
             pv=PV.BIT, comment="Raised by, paternal, stepfather?"),
        dict(name="s1a_fatherfigure_malerelative", cctype="BOOL",
             pv=PV.BIT, comment="Raised by, paternal, male relative?"),
        dict(name="s1a_fatherfigure_malerelative_detail",
             cctype="TEXT",
             comment="Raised by, paternal, male relative, detail"),
        dict(name="s1a_fatherfigure_familyfriend", cctype="BOOL",
             pv=PV.BIT, comment="Raised by, paternal, family friend?"),
        dict(name="s1a_fatherfigure_fosterfather", cctype="BOOL",
             pv=PV.BIT, comment="Raised by, paternal, foster father?"),
        dict(name="s1a_fatherfigure_adoptivefather", cctype="BOOL",
             pv=PV.BIT, comment="Raised by, paternal, adoptive father?"),
        dict(name="s1a_fatherfigure_other", cctype="BOOL",
             pv=PV.BIT, comment="Raised by, paternal, other?"),
        dict(name="s1a_fatherfigure_other_detail", cctype="TEXT",
             comment="Raised by, paternal, other, detail"),

        dict(name="s1b_institution", cctype="BOOL",
             pv=PV.BIT, comment="In institution before 17?"),
        dict(name="s1b_institution_time_years", cctype="FLOAT",
             min=0, comment="In institution, time (years)"),

        dict(name="s1c_mother_died", cctype="BOOL",
             pv=PV.BIT, comment="Mother died before 17?"),
        dict(name="s1c_father_died", cctype="BOOL",
             pv=PV.BIT, comment="Father died before 17?"),
        dict(name="s1c_mother_died_subject_aged", cctype="FLOAT",
             min=0, comment="Age when mother died (years)"),
        dict(name="s1c_father_died_subject_aged", cctype="FLOAT",
             min=0, comment="Age when father died (years)"),
        dict(name="s1c_separated_from_mother", cctype="BOOL",
             pv=PV.BIT, comment="Separated from mother for >=1y before 17?"),
        dict(name="s1c_separated_from_father", cctype="BOOL",
             pv=PV.BIT, comment="Separated from father for >=1y before 17?"),
        dict(name="s1c_first_separated_from_mother_aged",
             cctype="FLOAT", min=0,
             comment="Maternal separation, age (years)"),
        dict(name="s1c_first_separated_from_father_aged",
             cctype="FLOAT", min=0,
             comment="Paternal separation, age (years)"),
        dict(name="s1c_mother_how_long_first_separation_years",
             cctype="FLOAT", min=0,
             comment="Maternal separation, how long first separation (y)"),
        dict(name="s1c_father_how_long_first_separation_years",
             cctype="FLOAT", min=0,
             comment="Paternal separation, how long first separation (y)"),
        dict(name="s1c_mother_separation_reason", cctype="INT",
             min=1, max=6, comment="Maternal separation, reason "
             "(1 illness, 2 work, 3 divorce/separation, 4 never knew, "
             "5 abandoned, 6 other)"),
        dict(name="s1c_father_separation_reason", cctype="INT",
             min=1, max=6, comment="Paternal separation, reason "
             "(1 illness, 2 work, 3 divorce/separation, 4 never knew, "
             "5 abandoned, 6 other)"),
        dict(name="s1c_describe_experience", cctype="TEXT",
             comment="Loss of/separation from parent, description"),

        dict(name="s2a_which_mother_figure", cctype="INT",
             min=0, max=5,
             comment="Mother figure, which one (0 none/skip, 1 birth mother, "
             "2 stepmother, 3 other relative, 4 other non-relative, 5 other)"),
        dict(name="s2a_which_mother_figure_other_detail",
             cctype="TEXT",
             comment="Mother figure, other, detail"),
        dict(name="s2a_q1", cctype="INT", min=1, max=5,
             comment="Mother figure, difficult to please (1 no - 5 yes)"),
        dict(name="s2a_q2", cctype="INT", min=1, max=5,
             comment="Mother figure, concerned re my worries (1 no - 5 yes)"),
        dict(name="s2a_q3", cctype="INT", min=1, max=5,
             comment="Mother figure, interested re school (1 no - 5 yes)"),
        dict(name="s2a_q4", cctype="INT", min=1, max=5,
             comment="Mother figure, made me feel unwanted (1 no - 5 yes)"),
        dict(name="s2a_q5", cctype="INT", min=1, max=5,
             comment="Mother figure, better when upset (1 no - 5 yes)"),
        dict(name="s2a_q6", cctype="INT", min=1, max=5,
             comment="Mother figure, critical (1 no - 5 yes)"),
        dict(name="s2a_q7", cctype="INT", min=1, max=5,
             comment="Mother figure, unsupervised <10y (1 no - 5 yes)"),
        dict(name="s2a_q8", cctype="INT", min=1, max=5,
             comment="Mother figure, time to talk (1 no - 5 yes)"),
        dict(name="s2a_q9", cctype="INT", min=1, max=5,
             comment="Mother figure, nuisance (1 no - 5 yes)"),
        dict(name="s2a_q10", cctype="INT", min=1, max=5,
             comment="Mother figure, picked on unfairly (1 no - 5 yes)"),
        dict(name="s2a_q11", cctype="INT", min=1, max=5,
             comment="Mother figure, there if needed (1 no - 5 yes)"),
        dict(name="s2a_q12", cctype="INT", min=1, max=5,
             comment="Mother figure, interested in friends (1 no - 5 yes)"),
        dict(name="s2a_q13", cctype="INT", min=1, max=5,
             comment="Mother figure, concerned re whereabouts (1 no - 5 yes)"),
        dict(name="s2a_q14", cctype="INT", min=1, max=5,
             comment="Mother figure, cared when ill (1 no - 5 yes)"),
        dict(name="s2a_q15", cctype="INT", min=1, max=5,
             comment="Mother figure, neglected basic needs (1 no - 5 yes)"),
        dict(name="s2a_q16", cctype="INT", min=1, max=5,
             comment="Mother figure, preferred siblings (1 no - 5 yes)"),
        dict(name="s2a_extra", cctype="TEXT",
             comment="Mother figure, extra detail"),

        dict(name="s2b_q1", cctype="INT", min=0, max=2,
             comment="Mother figure, tease me (0 no - 2 yes)"),
        dict(name="s2b_q2", cctype="INT", min=0, max=2,
             comment="Mother figure, made me keep secrets (0 no - 2 yes)"),
        dict(name="s2b_q3", cctype="INT", min=0, max=2,
             comment="Mother figure, undermined confidence (0 no - 2 yes)"),
        dict(name="s2b_q4", cctype="INT", min=0, max=2,
             comment="Mother figure, contradictory (0 no - 2 yes)"),
        dict(name="s2b_q5", cctype="INT", min=0, max=2,
             comment="Mother figure, played on fears (0 no - 2 yes)"),
        dict(name="s2b_q6", cctype="INT", min=0, max=2,
             comment="Mother figure, liked to see me suffer (0 no - 2 yes)"),
        dict(name="s2b_q7", cctype="INT", min=0, max=2,
             comment="Mother figure, humiliated me (0 no - 2 yes)"),
        dict(name="s2b_q8", cctype="INT", min=0, max=2,
             comment="Mother figure, shamed me before others (0 no - 2 yes)"),
        dict(name="s2b_q9", cctype="INT", min=0, max=2,
             comment="Mother figure, rejecting (0 no - 2 yes)"),
        dict(name="s2b_q10", cctype="INT", min=0, max=2,
             comment="Mother figure, took things I cherished (0 no - 2 yes)"),
        dict(name="s2b_q11", cctype="INT", min=0, max=2,
             comment="Mother figure, eat disliked until sick (0 no - 2 yes)"),
        dict(name="s2b_q12", cctype="INT", min=0, max=2,
             comment="Mother figure, deprived light/food/company "
             "(0 no - 2 yes)"),
        dict(name="s2b_q13", cctype="INT", min=0, max=2,
             comment="Mother figure, wouldn't let me mix (0 no - 2 yes)"),
        dict(name="s2b_q14", cctype="INT", min=0, max=2,
             comment="Mother figure, obedience through guilt (0 no - 2 yes)"),
        dict(name="s2b_q15", cctype="INT", min=0, max=2,
             comment="Mother figure, threatened to hurt people dear to me "
             "(0 no - 2 yes)"),
        dict(name="s2b_q16", cctype="INT", min=0, max=2,
             comment="Mother figure, forced to break law (0 no - 2 yes)"),
        dict(name="s2b_q17", cctype="INT", min=0, max=2,
             comment="Mother figure, said wanted me dead (0 no - 2 yes)"),
        dict(name="s2b_q1_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q2_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q3_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q4_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q5_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q6_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q7_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q8_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q9_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q10_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q11_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q12_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q13_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q14_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q15_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q16_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_q17_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s2b_age_began", cctype="FLOAT", min=0,
             comment="Age these experienced began (years)"),
        dict(name="s2b_extra", cctype="TEXT",
             comment="Extra detail"),

        dict(name="s3a_which_father_figure", cctype="INT",
             min=0, max=5,
             comment="Father figure, which one (0 none/skip, 1 birth father, "
             "2 stepfather, 3 other relative, 4 other non-relative, 5 other)"),
        dict(name="s3a_which_father_figure_other_detail",
             cctype="TEXT",
             comment="Father figure, other, detail"),
        dict(name="s3a_q1", cctype="INT", min=1, max=5,
             comment="Father figure, difficult to please (1 no - 5 yes)"),
        dict(name="s3a_q2", cctype="INT", min=1, max=5,
             comment="Father figure, concerned re my worries (1 no - 5 yes)"),
        dict(name="s3a_q3", cctype="INT", min=1, max=5,
             comment="Father figure, interested re school (1 no - 5 yes)"),
        dict(name="s3a_q4", cctype="INT", min=1, max=5,
             comment="Father figure, made me feel unwanted (1 no - 5 yes)"),
        dict(name="s3a_q5", cctype="INT", min=1, max=5,
             comment="Father figure, better when upset (1 no - 5 yes)"),
        dict(name="s3a_q6", cctype="INT", min=1, max=5,
             comment="Father figure, critical (1 no - 5 yes)"),
        dict(name="s3a_q7", cctype="INT", min=1, max=5,
             comment="Father figure, unsupervised <10y (1 no - 5 yes)"),
        dict(name="s3a_q8", cctype="INT", min=1, max=5,
             comment="Father figure, time to talk (1 no - 5 yes)"),
        dict(name="s3a_q9", cctype="INT", min=1, max=5,
             comment="Father figure, nuisance (1 no - 5 yes)"),
        dict(name="s3a_q10", cctype="INT", min=1, max=5,
             comment="Father figure, picked on unfairly (1 no - 5 yes)"),
        dict(name="s3a_q11", cctype="INT", min=1, max=5,
             comment="Father figure, there if needed (1 no - 5 yes)"),
        dict(name="s3a_q12", cctype="INT", min=1, max=5,
             comment="Father figure, interested in friends (1 no - 5 yes)"),
        dict(name="s3a_q13", cctype="INT", min=1, max=5,
             comment="Father figure, concerned re whereabouts (1 no - 5 yes)"),
        dict(name="s3a_q14", cctype="INT", min=1, max=5,
             comment="Father figure, cared when ill (1 no - 5 yes)"),
        dict(name="s3a_q15", cctype="INT", min=1, max=5,
             comment="Father figure, neglected basic needs (1 no - 5 yes)"),
        dict(name="s3a_q16", cctype="INT", min=1, max=5,
             comment="Father figure, preferred siblings (1 no - 5 yes)"),
        dict(name="s3a_extra", cctype="TEXT",
             comment="Father figure, extra detail"),

        dict(name="s3b_q1", cctype="INT", min=0, max=2,
             comment="Father figure, tease me (0 no - 2 yes)"),
        dict(name="s3b_q2", cctype="INT", min=0, max=2,
             comment="Father figure, made me keep secrets (0 no - 2 yes)"),
        dict(name="s3b_q3", cctype="INT", min=0, max=2,
             comment="Father figure, undermined confidence (0 no - 2 yes)"),
        dict(name="s3b_q4", cctype="INT", min=0, max=2,
             comment="Father figure, contradictory (0 no - 2 yes)"),
        dict(name="s3b_q5", cctype="INT", min=0, max=2,
             comment="Father figure, played on fears (0 no - 2 yes)"),
        dict(name="s3b_q6", cctype="INT", min=0, max=2,
             comment="Father figure, liked to see me suffer (0 no - 2 yes)"),
        dict(name="s3b_q7", cctype="INT", min=0, max=2,
             comment="Father figure, humiliated me (0 no - 2 yes)"),
        dict(name="s3b_q8", cctype="INT", min=0, max=2,
             comment="Father figure, shamed me before others (0 no - 2 yes)"),
        dict(name="s3b_q9", cctype="INT", min=0, max=2,
             comment="Father figure, rejecting (0 no - 2 yes)"),
        dict(name="s3b_q10", cctype="INT", min=0, max=2,
             comment="Father figure, took things I cherished (0 no - 2 yes)"),
        dict(name="s3b_q11", cctype="INT", min=0, max=2,
             comment="Father figure, eat disliked until sick (0 no - 2 yes)"),
        dict(name="s3b_q12", cctype="INT", min=0, max=2,
             comment="Father figure, deprived light/food/company "
             "(0 no - 2 yes)"),
        dict(name="s3b_q13", cctype="INT", min=0, max=2,
             comment="Father figure, wouldn't let me mix (0 no - 2 yes)"),
        dict(name="s3b_q14", cctype="INT", min=0, max=2,
             comment="Father figure, obedience through guilt (0 no - 2 yes)"),
        dict(name="s3b_q15", cctype="INT", min=0, max=2,
             comment="Father figure, threatened to hurt people dear to me "
             "(0 no - 2 yes)"),
        dict(name="s3b_q16", cctype="INT", min=0, max=2,
             comment="Father figure, forced to break law (0 no - 2 yes)"),
        dict(name="s3b_q17", cctype="INT", min=0, max=2,
             comment="Father figure, said wanted me dead (0 no - 2 yes)"),
        dict(name="s3b_q1_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q2_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q3_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q4_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q5_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q6_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q7_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q8_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q9_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q10_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q11_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q12_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q13_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q14_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q15_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q16_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_q17_frequency", cctype="INT", min=0, max=3,
             comment=FREQUENCY_COMMENT),
        dict(name="s3b_age_began", cctype="FLOAT", min=0,
             comment="Age these experienced began (years)"),
        dict(name="s3b_extra", cctype="TEXT",
             comment="Extra detail"),

        dict(name="s3c_q1", cctype="INT", min=1, max=5,
             comment="Responsibility (1 no - 5 yes)"),
        dict(name="s3c_q2", cctype="INT", min=1, max=5,
             comment="Housework (1 no - 5 yes)"),
        dict(name="s3c_q3", cctype="INT", min=1, max=5,
             comment="Look after young siblings (1 no - 5 yes)"),
        dict(name="s3c_q4", cctype="INT", min=1, max=5,
             comment="Cooking/cleaning (1 no - 5 yes)"),
        dict(name="s3c_q5", cctype="INT", min=1, max=5,
             comment="Miss school for domestic responsibilities "
             "(1 no - 5 yes)"),
        dict(name="s3c_q6", cctype="INT", min=1, max=5,
             comment="Miss seeing friends for domestic responsibilities "
             "(1 no - 5 yes)"),
        dict(name="s3c_q7", cctype="INT", min=1, max=5,
             comment="Parents said they couldn't cope (1 no - 5 yes)"),
        dict(name="s3c_q8", cctype="INT", min=1, max=5,
             comment="Parents looked to you for help (1 no - 5 yes)"),
        dict(name="s3c_q9", cctype="INT", min=1, max=5,
             comment="Parents coped if you were hurt/ill (1 no - 5 yes)"),
        dict(name="s3c_q10", cctype="INT", min=1, max=5,
             comment="Parents confided their problems (1 no - 5 yes)"),
        dict(name="s3c_q11", cctype="INT", min=1, max=5,
             comment="Parents relied on you for emotional support "
             "(1 no - 5 yes)"),
        dict(name="s3c_q12", cctype="INT", min=1, max=5,
             comment="Parents cried in front of you (1 no - 5 yes)"),
        dict(name="s3c_q13", cctype="INT", min=1, max=5,
             comment="Concerned/worried re parent (1 no - 5 yes)"),
        dict(name="s3c_q14", cctype="INT", min=1, max=5,
             comment="Tried to support/care for parent (1 no - 5 yes)"),
        dict(name="s3c_q15", cctype="INT", min=1, max=5,
             comment="Try to make parent smile when upset (1 no - 5 yes)"),
        dict(name="s3c_q16", cctype="INT", min=1, max=5,
             comment="Parents made you feel guilty for their sacrifices "
             "(1 no - 5 yes)"),
        dict(name="s3c_q17", cctype="INT", min=1, max=5,
             comment="Had to keep secrets for parent (1 no - 5 yes)"),
        dict(name="s3c_which_parent_cared_for", cctype="INT",
             min=0, max=4,
             comment="Which parent did you have to provide care for (0 none, "
             "1 mother, 2 father, 3 both, 4 other)"),
        dict(name="s3c_parent_mental_problem", cctype="INT",
             min=0, max=2, comment="Parent/s had emotional/mental health "
             "problems (0 no - 2 yes)"),
        dict(name="s3c_parent_physical_problem", cctype="INT",
             min=0, max=2, comment="Parent/s had disability/physical "
             "illness (0 no - 2 yes)"),

        dict(name="s4a_adultconfidant", cctype="BOOL",
             pv=PV.BIT, comment="Adult confidant?"),
        dict(name="s4a_adultconfidant_mother", cctype="BOOL",
             pv=PV.BIT, comment="Adult confidant, mother?"),
        dict(name="s4a_adultconfidant_father", cctype="BOOL",
             pv=PV.BIT, comment="Adult confidant, father?"),
        dict(name="s4a_adultconfidant_otherrelative", cctype="BOOL",
             pv=PV.BIT, comment="Adult confidant, other relative?"),
        dict(name="s4a_adultconfidant_familyfriend", cctype="BOOL",
             pv=PV.BIT, comment="Adult confidant, family friend?"),
        dict(name="s4a_adultconfidant_responsibleadult", cctype="BOOL",
             pv=PV.BIT, comment="Adult confidant, teacher/vicar/etc.?"),
        dict(name="s4a_adultconfidant_other", cctype="BOOL",
             pv=PV.BIT, comment="Adult confidant, other?"),
        dict(name="s4a_adultconfidant_other_detail", cctype="TEXT",
             comment="Adult confidant, other, detail"),
        dict(name="s4a_adultconfidant_additional", cctype="TEXT",
             comment="Adult confidant, additional notes"),

        dict(name="s4b_childconfidant", cctype="BOOL",
             pv=PV.BIT, comment="Child confidant?"),
        dict(name="s4b_childconfidant_sister", cctype="BOOL",
             pv=PV.BIT, comment="Child confidant, sister?"),
        dict(name="s4b_childconfidant_brother", cctype="BOOL",
             pv=PV.BIT, comment="Child confidant, brother?"),
        dict(name="s4b_childconfidant_otherrelative", cctype="BOOL",
             pv=PV.BIT, comment="Child confidant, other relative?"),
        dict(name="s4b_childconfidant_closefriend", cctype="BOOL",
             pv=PV.BIT, comment="Child confidant, close friend?"),
        dict(name="s4b_childconfidant_otherfriend", cctype="BOOL",
             pv=PV.BIT,
             comment="Child confidant, other less close friend(s)?"),
        dict(name="s4b_childconfidant_other", cctype="BOOL",
             pv=PV.BIT, comment="Child confidant, other person?"),
        dict(name="s4b_childconfidant_other_detail", cctype="TEXT",
             comment="Child confidant, other person, detail"),
        dict(name="s4b_childconfidant_additional", cctype="TEXT",
             comment="Child confidant, additional notes"),

        dict(name="s4c_closest_mother", cctype="BOOL",
             pv=PV.BIT, comment="Two closest people include: mother?"),
        dict(name="s4c_closest_father", cctype="BOOL",
             pv=PV.BIT, comment="Two closest people include: father?"),
        dict(name="s4c_closest_sibling", cctype="BOOL",
             pv=PV.BIT, comment="Two closest people include: sibling?"),
        dict(name="s4c_closest_otherrelative", cctype="BOOL",
             pv=PV.BIT, comment="Two closest people include: other relative?"),
        dict(name="s4c_closest_adultfriend", cctype="BOOL", pv=PV.BIT,
             comment="Two closest people include: adult family friend?"),
        dict(name="s4c_closest_childfriend", cctype="BOOL", pv=PV.BIT,
             comment="Two closest people include: friend your age?"),
        dict(name="s4c_closest_other", cctype="BOOL",
             pv=PV.BIT, comment="Two closest people include: other?"),
        dict(name="s4c_closest_other_detail", cctype="TEXT",
             comment="Two closest people include: other, detail"),
        dict(name="s4c_closest_additional", cctype="TEXT",
             comment="Two closest people include: additional notes"),

        dict(name="s5c_physicalabuse", cctype="BOOL", pv=PV.BIT,
             comment="Physical abuse?"),
        dict(name="s5c_abused_by_mother", cctype="BOOL", pv=PV.BIT,
             comment="Physical abuse, by mother?"),
        dict(name="s5c_abused_by_father", cctype="BOOL", pv=PV.BIT,
             comment="Physical abuse, by father?"),
        dict(name="s5c_mother_abuse_age_began", cctype="FLOAT",
             comment="Physical abuse, by mother, age began (y)"),
        dict(name="s5c_father_abuse_age_began", cctype="FLOAT",
             comment="Physical abuse, by father, age began (y)"),
        dict(name="s5c_mother_hit_more_than_once", cctype="BOOL",
             pv=PV.BIT,
             comment="Physical abuse, by mother, hit on >1 occasion"),
        dict(name="s5c_father_hit_more_than_once", cctype="BOOL",
             pv=PV.BIT,
             comment="Physical abuse, by father, hit on >1 occasion"),
        dict(name="s5c_mother_hit_how", cctype="INT",
             min=1, max=4,
             comment="Physical abuse, by mother, hit how (1 belt/stick, "
             "2 punched/kicked, 3 hit with hand, 4 other)"),
        dict(name="s5c_father_hit_how", cctype="INT",
             min=1, max=4,
             comment="Physical abuse, by father, hit how (1 belt/stick, "
             "2 punched/kicked, 3 hit with hand, 4 other)"),
        dict(name="s5c_mother_injured", cctype="BOOL", pv=PV.BIT,
             comment="Physical abuse, by mother, injured?"),
        dict(name="s5c_father_injured", cctype="BOOL", pv=PV.BIT,
             comment="Physical abuse, by father, injured?"),
        dict(name="s5c_mother_out_of_control", cctype="BOOL", pv=PV.BIT,
             comment="Physical abuse, by mother, out of control?"),
        dict(name="s5c_father_out_of_control", cctype="BOOL", pv=PV.BIT,
             comment="Physical abuse, by father, out of control?"),
        dict(name="s5c_parental_abuse_description", cctype="TEXT",
             comment="Physical abuse, description"),
        dict(name="s5c_abuse_by_nonparent", cctype="BOOL", pv=PV.BIT,
             comment="Physical abuse, by anyone else in household?"),
        dict(name="s5c_nonparent_abuse_description", cctype="TEXT",
             comment="Physical abuse, nonparent, description"),

        dict(name="s6_any_unwanted_sexual_experience", cctype="BOOL",
             pv=PV.BIT,
             comment="Any unwanted sexual experiences (0 no - 2 yes)"),
        dict(name="s6_unwanted_intercourse", cctype="BOOL", pv=PV.BIT,
             comment="Unwanted intercourse before 17yo (0 no - 2 yes)"),
        dict(name="s6_upsetting_sexual_adult_authority", cctype="BOOL",
             pv=PV.BIT, comment="Upsetting sexual experiences under 17yo with "
             "related adult or someone in authority (0 no - 2 yes)"),
        dict(name="s6_first_age", cctype="FLOAT", min=0,
             comment="Sexual abuse, first experience, age it began"),
        dict(name="s6_other_age", cctype="FLOAT", min=0,
             comment="Sexual abuse, other experience, age it began"),
        dict(name="s6_first_person_known", cctype="BOOL", pv=PV.BIT,
             comment="Sexual abuse, first experience, knew the person?"),
        dict(name="s6_other_person_known", cctype="BOOL", pv=PV.BIT,
             comment="Sexual abuse, other experience, knew the person?"),
        dict(name="s6_first_relative", cctype="BOOL", pv=PV.BIT,
             comment="Sexual abuse, first experience, person was a relative?"),
        dict(name="s6_other_relative", cctype="BOOL", pv=PV.BIT,
             comment="Sexual abuse, other experience, person was a relative?"),
        dict(name="s6_first_in_household", cctype="BOOL", pv=PV.BIT,
             comment="Sexual abuse, first experience, person lived in "
             "household?"),
        dict(name="s6_other_in_household", cctype="BOOL", pv=PV.BIT,
             comment="Sexual abuse, other experience, person lived in "
             "household?"),
        dict(name="s6_first_more_than_once", cctype="BOOL", pv=PV.BIT,
             comment="Sexual abuse, first experience, happened more than "
             "once?"),
        dict(name="s6_other_more_than_once", cctype="BOOL", pv=PV.BIT,
             comment="Sexual abuse, other experience, happened more than "
             "once?"),
        dict(name="s6_first_touch_privates_subject", cctype="BOOL",
             pv=PV.BIT, comment="Sexual abuse, first experience, touched your "
             "private parts?"),
        dict(name="s6_other_touch_privates_subject", cctype="BOOL",
             pv=PV.BIT, comment="Sexual abuse, other experience, touched your "
             "private parts?"),
        dict(name="s6_first_touch_privates_other", cctype="BOOL",
             pv=PV.BIT, comment="Sexual abuse, first experience, touched their"
             " private parts?"),
        dict(name="s6_other_touch_privates_other", cctype="BOOL",
             pv=PV.BIT, comment="Sexual abuse, other experience, touched their"
             " private parts?"),
        dict(name="s6_first_intercourse", cctype="BOOL", pv=PV.BIT,
             comment="Sexual abuse, first experience, sexual intercourse?"),
        dict(name="s6_other_intercourse", cctype="BOOL", pv=PV.BIT,
             comment="Sexual abuse, other experience, sexual intercourse?"),
        dict(name="s6_unwanted_sexual_description", cctype="TEXT",
             comment="Sexual abuse, description"),

        dict(name="any_other_comments", cctype="TEXT",
             comment="Any other comments"),
    ]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="parental_loss_risk", cctype="BOOL",
                 value=self.parental_loss_risk(),
                 comment="Parental loss risk factor?"),
            dict(name="parental_loss_high_risk", cctype="BOOL",
                 value=self.parental_loss_high_risk(),
                 comment="Parental loss higher risk factor?"),
            dict(name="mother_antipathy", cctype="INT",
                 value=self.mother_antipathy(),
                 comment="Maternal antipathy score (8-40)"),
            dict(name="mother_neglect", cctype="INT",
                 value=self.mother_neglect(),
                 comment="Maternal neglect score (8-40)"),
            dict(name="mother_psychological_abuse", cctype="INT",
                 value=self.mother_psychological_abuse(),
                 comment="Maternal psychological abuse score (0-85)"),
            dict(name="father_antipathy", cctype="INT",
                 value=self.father_antipathy(),
                 comment="Paternal antipathy score (8-40)"),
            dict(name="father_neglect", cctype="INT",
                 value=self.father_neglect(),
                 comment="Paternal neglect score (8-40)"),
            dict(name="father_psychological_abuse", cctype="INT",
                 value=self.father_psychological_abuse(),
                 comment="Paternal psychological abuse score (0-85)"),
            dict(name="role_reversal", cctype="INT",
                 value=self.role_reversal(),
                 comment="Role reversal score (17-85)"),
            dict(name="physical_abuse_screen", cctype="INT",
                 value=self.physical_abuse_screen(),
                 comment="Physical abuse screen (0-1)"),
            dict(name="physical_abuse_severity_mother", cctype="INT",
                 value=self.physical_abuse_severity_mother(),
                 comment="Maternal physical abuse severity score (0-4)"),
            dict(name="physical_abuse_severity_father", cctype="INT",
                 value=self.physical_abuse_severity_father(),
                 comment="Paternal physical abuse severity score (0-4)"),
            dict(name="sexual_abuse_screen", cctype="INT",
                 value=self.sexual_abuse_screen(),
                 comment="Sexual abuse screen (0-3)"),
            dict(name="sexual_abuse_score_first", cctype="INT",
                 value=self.sexual_abuse_score_first(),
                 comment="First sexual abuse severity score (0-7)"),
            dict(name="sexual_abuse_score_other", cctype="INT",
                 value=self.sexual_abuse_score_other(),
                 comment="Other sexual abuse severity score (0-7)"),
        ]

    # -------------------------------------------------------------------------
    # Complete?
    # -------------------------------------------------------------------------

    def is_complete(self):
        return (
            self.complete_1A() and
            self.complete_1B() and
            self.complete_1C() and
            self.complete_2A() and
            self.complete_2B() and
            self.complete_3A() and
            self.complete_3B() and
            self.complete_3C() and
            self.complete_4A() and
            self.complete_4B() and
            self.complete_4C() and
            self.complete_5() and
            self.complete_6() and
            self.field_contents_valid()
        )

    def is_at_least_one_field_true(self, fields):
        for f in fields:
            if getattr(self, f):
                return True
        return True

    def complete_1A(self):
        if not self.is_at_least_one_field_true([
            "s1a_motherfigure_birthmother",
            "s1a_motherfigure_stepmother",
            "s1a_motherfigure_femalerelative",
            "s1a_motherfigure_familyfriend",
            "s1a_motherfigure_fostermother",
            "s1a_motherfigure_adoptivemother",
            "s1a_motherfigure_other",
            "s1a_fatherfigure_birthfather",
            "s1a_fatherfigure_stepfather",
            "s1a_fatherfigure_malerelative",
            "s1a_fatherfigure_familyfriend",
            "s1a_fatherfigure_fosterfather",
            "s1a_fatherfigure_adoptivefather",
            "s1a_fatherfigure_other",
        ]):
            return False
        if (self.s1a_motherfigure_other and
                not self.s1a_motherfigure_other_detail):
            return False
        if (self.s1a_motherfigure_femalerelative and
                not self.s1a_motherfigure_femalerelative_detail):
            return False
        if (self.s1a_fatherfigure_other and
                not self.s1a_fatherfigure_other_detail):
            return False
        if (self.s1a_fatherfigure_malerelative and
                not self.s1a_fatherfigure_malerelative_detail):
            return False
        return True

    def complete_1B(self):
        if self.s1b_institution is None:
            return False
        if self.s1b_institution and self.s1b_institution_time_years is None:
            return False
        return True

    def complete_1C(self):
        if self.s1c_mother_died is None or self.s1c_father_died is None:
            return False
        if self.s1c_mother_died and self.s1c_mother_died_subject_aged is None:
            return False
        if self.s1c_father_died and self.s1c_father_died_subject_aged is None:
            return False
        if (self.s1c_separated_from_mother is None or
                self.s1c_separated_from_father is None):
            return False
        if self.s1c_separated_from_mother:
            if not self.are_all_fields_complete([
                "s1c_first_separated_from_mother_aged",
                "s1c_mother_how_long_first_separation_years",
                "s1c_mother_separation_reason"
            ]):
                return False
        if self.s1c_separated_from_father:
            if not self.are_all_fields_complete([
                "s1c_first_separated_from_father_aged",
                "s1c_father_how_long_first_separation_years",
                "s1c_father_separation_reason"
            ]):
                return False
        return True

    def complete_2A(self):
        if self.s2a_which_mother_figure is None:
            return False
        if self.s2a_which_mother_figure == 0:
            return True
        if (self.s2a_which_mother_figure == 5 and
                self.s2a_which_mother_figure_other_detail is None):
            return False
        for i in range(1, 16):  # not q16 (siblings)
            if getattr(self, "s2a_q" + str(i)) is None:
                return False
        return True

    def complete_2B(self):
        abuse = False
        if self.s2a_which_mother_figure == 0:
            return True
        for i in range(1, 18):
            if getattr(self, "s2b_q" + str(i)) is None:
                return False
            if getattr(self, "s2b_q" + str(i)) != 0:
                abuse = True
                if getattr(self, "s2b_q" + str(i) + "_frequency") is None:
                    return False
        if abuse and self.s2b_age_began is None:
            return False
        return True

    def complete_3A(self):
        if self.s3a_which_father_figure is None:
            return False
        if self.s3a_which_father_figure == 0:
            return True
        if (self.s3a_which_father_figure == 5 and
                self.s3a_which_father_figure_other_detail is None):
            return False
        for i in range(1, 16):  # not q16 (siblings)
            if getattr(self, "s3a_q" + str(i)) is None:
                return False
        return True

    def complete_3B(self):
        abuse = False
        if self.s3a_which_father_figure == 0:
            return True
        for i in range(1, 18):
            if getattr(self, "s3b_q" + str(i)) is None:
                return False
            if getattr(self, "s3b_q" + str(i)) != 0:
                abuse = True
                if getattr(self, "s3b_q" + str(i) + "_frequency") is None:
                    return False
        if abuse and self.s3b_age_began is None:
            return False
        return True

    def complete_3C(self):
        return self.are_all_fields_complete([
            "s3c_q1",
            "s3c_q2",
            "s3c_q3",
            "s3c_q4",
            "s3c_q5",
            "s3c_q6",
            "s3c_q7",
            "s3c_q8",
            "s3c_q9",
            "s3c_q10",
            "s3c_q11",
            "s3c_q12",
            "s3c_q13",
            "s3c_q14",
            "s3c_q15",
            "s3c_q16",
            "s3c_q17",
            "s3c_which_parent_cared_for",
            "s3c_parent_mental_problem",
            "s3c_parent_physical_problem"
        ])

    def complete_4A(self):
        if self.s4a_adultconfidant is None:
            return False
        if not self.s4a_adultconfidant:
            return True
        if not self.is_at_least_one_field_true([
            "s4a_adultconfidant_mother",
            "s4a_adultconfidant_father",
            "s4a_adultconfidant_otherrelative",
            "s4a_adultconfidant_familyfriend",
            "s4a_adultconfidant_responsibleadult",
            "s4a_adultconfidant_other"
        ]):
            return False
        if self.s4a_adultconfidant_other \
                and not self.s4a_adultconfidant_other_detail:
            return False
        return True

    def complete_4B(self):
        if self.s4b_childconfidant is None:
            return False
        if not self.s4b_childconfidant:
            return True
        if not self.is_at_least_one_field_true([
            "s4b_childconfidant_sister",
            "s4b_childconfidant_brother",
            "s4b_childconfidant_otherrelative",
            "s4b_childconfidant_closefriend",
            "s4b_childconfidant_otherfriend",
            "s4b_childconfidant_other"
        ]):
            return False
        if self.s4b_childconfidant_other \
                and not self.s4b_childconfidant_other_detail:
            return False
        return True

    def complete_4C(self):
        n = 0
        if self.s4c_closest_mother:
            n += 1
        if self.s4c_closest_father:
            n += 1
        if self.s4c_closest_sibling:
            n += 1
        if self.s4c_closest_otherrelative:
            n += 1
        if self.s4c_closest_adultfriend:
            n += 1
        if self.s4c_closest_childfriend:
            n += 1
        if self.s4c_closest_other:
            n += 1
        if n < 2:
            return False
        if self.s4c_closest_other and not self.s4c_closest_other_detail:
            return False
        return True

    def complete_5(self):
        if self.s5c_physicalabuse is None:
            return False
        if self.s5c_physicalabuse == 0:
            return True
        if (self.s5c_abused_by_mother is None or
                self.s5c_abused_by_father is None or
                self.s5c_abuse_by_nonparent is None):
            return False
        if self.s5c_abused_by_mother:
            if not self.are_all_fields_complete([
                "s5c_mother_abuse_age_began",
                "s5c_mother_hit_more_than_once",
                "s5c_mother_hit_how",
                "s5c_mother_injured",
                "s5c_mother_out_of_control"
            ]):
                return False
        if self.s5c_abused_by_father:
            if not self.are_all_fields_complete([
                "s5c_father_abuse_age_began",
                "s5c_father_hit_more_than_once",
                "s5c_father_hit_how",
                "s5c_father_injured",
                "s5c_father_out_of_control"
            ]):
                return False
        if (self.s5c_abuse_by_nonparent and
                not self.s5c_nonparent_abuse_description):
            return False
        return True

    def complete_6(self):
        if (self.s6_any_unwanted_sexual_experience is None or
                self.s6_unwanted_intercourse is None or
                self.s6_upsetting_sexual_adult_authority is None):
            return False
        if (self.s6_any_unwanted_sexual_experience == 0 and
                self.s6_unwanted_intercourse == 0 and
                self.s6_upsetting_sexual_adult_authority == 0):
            return True
        if not self.are_all_fields_complete([
            "s6_first_age",
            "s6_first_person_known",
            "s6_first_relative",
            "s6_first_in_household",
            "s6_first_more_than_once",
            "s6_first_touch_privates_subject",
            "s6_first_touch_privates_other",
            "s6_first_intercourse"
        ]):
            return False
        # no checks for "other experience"
        return True

    # -------------------------------------------------------------------------
    # Scoring
    # -------------------------------------------------------------------------

    def total_sum_abort_if_none(self, fields):
        total = 0
        for field in fields:
            value = getattr(self, field)
            if value is None:
                return None
            total += value
        return total

    def total_nonzero_scores_1_abort_if_none(self, fields):
        total = 0
        for field in fields:
            value = getattr(self, field)
            if value is None:
                return None
            if value:
                total += 1
        return total

    def parental_loss_risk(self):
        return (
            self.s1c_mother_died or
            self.s1c_father_died or
            self.s1c_separated_from_mother or
            self.s1c_separated_from_father
        )

    def parental_loss_high_risk(self):
        return (
            self.s1c_separated_from_mother and (
                self.s1c_mother_separation_reason == 5 or
                self.s1c_mother_separation_reason == 6
            ) or
            self.s1c_separated_from_father and (
                self.s1c_father_separation_reason == 5 or
                self.s1c_father_separation_reason == 6
            )
        )

    def mother_antipathy(self):
        if self.s2a_which_mother_figure == 0:
            return None
        total = 0
        for i in [1, 4, 6, 8, 9, 10, 11, 16]:
            score = getattr(self, "s2a_q" + str(i))
            if i == 16 and score is None:
                # Q16 is allowed to be blank (if no siblings)
                score = 0
            if score is None:
                return None
            if i in [8, 11]:
                score = 6 - score  # reverse
            total += score
        return total

    def father_antipathy(self):
        if self.s3a_which_father_figure == 0:
            return None
        total = 0
        for i in [1, 4, 6, 8, 9, 10, 11, 16]:
            score = getattr(self, "s3a_q" + str(i))
            if i == 16 and score is None:
                # Q16 is allowed to be blank (if no siblings)
                score = 0
            if score is None:
                return None
            if i in [8, 11]:
                score = 6 - score  # reverse
            total += score
        return total

    def mother_neglect(self):
        if self.s2a_which_mother_figure == 0:
            return None
        total = 0
        for i in [2, 3, 5, 7, 12, 13, 14, 15]:
            score = getattr(self, "s2a_q" + str(i))
            if score is None:
                return None
            if i in [2, 3, 5, 12, 13, 14]:
                score = 6 - score  # reverse
            total += score
        return total

    def father_neglect(self):
        if self.s3a_which_father_figure == 0:
            return None
        total = 0
        for i in [2, 3, 5, 7, 12, 13, 14, 15]:
            score = getattr(self, "s3a_q" + str(i))
            if score is None:
                return None
            if i in [2, 3, 5, 12, 13, 14]:
                score = 6 - score  # reverse
            total += score
        return total

    def mother_psychological_abuse(self):
        if self.s2a_which_mother_figure == 0:
            return None
        total = 0
        for i in range(1, 18):
            score = getattr(self, "s2b_q" + str(i))
            if score is None:
                return None
            total += score
            freqscore = getattr(self, "s2b_q" + str(i) + "_frequency")
            if score != 0 and freqscore is None:
                return None
            if freqscore is not None:
                total += freqscore
        return total

    def father_psychological_abuse(self):
        if self.s3a_which_father_figure == 0:
            return None
        total = 0
        for i in range(1, 18):
            score = getattr(self, "s3b_q" + str(i))
            if score is None:
                return None
            total += score
            freqscore = getattr(self, "s3b_q" + str(i) + "_frequency")
            if score != 0 and freqscore is None:
                return None
            if freqscore is not None:
                total += freqscore
        return total

    def role_reversal(self):
        total = 0
        for i in range(1, 18):
            score = getattr(self, "s3c_q" + str(i))
            if score is None:
                return None
            total += score
        return total

    def physical_abuse_screen(self):
        FIELDS = [
            "s5c_physicalabuse"
        ]
        return self.total_nonzero_scores_1_abort_if_none(FIELDS)

    def physical_abuse_severity_mother(self):
        if self.physical_abuse_screen() == 0:
            return 0
        if self.s5c_abused_by_mother == 0:
            return 0
        MAINFIELDS = [
            "s5c_mother_hit_more_than_once",
            "s5c_mother_injured",
            "s5c_mother_out_of_control"
        ]
        total = self.total_nonzero_scores_1_abort_if_none(MAINFIELDS)
        if total is None:
            return None
        if self.s5c_mother_hit_how is None:
            return None
        if self.s5c_mother_hit_how == 1 or self.s5c_mother_hit_how == 2:
            total += 1
        return total

    def physical_abuse_severity_father(self):
        if self.physical_abuse_screen() == 0:
            return 0
        if self.s5c_abused_by_father == 0:
            return 0
        MAINFIELDS = [
            "s5c_father_hit_more_than_once",
            "s5c_father_injured",
            "s5c_father_out_of_control"
        ]
        total = self.total_nonzero_scores_1_abort_if_none(MAINFIELDS)
        if total is None:
            return None
        if self.s5c_father_hit_how is None:
            return None
        if self.s5c_father_hit_how == 1 or self.s5c_father_hit_how == 2:
            total += 1
        return total

    def sexual_abuse_screen(self):
        FIELDS = [
            "s6_any_unwanted_sexual_experience",
            "s6_unwanted_intercourse",
            "s6_upsetting_sexual_adult_authority"
        ]
        return self.total_nonzero_scores_1_abort_if_none(FIELDS)

    def sexual_abuse_score_first(self):
        if self.sexual_abuse_screen() == 0:
            return 0
        FIELDS = [
            "s6_first_person_known",
            "s6_first_relative",
            "s6_first_in_household",
            "s6_first_more_than_once",
            "s6_first_touch_privates_subject",
            "s6_first_touch_privates_other",
            "s6_first_intercourse"
        ]
        return self.total_nonzero_scores_1_abort_if_none(FIELDS)

    def sexual_abuse_score_other(self):
        if self.sexual_abuse_screen() == 0:
            return 0
        FIELDS = [
            "s6_other_person_known",
            "s6_other_relative",
            "s6_other_in_household",
            "s6_other_more_than_once",
            "s6_other_touch_privates_subject",
            "s6_other_touch_privates_other",
            "s6_other_intercourse"
        ]
        return self.total_nonzero_scores_1_abort_if_none(FIELDS)

    # -------------------------------------------------------------------------
    # HTML
    # -------------------------------------------------------------------------

    def get_task_html(self):
        SEPARATION_MAP = {
            None: None,
            1: "1 — " + WSTRING("cecaq3_1c_separation_reason1"),
            2: "2 — " + WSTRING("cecaq3_1c_separation_reason2"),
            3: "3 — " + WSTRING("cecaq3_1c_separation_reason3"),
            4: "4 — " + WSTRING("cecaq3_1c_separation_reason4"),
            5: "5 — " + WSTRING("cecaq3_1c_separation_reason5"),
            6: "6 — " + WSTRING("cecaq3_1c_separation_reason6"),
        }
        MOTHERFIGURE_MAP = {
            None: None,
            0: "0 — " + WSTRING("cecaq3_2a_which_option0"),
            1: "1 — " + WSTRING("cecaq3_2a_which_option1"),
            2: "2 — " + WSTRING("cecaq3_2a_which_option2"),
            3: "3 — " + WSTRING("cecaq3_2a_which_option3"),
            4: "4 — " + WSTRING("cecaq3_2a_which_option4"),
            5: "5 — " + WSTRING("cecaq3_2a_which_option5"),
        }
        FATHERFIGURE_MAP = {
            None: None,
            0: "0 — " + WSTRING("cecaq3_3a_which_option0"),
            1: "1 — " + WSTRING("cecaq3_3a_which_option1"),
            2: "2 — " + WSTRING("cecaq3_3a_which_option2"),
            3: "3 — " + WSTRING("cecaq3_3a_which_option3"),
            4: "4 — " + WSTRING("cecaq3_3a_which_option4"),
            5: "5 — " + WSTRING("cecaq3_3a_which_option5"),
        }
        NO_YES_5WAY_MAP = {
            None: None,
            1: "1 — " + WSTRING("cecaq3_options5way_notoyes_1"),
            2: "2 — (between not-at-all and unsure)",
            3: "3 — " + WSTRING("cecaq3_options5way_notoyes_3"),
            4: "4 — (between unsure and yes-definitely)",
            5: "5 — " + WSTRING("cecaq3_options5way_notoyes_5"),
        }
        NO_YES_3WAY_MAP = {
            None: None,
            0: "0 — " + WSTRING("cecaq3_options3way_noto_yes_0"),
            1: "1 — " + WSTRING("cecaq3_options3way_noto_yes_1"),
            2: "2 — " + WSTRING("cecaq3_options3way_noto_yes_2"),
        }
        FREQUENCY_MAP = {
            None: None,
            0: "0 — " + WSTRING("cecaq3_optionsfrequency0"),
            1: "1 — " + WSTRING("cecaq3_optionsfrequency1"),
            2: "2 — " + WSTRING("cecaq3_optionsfrequency2"),
            3: "3 — " + WSTRING("cecaq3_optionsfrequency3"),
        }
        PARENT_CARED_FOR_MAP = {
            None: None,
            0: "0 — " + WSTRING("cecaq3_3c_whichparentcaredfor_option0"),
            1: "1 — " + WSTRING("cecaq3_3c_whichparentcaredfor_option1"),
            2: "2 — " + WSTRING("cecaq3_3c_whichparentcaredfor_option2"),
            3: "3 — " + WSTRING("cecaq3_3c_whichparentcaredfor_option3"),
            4: "4 — " + WSTRING("cecaq3_3c_whichparentcaredfor_option4"),
        }
        HITTING_MAP = {
            None: None,
            1: "1 — " + WSTRING("cecaq3_5_hit_option_1"),
            2: "2 — " + WSTRING("cecaq3_5_hit_option_2"),
            3: "3 — " + WSTRING("cecaq3_5_hit_option_3"),
            4: "4 — " + WSTRING("cecaq3_5_hit_option_4"),
        }
        html = (
            """
                <div class="summary">
                    <table class="summary">
            """ +
            self.get_is_complete_tr() +
            tr_qa("Parental loss risk factor? <sup>[1]</sup>",
                  get_yes_no(self.parental_loss_risk())) +
            tr_qa("Parental loss higher risk factor? <sup>[2]</sup>",
                  get_yes_no(self.parental_loss_high_risk())) +
            tr_qa("Maternal antipathy score (8–40) <sup>[3]</sup>",
                  self.mother_antipathy()) +
            tr_qa("Maternal neglect score (8–40) <sup>[3]</sup>",
                  self.mother_neglect()) +
            tr_qa("Maternal psychological abuse score (0–85) <sup>[4]</sup>",
                  self.mother_psychological_abuse()) +
            tr_qa("Paternal antipathy score (8–40) <sup>[3]</sup>",
                  self.father_antipathy()) +
            tr_qa("Paternal neglect score (8–40) <sup>[3]</sup>",
                  self.father_neglect()) +
            tr_qa("Paternal psychological abuse score (0–85) <sup>[4]</sup>",
                  self.father_psychological_abuse()) +
            tr_qa("Role reversal score (17–85) <sup>[5]</sup>",
                  self.role_reversal()) +
            tr_qa("Physical abuse screen (0–1) <sup>[6]</sup>",
                  self.physical_abuse_screen()) +
            tr_qa("Maternal physical abuse severity score (0–4) "
                  "<sup>[6]</sup>",
                  self.physical_abuse_severity_mother()) +
            tr_qa("Paternal physical abuse severity score (0–4) "
                  "<sup>[6]</sup>",
                  self.physical_abuse_severity_father()) +
            tr_qa("Sexual abuse screen (0–3) <sup>[7]</sup>",
                  self.sexual_abuse_screen()) +
            tr_qa("First sexual abuse severity score (0–7) <sup>[7]</sup>",
                  self.sexual_abuse_score_first()) +
            tr_qa("Other sexual abuse severity score (0–7) <sup>[7]</sup>",
                  self.sexual_abuse_score_other()) +
            """
                    </table>
                </div>
                <table class="taskdetail">
            """ +

            subheading_spanning_two_columns("1A: " + WSTRING("cecaq3_1a_q")) +
            subsubheading_from_wstring("cecaq3_1a_motherfigures") +
            wstring_boolean("cecaq3_1a_mf_birthmother",
                            self.s1a_motherfigure_birthmother) +
            wstring_boolean("cecaq3_1a_mf_stepmother",
                            self.s1a_motherfigure_stepmother) +
            wstring_boolean("cecaq3_1a_mf_femalerelative",
                            self.s1a_motherfigure_femalerelative) +
            string_string("(Female relative details)",
                          self.s1a_motherfigure_femalerelative_detail) +
            wstring_boolean("cecaq3_1a_mf_familyfriend",
                            self.s1a_motherfigure_familyfriend) +
            wstring_boolean("cecaq3_1a_mf_fostermother",
                            self.s1a_motherfigure_fostermother) +
            wstring_boolean("cecaq3_1a_mf_adoptivemother",
                            self.s1a_motherfigure_adoptivemother) +
            wstring_boolean("cecaq3_other", self.s1a_motherfigure_other) +
            string_string("(Other, details)",
                          self.s1a_motherfigure_other_detail) +

            subsubheading_from_wstring("cecaq3_1a_fatherfigures") +
            wstring_boolean("cecaq3_1a_ff_birthfather",
                            self.s1a_fatherfigure_birthfather) +
            wstring_boolean("cecaq3_1a_ff_stepfather",
                            self.s1a_fatherfigure_stepfather) +
            wstring_boolean("cecaq3_1a_ff_malerelative",
                            self.s1a_fatherfigure_malerelative) +
            string_string("(Male relative details)",
                          self.s1a_fatherfigure_malerelative_detail) +
            wstring_boolean("cecaq3_1a_ff_familyfriend",
                            self.s1a_fatherfigure_familyfriend) +
            wstring_boolean("cecaq3_1a_ff_fosterfather",
                            self.s1a_fatherfigure_fosterfather) +
            wstring_boolean("cecaq3_1a_ff_adoptivefather",
                            self.s1a_fatherfigure_adoptivefather) +
            wstring_boolean("cecaq3_other", self.s1a_fatherfigure_other) +
            string_string("(Other, details)",
                          self.s1a_fatherfigure_other_detail) +

            subheading_from_string("1B: " + WSTRING("cecaq3_1b_q")) +
            wstring_boolean("cecaq3_1b_q", self.s1b_institution) +
            wstring_numeric("cecaq3_1b_q_how_long",
                            self.s1b_institution_time_years) +

            subheading_from_string("1C: " + WSTRING("cecaq3_1c_heading")) +
            subsubheading_from_wstring("cecaq3_mother") +

            string_boolean("Mother died before age 17",
                           self.s1c_mother_died) +
            wstring_numeric("cecaq3_1c_parentdiedage",
                            self.s1c_mother_died_subject_aged) +
            string_boolean("Separated from mother for >1y",
                           self.s1c_separated_from_mother) +
            wstring_numeric("cecaq3_1c_age_first_separated",
                            self.s1c_first_separated_from_mother_aged) +
            wstring_numeric("cecaq3_1c_how_long_separation",
                            self.s1c_mother_how_long_first_separation_years) +
            wstring_dict("cecaq3_1c_separation_reason",
                         self.s1c_mother_separation_reason, SEPARATION_MAP) +

            subsubheading_from_wstring("cecaq3_father") +
            string_boolean("Father died before age 17", self.s1c_father_died) +
            wstring_numeric("cecaq3_1c_parentdiedage",
                            self.s1c_father_died_subject_aged) +
            string_boolean("Separated from father for >1y",
                           self.s1c_separated_from_father) +
            wstring_numeric("cecaq3_1c_age_first_separated",
                            self.s1c_first_separated_from_father_aged) +
            wstring_numeric("cecaq3_1c_how_long_separation",
                            self.s1c_father_how_long_first_separation_years) +
            wstring_dict("cecaq3_1c_separation_reason",
                         self.s1c_father_separation_reason, SEPARATION_MAP) +
            wstring_string("cecaq3_please_describe_experience",
                           self.s1c_describe_experience) +

            subheading_from_string("2A: " + WSTRING("cecaq3_2a_heading")) +
            wstring_dict("cecaq3_2a_which",
                         self.s2a_which_mother_figure, MOTHERFIGURE_MAP) +
            wstring_string("cecaq3_rnc_if_other_describe",
                           self.s2a_which_mother_figure_other_detail)
        )
        for i in range(1, 17):
            html += string_dict(str(i) + ". " + WSTRING("cecaq3_2a_q" +
                                                        str(i)),
                                getattr(self, "s2a_q" + str(i)),
                                NO_YES_5WAY_MAP)
        html += (
            wstring_string("cecaq3_2a_add_anything", self.s2a_extra) +
            subheading_from_string("2B: " + WSTRING("cecaq3_2b_heading"))
        )
        for i in range(1, 18):
            html += tr(
                str(i) + ". " + WSTRING("cecaq3_2b_q" + str(i)),
                answer(get_from_dict(NO_YES_3WAY_MAP,
                                     getattr(self, "s2b_q" + str(i)))) +
                " (" +
                answer(get_from_dict(
                    FREQUENCY_MAP,
                    getattr(self, "s2b_q" + str(i) + "_frequency"))) +
                ")"
            )
        html += (
            wstring_boolean("cecaq3_if_any_what_age", self.s2b_age_began) +
            wstring_string("cecaq3_is_there_more_you_want_to_say",
                           self.s2b_extra) +

            subheading_from_string("3A: " + WSTRING("cecaq3_3a_heading")) +
            wstring_dict("cecaq3_2a_which",
                         self.s3a_which_father_figure, FATHERFIGURE_MAP) +
            wstring_string("cecaq3_rnc_if_other_describe",
                           self.s3a_which_father_figure_other_detail)
        )
        for i in range(1, 17):
            html += string_dict(
                str(i) + ". " + WSTRING("cecaq3_3a_q" + str(i)),
                getattr(self, "s3a_q" + str(i)), NO_YES_5WAY_MAP)
        html += (
            wstring_string("cecaq3_3a_add_anything", self.s3a_extra) +
            subheading_from_string("3B: " + WSTRING("cecaq3_3b_heading"))
        )
        for i in range(1, 18):
            html += tr(
                str(i) + ". " + WSTRING("cecaq3_3b_q" + str(i)),
                answer(get_from_dict(NO_YES_3WAY_MAP,
                                     getattr(self, "s3b_q" + str(i)))) +
                " (" +
                answer(get_from_dict(
                    FREQUENCY_MAP,
                    getattr(self, "s3b_q" + str(i) + "_frequency"))) +
                ")"
            )
        html += (
            wstring_boolean("cecaq3_if_any_what_age", self.s3b_age_began) +
            wstring_string("cecaq3_is_there_more_you_want_to_say",
                           self.s3b_extra) +
            subheading_from_string("3C: " + WSTRING("cecaq3_3c_heading"))
        )
        for i in range(1, 18):
            html += string_dict(
                str(i) + ". " + WSTRING("cecaq3_3c_q" + str(i)),
                getattr(self, "s3c_q" + str(i)), NO_YES_5WAY_MAP)
        html += (
            wstring_dict("cecaq3_3c_which_parent_cared_for",
                         self.s3c_which_parent_cared_for,
                         PARENT_CARED_FOR_MAP) +
            wstring_boolean("cecaq3_3c_parent_mental_problem",
                            self.s3c_parent_mental_problem) +
            wstring_boolean("cecaq3_3c_parent_physical_problem",
                            self.s3c_parent_physical_problem) +

            subheading_from_string("4: " + WSTRING("cecaq3_4_heading")) +
            subsubheading_from_string("(Adult confidant)") +
            wstring_boolean("cecaq3_4a_q", self.s4a_adultconfidant) +
            subsubheading_from_wstring("cecaq3_4_if_so_who") +
            wstring_boolean("cecaq3_4a_option_mother",
                            self.s4a_adultconfidant_mother) +
            wstring_boolean("cecaq3_4a_option_father",
                            self.s4a_adultconfidant_father) +
            wstring_boolean("cecaq3_4a_option_relative",
                            self.s4a_adultconfidant_otherrelative) +
            wstring_boolean("cecaq3_4a_option_friend",
                            self.s4a_adultconfidant_familyfriend) +
            wstring_boolean("cecaq3_4a_option_responsibleadult",
                            self.s4a_adultconfidant_responsibleadult) +
            wstring_boolean("cecaq3_4a_option_other",
                            self.s4a_adultconfidant_other) +
            string_string("(Other, details)",
                          self.s4a_adultconfidant_other_detail) +
            wstring_string("cecaq3_4_note_anything",
                           self.s4a_adultconfidant_additional) +
            subsubheading_from_string("(Child confidant)") +
            wstring_boolean("cecaq3_4b_q", self.s4b_childconfidant) +
            subsubheading_from_wstring("cecaq3_4_if_so_who") +
            wstring_boolean("cecaq3_4b_option_sister",
                            self.s4b_childconfidant_sister) +
            wstring_boolean("cecaq3_4b_option_brother",
                            self.s4b_childconfidant_brother) +
            wstring_boolean("cecaq3_4b_option_relative",
                            self.s4b_childconfidant_otherrelative) +
            wstring_boolean("cecaq3_4b_option_closefriend",
                            self.s4b_childconfidant_closefriend) +
            wstring_boolean("cecaq3_4b_option_otherfriend",
                            self.s4b_childconfidant_otherfriend) +
            wstring_boolean("cecaq3_4b_option_other",
                            self.s4b_childconfidant_other) +
            string_string("(Other, details)",
                          self.s4b_childconfidant_other_detail) +
            wstring_string("cecaq3_4_note_anything",
                           self.s4b_childconfidant_additional) +
            subsubheading_from_wstring("cecaq3_4c_q") +
            wstring_boolean("cecaq3_4c_option_mother",
                            self.s4c_closest_mother) +
            wstring_boolean("cecaq3_4c_option_father",
                            self.s4c_closest_father) +
            string_boolean("cecaq3_4c_option_sibling",
                           self.s4c_closest_sibling) +
            wstring_boolean("cecaq3_4c_option_relative",
                            self.s4c_closest_otherrelative) +
            wstring_boolean("cecaq3_4c_option_adultfriend",
                            self.s4c_closest_adultfriend) +
            wstring_boolean("cecaq3_4c_option_youngfriend",
                            self.s4c_closest_childfriend) +
            wstring_boolean("cecaq3_4c_option_other", self.s4c_closest_other) +
            string_string("(Other, details)", self.s4c_closest_other_detail) +
            wstring_string("cecaq3_4_note_anything",
                           self.s4c_closest_additional) +

            subheading_from_string("4: " + WSTRING("cecaq3_5_heading")) +
            wstring_boolean("cecaq3_5_mainq", self.s5c_physicalabuse) +
            subsubheading_from_wstring("cecaq3_5_motherfigure") +
            wstring_boolean("cecaq3_5_did_this_person_hurt_you",
                            self.s5c_abused_by_mother) +
            wstring_numeric("cecaq3_5_how_old",
                            self.s5c_mother_abuse_age_began) +
            wstring_boolean("cecaq3_5_hit_more_than_once",
                            self.s5c_mother_hit_more_than_once) +
            wstring_dict("cecaq3_5_how_hit",
                         self.s5c_mother_hit_how, HITTING_MAP) +
            wstring_boolean("cecaq3_5_injured", self.s5c_mother_injured) +
            wstring_boolean("cecaq3_5_outofcontrol",
                            self.s5c_mother_out_of_control) +
            subsubheading_from_wstring("cecaq3_5_fatherfigure") +
            wstring_boolean("cecaq3_5_did_this_person_hurt_you",
                            self.s5c_abused_by_father) +
            wstring_numeric("cecaq3_5_how_old",
                            self.s5c_father_abuse_age_began) +
            wstring_boolean("cecaq3_5_hit_more_than_once",
                            self.s5c_father_hit_more_than_once) +
            wstring_dict("cecaq3_5_how_hit",
                         self.s5c_father_hit_how, HITTING_MAP) +
            wstring_boolean("cecaq3_5_injured", self.s5c_father_injured) +
            wstring_boolean("cecaq3_5_outofcontrol",
                            self.s5c_father_out_of_control) +
            wstring_string("cecaq3_5_can_you_describe_1",
                           self.s5c_parental_abuse_description) +
            subsubheading_from_string("(Other in household)") +
            wstring_boolean("cecaq3_5_anyone_else",
                            self.s5c_abuse_by_nonparent) +
            wstring_string("cecaq3_5_can_you_describe_2",
                           self.s5c_nonparent_abuse_description) +

            subheading_from_string("6: " + WSTRING("cecaq3_6_heading")) +
            wstring_dict("cecaq3_6_any_unwanted",
                         self.s6_any_unwanted_sexual_experience,
                         NO_YES_3WAY_MAP) +
            wstring_dict("cecaq3_6_intercourse",
                         self.s6_unwanted_intercourse, NO_YES_3WAY_MAP) +
            wstring_dict("cecaq3_6_upset_adult_authority",
                         self.s6_upsetting_sexual_adult_authority,
                         NO_YES_3WAY_MAP) +

            subsubheading_from_wstring("cecaq3_6_first_experience") +
            wstring_numeric("cecaq3_6_q1", self.s6_first_age) +
            wstring_boolean("cecaq3_6_q2", self.s6_first_person_known) +
            wstring_boolean("cecaq3_6_q3", self.s6_first_relative) +
            wstring_boolean("cecaq3_6_q4", self.s6_first_in_household) +
            wstring_boolean("cecaq3_6_q5", self.s6_first_more_than_once) +
            wstring_boolean("cecaq3_6_q6",
                            self.s6_first_touch_privates_subject) +
            wstring_boolean("cecaq3_6_q7",
                            self.s6_first_touch_privates_other) +
            wstring_boolean("cecaq3_6_q8", self.s6_first_intercourse) +

            subsubheading_from_wstring("cecaq3_6_other_experience") +
            wstring_numeric("cecaq3_6_q1", self.s6_other_age) +
            wstring_boolean("cecaq3_6_q2", self.s6_other_person_known) +
            wstring_boolean("cecaq3_6_q3", self.s6_other_relative) +
            wstring_boolean("cecaq3_6_q4", self.s6_other_in_household) +
            wstring_boolean("cecaq3_6_q5", self.s6_other_more_than_once) +
            wstring_boolean("cecaq3_6_q6",
                            self.s6_other_touch_privates_subject) +
            wstring_boolean("cecaq3_6_q7",
                            self.s6_other_touch_privates_other) +
            wstring_boolean("cecaq3_6_q8", self.s6_other_intercourse) +
            wstring_string("cecaq3_5_can_you_describe_1",
                           self.s6_unwanted_sexual_description) +

            subheading_from_wstring("cecaq3_any_other_comments") +
            wstring_string("cecaq3_any_other_comments",
                           self.any_other_comments) +

            """
                </table>
                <div class="footnotes">
                    [1] Death of mother/father before age 17 or continuous
                        separation of ≥1 year.
                    [2] Reason for loss ‘abandonment’ or ‘other’.
                    [3] Section 2A and 3A contain antipathy and neglect scales.
                        Antipathy scales: reverse items 8, 11;
                        then sum 1, 4, 6, 8–11, 16.
                        Neglect scales: reverse items 2, 3, 5, 12–14;
                        then sum 2, 3, 5, 7, 12–15.
                    [4] Psychological abuse scores (sections 2B, 3B):
                        sum of items 1–17 (yes=2, unsure=1, no=0) with
                        frequencies (never=0, once=1, rarely=2, often=3).
                        Any score &gt;1 is a risk indicator.
                    [5] Role reversal: sum of scores from section 3C.
                    [6] Physical abuse (section 4): first question (screen
                        item) is scored 0/1. For each parent, score 1 for
                        {&gt;1 occasion, {belt/stick/punch/kick}, injured,
                        out-of-control}.
                    [7] Sexual abuse (section 6): no=0, unsure=1, yes=1.
                    First three questions are the screen.
                </div>
            """
        )
        return html


# =============================================================================
# Helper functions
# =============================================================================

def subheading_from_string(s):
    return subheading_spanning_two_columns(s)


def subheading_from_wstring(ws):
    return subheading_from_string(WSTRING(ws))


def subsubheading_from_string(s):
    return """<tr><td></td><td class="subheading">{}</td></tr>""".format(s)


def subsubheading_from_wstring(ws):
    return subsubheading_from_string(WSTRING(ws))


def row(label, value, default=""):
    return tr_qa(label, value, default=default)


def string_boolean(string, value):
    return row(string, get_yes_no_none(value))


def string_numeric(string, value):
    return row(string, value)


def string_string(string, value):
    return row(string, ws.webify(value))


def string_dict(string, value, d):
    return row(string, get_from_dict(d, value))


def wstring_boolean(wstring, value):
    return string_boolean(WSTRING(wstring), value)


def wstring_numeric(wstring, value):
    return string_numeric(WSTRING(wstring), value)


def wstring_string(wstring, value):
    return string_string(WSTRING(wstring), value)


def wstring_dict(wstring, value, d):
    return string_dict(WSTRING(wstring), value, d)
