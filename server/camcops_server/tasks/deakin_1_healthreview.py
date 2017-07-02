#!/usr/bin/env python
# deakin_1_healthreview.py

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

from typing import List

from ..cc_modules.cc_constants import PV
from ..cc_modules.cc_html import tr_qa
from ..cc_modules.cc_task import Task


# =============================================================================
# Deakin_1_HealthReview
# =============================================================================

FREQUENCY_COMMENT = (
    "Frequency (0 did not use, 1 occasionally, 2 monthly, 3 weekly, 4 daily)"
)


class Deakin1HealthReview(Task):
    tablename = "deakin_1_healthreview"
    shortname = "Deakin_1_HealthReview"
    longname = "Deakin JB – 1 – Health Review"
    fieldspecs = [
        dict(name="ethnicity", cctype="INT", min=1, max=16,
             comment="Ethnicity code, per GMC Patient Questionnaire (1-16)"),
        dict(name="ethnicity_text", cctype="TEXT",
             comment="Ethnicity, description"),
        dict(name="ethnicity_other_details", cctype="TEXT",
             comment="Ethnicity, other, details"),

        dict(name="handedness", cctype="TEXT", pv=["L", "R"],
             comment="Handedness (L, R)"),

        dict(name="education", cctype="TEXT"),

        dict(name="allergies", cctype="BOOL", pv=PV.BIT),
        dict(name="allergy_asthma", cctype="BOOL", pv=PV.BIT),
        dict(name="allergy_pollen_dust", cctype="BOOL", pv=PV.BIT),
        dict(name="allergy_dermatitis", cctype="BOOL", pv=PV.BIT),
        dict(name="allergy_food", cctype="BOOL", pv=PV.BIT),
        dict(name="allergy_dander", cctype="BOOL", pv=PV.BIT),
        dict(name="allergy_other", cctype="BOOL", pv=PV.BIT),
        dict(name="allergy_details", cctype="TEXT"),

        dict(name="vaccinations_last3months", cctype="BOOL", pv=PV.BIT),
        dict(name="vaccination_details", cctype="TEXT"),

        dict(name="infections_last3months", cctype="BOOL", pv=PV.BIT),
        dict(name="infection_recent_respiratory", cctype="BOOL",
             pv=PV.BIT),
        dict(name="infection_recent_gastroenteritis", cctype="BOOL",
             pv=PV.BIT),
        dict(name="infection_recent_urinary", cctype="BOOL", pv=PV.BIT),
        dict(name="infection_recent_sexual", cctype="BOOL", pv=PV.BIT),
        dict(name="infection_recent_hepatitis", cctype="BOOL",
             pv=PV.BIT),
        dict(name="infection_recent_other", cctype="BOOL", pv=PV.BIT),
        dict(name="infection_recent_details", cctype="TEXT"),

        dict(name="infections_chronic", cctype="BOOL", pv=PV.BIT),
        dict(name="infection_chronic_respiratory", cctype="BOOL",
             pv=PV.BIT),
        dict(name="infection_chronic_gastroenteritis", cctype="BOOL",
             pv=PV.BIT),
        dict(name="infection_chronic_urinary", cctype="BOOL",
             pv=PV.BIT),
        dict(name="infection_chronic_sexual", cctype="BOOL", pv=PV.BIT),
        dict(name="infection_chronic_hepatitis", cctype="BOOL",
             pv=PV.BIT),
        dict(name="infection_chronic_other", cctype="BOOL", pv=PV.BIT),
        dict(name="infection_chronic_details", cctype="TEXT"),

        dict(name="immune_disorders", cctype="BOOL", pv=PV.BIT),
        dict(name="immunity_ms", cctype="BOOL", pv=PV.BIT),
        dict(name="immunity_sle", cctype="BOOL", pv=PV.BIT),
        dict(name="immunity_arthritis", cctype="BOOL", pv=PV.BIT),
        dict(name="immunity_hiv", cctype="BOOL", pv=PV.BIT),
        dict(name="immunity_graves", cctype="BOOL", pv=PV.BIT),
        dict(name="immunity_diabetes", cctype="BOOL", pv=PV.BIT),
        dict(name="immunity_other", cctype="BOOL", pv=PV.BIT),
        dict(name="immunity_details", cctype="TEXT"),

        dict(name="family_history", cctype="BOOL", pv=PV.BIT),
        dict(name="familyhistory_ms", cctype="BOOL", pv=PV.BIT),
        dict(name="familyhistory_sle", cctype="BOOL", pv=PV.BIT),
        dict(name="familyhistory_arthritis", cctype="BOOL", pv=PV.BIT),
        dict(name="familyhistory_graves", cctype="BOOL", pv=PV.BIT),
        dict(name="familyhistory_diabetes", cctype="BOOL", pv=PV.BIT),
        dict(name="familyhistory_psychosis_sz", cctype="BOOL",
             pv=PV.BIT),
        dict(name="familyhistory_bipolar", cctype="BOOL", pv=PV.BIT),
        dict(name="familyhistory_details", cctype="TEXT"),

        dict(name="health_anything_else", cctype="BOOL", pv=PV.BIT),
        dict(name="health_anything_else_details", cctype="TEXT"),

        dict(name="drug_history", cctype="TEXT"),
        dict(name="first_antipsychotic_medication", cctype="TEXT"),

        dict(name="recreational_drug_in_last_3_months", cctype="BOOL",
             pv=PV.BIT),
        dict(name="recdrug_tobacco_frequency", cctype="INT",
             min=0, max=4, comment=FREQUENCY_COMMENT),
        dict(name="recdrug_tobacco_cigsperweek", cctype="INT", min=0,
             comment=FREQUENCY_COMMENT),
        dict(name="recdrug_tobacco_prevheavy", cctype="BOOL",
             pv=PV.BIT),
        dict(name="recdrug_cannabis_frequency", cctype="INT",
             min=0, max=4, comment=FREQUENCY_COMMENT),
        dict(name="recdrug_cannabis_jointsperweek", cctype="INT", min=0,
             comment=FREQUENCY_COMMENT),
        dict(name="recdrug_cannabis_prevheavy", cctype="BOOL",
             pv=PV.BIT),
        dict(name="recdrug_alcohol_frequency", cctype="INT",
             min=0, max=4, comment=FREQUENCY_COMMENT),
        dict(name="recdrug_alcohol_unitsperweek", cctype="INT", min=0,
             comment=FREQUENCY_COMMENT),
        dict(name="recdrug_alcohol_prevheavy", cctype="BOOL",
             pv=PV.BIT),
        dict(name="recdrug_mdma_frequency", cctype="INT",
             min=0, max=4, comment=FREQUENCY_COMMENT),
        dict(name="recdrug_mdma_prevheavy", cctype="BOOL", pv=PV.BIT),
        dict(name="recdrug_cocaine_frequency", cctype="INT",
             min=0, max=4, comment=FREQUENCY_COMMENT),
        dict(name="recdrug_cocaine_prevheavy", cctype="BOOL",
             pv=PV.BIT),
        dict(name="recdrug_crack_frequency", cctype="INT",
             min=0, max=4, comment=FREQUENCY_COMMENT),
        dict(name="recdrug_crack_prevheavy", cctype="BOOL", pv=PV.BIT),
        dict(name="recdrug_heroin_frequency", cctype="INT",
             min=0, max=4, comment=FREQUENCY_COMMENT),
        dict(name="recdrug_heroin_prevheavy", cctype="BOOL", pv=PV.BIT),
        dict(name="recdrug_methadone_frequency", cctype="INT",
             min=0, max=4, comment=FREQUENCY_COMMENT),
        dict(name="recdrug_methadone_prevheavy", cctype="BOOL",
             pv=PV.BIT),
        dict(name="recdrug_amphetamines_frequency", cctype="INT",
             min=0, max=4, comment=FREQUENCY_COMMENT),
        dict(name="recdrug_amphetamines_prevheavy", cctype="BOOL",
             pv=PV.BIT),
        dict(name="recdrug_benzodiazepines_frequency", cctype="INT",
             min=0, max=4, comment=FREQUENCY_COMMENT),
        dict(name="recdrug_benzodiazepines_prevheavy", cctype="BOOL",
             pv=PV.BIT),
        dict(name="recdrug_ketamine_frequency", cctype="INT",
             min=0, max=4, comment=FREQUENCY_COMMENT),
        dict(name="recdrug_ketamine_prevheavy", cctype="BOOL",
             pv=PV.BIT),
        dict(name="recdrug_legalhighs_frequency", cctype="INT",
             min=0, max=4, comment=FREQUENCY_COMMENT),
        dict(name="recdrug_legalhighs_prevheavy", cctype="BOOL",
             pv=PV.BIT),
        dict(name="recdrug_inhalants_frequency", cctype="INT",
             min=0, max=4, comment=FREQUENCY_COMMENT),
        dict(name="recdrug_inhalants_prevheavy", cctype="BOOL",
             pv=PV.BIT),
        dict(name="recdrug_hallucinogens_frequency", cctype="INT",
             min=0, max=4, comment=FREQUENCY_COMMENT),
        dict(name="recdrug_hallucinogens_prevheavy", cctype="BOOL",
             pv=PV.BIT),
        dict(name="recdrug_details", cctype="TEXT"),
        dict(name="recdrug_prevheavy", cctype="BOOL", pv=PV.BIT),
        dict(name="recdrug_prevheavy_details", cctype="TEXT"),

        dict(name="mri_claustrophobic", cctype="BOOL", pv=PV.BIT),
        dict(name="mri_difficulty_lying_1_hour", cctype="BOOL",
             pv=PV.BIT),
        dict(name="mri_nonremovable_metal", cctype="BOOL", pv=PV.BIT),
        dict(name="mri_metal_from_operations", cctype="BOOL",
             pv=PV.BIT),
        dict(name="mri_tattoos_nicotine_patches", cctype="BOOL",
             pv=PV.BIT),
        dict(name="mri_worked_with_metal", cctype="BOOL", pv=PV.BIT),
        dict(name="mri_previous_brain_scan", cctype="BOOL", pv=PV.BIT),
        dict(name="mri_previous_brain_scan_details", cctype="TEXT"),
        dict(name="other_relevant_things", cctype="BOOL", pv=PV.BIT),
        dict(name="other_relevant_things_details", cctype="TEXT"),

        dict(name="willing_to_participate_in_further_studies",
             cctype="BOOL", pv=PV.BIT),
    ]
    for d in fieldspecs:
        if "comment" not in d:
            d["comment"] = d["name"]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete([
                "ethnicity",
                "handedness",
                "education",
                "allergies",
                "vaccinations_last3months",
                "infections_last3months",
                "infections_chronic",
                "immune_disorders",
                "health_anything_else",
                "recreational_drug_in_last_3_months",
                "recdrug_prevheavy",
                "mri_claustrophobic",
                "mri_difficulty_lying_1_hour",
                "mri_nonremovable_metal",
                "mri_metal_from_operations",
                "mri_tattoos_nicotine_patches",
                "mri_worked_with_metal",
                "mri_previous_brain_scan",
                "other_relevant_things",
                "willing_to_participate_in_further_studies"
            ]) and
            self.field_contents_valid()
        )

    def get_drug_frequency_row(self, fieldname: str) -> str:
        drug_frequency_dict = {
            0: "Did not use",
            1: "Occasionally",
            2: "Monthly",
            3: "Weekly",
            4: "Daily"
        }
        frequency = drug_frequency_dict.get(getattr(self, fieldname), None)
        return tr_qa(fieldname, frequency)

    def get_task_html(self) -> str:
        return """
            <div class="summary">
                <table class="summary">
                    {}
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """.format(self.get_is_complete_tr()) + (
            self.get_twocol_val_row("ethnicity") +
            self.get_twocol_string_row("ethnicity_text") +
            self.get_twocol_string_row("ethnicity_other_details") +

            self.get_twocol_string_row("handedness") +

            self.get_twocol_string_row("education") +

            self.get_twocol_bool_row("allergies") +
            self.get_twocol_bool_row("allergy_asthma") +
            self.get_twocol_bool_row("allergy_pollen_dust") +
            self.get_twocol_bool_row("allergy_dermatitis") +
            self.get_twocol_bool_row("allergy_food") +
            self.get_twocol_bool_row("allergy_dander") +
            self.get_twocol_bool_row("allergy_other") +
            self.get_twocol_string_row("allergy_details") +

            self.get_twocol_bool_row("vaccinations_last3months") +
            self.get_twocol_string_row("vaccination_details") +

            self.get_twocol_bool_row("infections_last3months") +
            self.get_twocol_bool_row("infection_recent_respiratory") +
            self.get_twocol_bool_row("infection_recent_gastroenteritis") +
            self.get_twocol_bool_row("infection_recent_urinary") +
            self.get_twocol_bool_row("infection_recent_sexual") +
            self.get_twocol_bool_row("infection_recent_hepatitis") +
            self.get_twocol_bool_row("infection_recent_other") +
            self.get_twocol_string_row("infection_recent_details") +

            self.get_twocol_bool_row("infections_chronic") +
            self.get_twocol_bool_row("infection_chronic_respiratory") +
            self.get_twocol_bool_row("infection_chronic_gastroenteritis") +
            self.get_twocol_bool_row("infection_chronic_urinary") +
            self.get_twocol_bool_row("infection_chronic_sexual") +
            self.get_twocol_bool_row("infection_chronic_hepatitis") +
            self.get_twocol_bool_row("infection_chronic_other") +
            self.get_twocol_string_row("infection_chronic_details") +

            self.get_twocol_bool_row("immune_disorders") +
            self.get_twocol_bool_row("immunity_ms") +
            self.get_twocol_bool_row("immunity_sle") +
            self.get_twocol_bool_row("immunity_arthritis") +
            self.get_twocol_bool_row("immunity_hiv") +
            self.get_twocol_bool_row("immunity_graves") +
            self.get_twocol_bool_row("immunity_diabetes") +
            self.get_twocol_bool_row("immunity_other") +
            self.get_twocol_string_row("immunity_details") +

            self.get_twocol_bool_row("family_history") +
            self.get_twocol_bool_row("familyhistory_ms") +
            self.get_twocol_bool_row("familyhistory_sle") +
            self.get_twocol_bool_row("familyhistory_arthritis") +
            self.get_twocol_bool_row("familyhistory_graves") +
            self.get_twocol_bool_row("familyhistory_diabetes") +
            self.get_twocol_bool_row("familyhistory_psychosis_sz") +
            self.get_twocol_bool_row("familyhistory_bipolar") +
            self.get_twocol_string_row("familyhistory_details") +

            self.get_twocol_bool_row("health_anything_else") +
            self.get_twocol_string_row("health_anything_else_details") +

            self.get_twocol_string_row("drug_history") +
            self.get_twocol_string_row("first_antipsychotic_medication") +

            self.get_twocol_bool_row("recreational_drug_in_last_3_months") +
            self.get_drug_frequency_row("recdrug_tobacco_frequency") +
            self.get_twocol_val_row("recdrug_tobacco_cigsperweek") +
            self.get_twocol_bool_row("recdrug_tobacco_prevheavy") +
            self.get_drug_frequency_row("recdrug_cannabis_frequency") +
            self.get_twocol_val_row("recdrug_cannabis_jointsperweek") +
            self.get_twocol_bool_row("recdrug_cannabis_prevheavy") +
            self.get_drug_frequency_row("recdrug_alcohol_frequency") +
            self.get_twocol_val_row("recdrug_alcohol_unitsperweek") +
            self.get_twocol_bool_row("recdrug_alcohol_prevheavy") +
            self.get_drug_frequency_row("recdrug_mdma_frequency") +
            self.get_twocol_bool_row("recdrug_mdma_prevheavy") +
            self.get_drug_frequency_row("recdrug_cocaine_frequency") +
            self.get_twocol_bool_row("recdrug_cocaine_prevheavy") +
            self.get_drug_frequency_row("recdrug_crack_frequency") +
            self.get_twocol_bool_row("recdrug_crack_prevheavy") +
            self.get_drug_frequency_row("recdrug_heroin_frequency") +
            self.get_twocol_bool_row("recdrug_heroin_prevheavy") +
            self.get_drug_frequency_row("recdrug_methadone_frequency") +
            self.get_twocol_bool_row("recdrug_methadone_prevheavy") +
            self.get_drug_frequency_row("recdrug_amphetamines_frequency") +
            self.get_twocol_bool_row("recdrug_amphetamines_prevheavy") +
            self.get_drug_frequency_row("recdrug_benzodiazepines_frequency") +
            self.get_twocol_bool_row("recdrug_benzodiazepines_prevheavy") +
            self.get_drug_frequency_row("recdrug_ketamine_frequency") +
            self.get_twocol_bool_row("recdrug_ketamine_prevheavy") +
            self.get_drug_frequency_row("recdrug_legalhighs_frequency") +
            self.get_twocol_bool_row("recdrug_legalhighs_prevheavy") +
            self.get_drug_frequency_row("recdrug_inhalants_frequency") +
            self.get_twocol_bool_row("recdrug_inhalants_prevheavy") +
            self.get_drug_frequency_row("recdrug_hallucinogens_frequency") +
            self.get_twocol_bool_row("recdrug_hallucinogens_prevheavy") +
            self.get_twocol_string_row("recdrug_details") +
            self.get_twocol_bool_row("recdrug_prevheavy") +
            self.get_twocol_string_row("recdrug_prevheavy_details") +

            self.get_twocol_bool_row("mri_claustrophobic") +
            self.get_twocol_bool_row("mri_difficulty_lying_1_hour") +
            self.get_twocol_bool_row("mri_nonremovable_metal") +
            self.get_twocol_bool_row("mri_metal_from_operations") +
            self.get_twocol_bool_row("mri_tattoos_nicotine_patches") +
            self.get_twocol_bool_row("mri_worked_with_metal") +
            self.get_twocol_bool_row("mri_previous_brain_scan") +
            self.get_twocol_string_row("mri_previous_brain_scan_details") +
            self.get_twocol_bool_row("other_relevant_things") +
            self.get_twocol_string_row("other_relevant_things_details") +
            self.get_twocol_bool_row(
                "willing_to_participate_in_further_studies") +

            "</table>"
        )
