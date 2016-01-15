// Deakin_1_HealthReview.js

/*
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
*/

/*jslint node: true, newcap: true, nomen: true, plusplus: true, unparam: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    // TABLE
    tablename = "deakin_1_healthreview",
    fieldlist = dbcommon.standardTaskFields(),
    // TASK
    N_ETHNICITY_OPTIONS = 16,
    STR_DETAILS_IF_YES = "If you answered YES, please give details:",
    STR_DETAILS = "Details:",
    TICK_ANY_THAT_APPLY = "Tick any that apply:",
    DRUGLIST = [ // order is important
        "tobacco",
        "cannabis",
        "alcohol",
        "Ecstasy (MDMA)",
        "cocaine",
        "crack cocaine",
        "amphetamines",
        "heroin",
        "methadone (heroin substitute)",
        "benzodiazepines",
        "ketamine",
        "legal highs (e.g. Salvia)",
        "inhalants",
        "hallucinogens"
    ],
    INFECTIONLIST = [ // order is important
        "respiratory infection",
        "gastroenteritis",
        "urinary tract infection",
        "sexually transmitted infection",
        "hepatitis",
        "other"
    ],
    PT_ETHNICITY = "eth",
    PT_ALLERGY = "all",
    PT_VACCINES = "vac",
    PT_ACUTE_INFECTIONS = "acinf",
    PT_CHRONIC_INFECTIONS = "chinf",
    PT_IMMUNE = "imm",
    PT_FH = "fh",
    PT_HEALTH_OTHER = "ho",
    PT_RECDRUGS = "recdrug",
    PT_MRI = "mri",
    ET_ETHNICITY_OTHER = "eth_other",
    ET_ALLERGY = "all",
    ET_VACCINES = "vacc",
    ET_ACUTE_INFECTIONS = "acinf",
    ET_CHRONIC_INFECTIONS = "chinf",
    ET_IMMUNE = "imm",
    ET_FH = "fh",
    ET_HEALTH_OTHER = "ho",
    ET_RECDRUGS = "recdrug",
    ET_PREVSCAN = "prevscan",
    ET_OTHERDETAILS = "otherdetails";

fieldlist.push(
    {name: 'ethnicity', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'ethnicity_text', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'ethnicity_other_details', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'handedness', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'education', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'allergies', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'allergy_asthma', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'allergy_pollen_dust', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'allergy_dermatitis', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'allergy_food', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'allergy_dander', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'allergy_other', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'allergy_details', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'vaccinations_last3months', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'vaccination_details', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'infections_last3months', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'infection_recent_respiratory', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'infection_recent_gastroenteritis', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'infection_recent_urinary', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'infection_recent_sexual', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'infection_recent_hepatitis', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'infection_recent_other', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'infection_recent_details', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'infections_chronic', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'infection_chronic_respiratory', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'infection_chronic_gastroenteritis', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'infection_chronic_urinary', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'infection_chronic_sexual', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'infection_chronic_hepatitis', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'infection_chronic_other', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'infection_chronic_details', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'immune_disorders', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'immunity_ms', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'immunity_sle', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'immunity_arthritis', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'immunity_hiv', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'immunity_graves', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'immunity_diabetes', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'immunity_other', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'immunity_details', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'family_history', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'familyhistory_ms', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'familyhistory_sle', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'familyhistory_arthritis', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'familyhistory_graves', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'familyhistory_diabetes', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'familyhistory_psychosis_sz', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'familyhistory_bipolar', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'familyhistory_details', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'health_anything_else', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'health_anything_else_details', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'drug_history', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'first_antipsychotic_medication', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'recreational_drug_in_last_3_months', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_tobacco_frequency', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_tobacco_cigsperweek', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_tobacco_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_cannabis_frequency', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_cannabis_jointsperweek', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_cannabis_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_alcohol_frequency', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_alcohol_unitsperweek', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_alcohol_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_mdma_frequency', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_mdma_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_cocaine_frequency', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_cocaine_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_crack_frequency', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_crack_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_heroin_frequency', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_heroin_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_methadone_frequency', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_methadone_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_amphetamines_frequency', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_amphetamines_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_benzodiazepines_frequency', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_benzodiazepines_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_ketamine_frequency', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_ketamine_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_legalhighs_frequency', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_legalhighs_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_inhalants_frequency', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_inhalants_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_hallucinogens_frequency', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'recdrug_hallucinogens_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_details', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'recdrug_prevheavy', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'recdrug_prevheavy_details', type: DBCONSTANTS.TYPE_TEXT},

    {name: 'mri_claustrophobic', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'mri_difficulty_lying_1_hour', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'mri_nonremovable_metal', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'mri_metal_from_operations', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'mri_tattoos_nicotine_patches', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'mri_worked_with_metal', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'mri_previous_brain_scan', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'mri_previous_brain_scan_details', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'other_relevant_things', type: DBCONSTANTS.TYPE_BOOLEAN},
    {name: 'other_relevant_things_details', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'willing_to_participate_in_further_studies', type: DBCONSTANTS.TYPE_BOOLEAN}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function Deakin_1_HealthReview(patient_id) {
    taskcommon.BaseTask.call(this, patient_id); // call base constructor
}

lang.inheritPrototype(Deakin_1_HealthReview, taskcommon.BaseTask);
lang.extendPrototype(Deakin_1_HealthReview, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: Deakin_1_HealthReview,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    // OTHER

    // Standard task functions
    isComplete: function () {
        return taskcommon.isComplete(this, [
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
        ]);
    },

    getSummary: function () {
        return L('no_summary_see_facsimile') + this.isCompleteSuffix();
    },

    getDetail: function () {
        return this.getSummary();
    },

    edit: function (readOnly) {
        var self = this,
            KeyValuePair = require('lib/KeyValuePair'),
            Questionnaire = require('questionnaire/Questionnaire'),
            UICONSTANTS = require('common/UICONSTANTS'),
            lang = require('lib/lang'),
            yes_no_options = taskcommon.OPTIONS_YES_NO_BOOLEAN,
            ethnicityoptions = [],
            pages,
            questionnaire,
            i;

        for (i = 1; i <= N_ETHNICITY_OPTIONS; ++i) {
            ethnicityoptions.push(
                new KeyValuePair(L("gmcpq_ethnicity_option" + i), i)
            );
        }

        pages = [
            {
                pageTag: PT_ETHNICITY,
                title: "Ethnicity",
                elements: [
                    {
                        type: "QuestionText",
                        text: "Please enter your ethnicity:",
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        field: "ethnicity",
                        options: ethnicityoptions
                    },
                    {
                        elementTag: ET_ETHNICITY_OTHER,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "ethnicity_other_details",
                                prompt: L("gmcpq_ethnicity_other_s")
                            }
                        ]
                    }
                ]
            },
            {
                title: "Handedness",
                elements: [
                    {
                        type: "QuestionText",
                        text: "I prefer to use my:",
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        horizontal: true,
                        showInstruction: false,
                        field: "handedness",
                        options: [
                            new KeyValuePair("Left hand", "L"),
                            new KeyValuePair("Right hand", "R")
                        ]
                    }
                ]
            },
            {
                title: "Education",
                elements: [
                    {
                        type: "QuestionText",
                        text: "Please enter your highest level of education, or nearest equivalent:",
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        field: "education",
                        options: [
                            new KeyValuePair("None", "none"),
                            new KeyValuePair("CSE", "cse"),
                            new KeyValuePair("GCSE", "gcse"),
                            new KeyValuePair("O Level", "olevel"),
                            new KeyValuePair("A Level", "alevel"),
                            new KeyValuePair("Vocational qualification, NVQ — full time", "nvq_fulltime"),
                            new KeyValuePair("Vocational qualification, NVQ — part time", "nvq_parttime"),
                            new KeyValuePair("Degree qualification — diploma", "degree_diploma"),
                            new KeyValuePair("Degree qualification — bachelor’s", "degree_bachelor"),
                            new KeyValuePair("Degree qualification — other", "degree_other"),
                            new KeyValuePair("Postgraduate qualification — master’s", "postgrad_masters"),
                            new KeyValuePair("Postgraduate qualification — PhD", "postgrad_phd")
                        ]
                    }
                ]
            },
            {
                pageTag: PT_ALLERGY,
                title: "Allergies",
                elements: [
                    {
                        type: "QuestionText",
                        text: "Do you have any allergies?",
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        horizontal: true,
                        showInstruction: false,
                        field: "allergies",
                        options: yes_no_options
                    },
                    {
                        type: "QuestionText",
                        text: STR_DETAILS_IF_YES,
                        bold: true
                    },
                    {
                        elementTag: ET_ALLERGY,
                        type: "QuestionMultipleResponse",
                        mandatory: false,
                        min_answers: 1,
                        instruction: TICK_ANY_THAT_APPLY,
                        options: [
                            "asthma",
                            "pollen/dust",
                            "dermatitis",
                            "food allergy",
                            "animal dander",
                            "other"
                        ],
                        fields: [
                            'allergy_asthma',
                            'allergy_pollen_dust',
                            'allergy_dermatitis',
                            'allergy_food',
                            'allergy_dander',
                            'allergy_other'
                        ]
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "allergy_details",
                                prompt: STR_DETAILS
                            }
                        ]
                    }
                ]
            },
            {
                pageTag: PT_VACCINES,
                title: "Recent vaccinations",
                elements: [
                    {
                        type: "QuestionText",
                        text: "Have you had any vaccinations or inoculations in the last 3 months?",
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        horizontal: true,
                        showInstruction: false,
                        field: "vaccinations_last3months",
                        options: yes_no_options
                    },
                    {
                        type: "QuestionText",
                        text: STR_DETAILS_IF_YES,
                        bold: true
                    },
                    {
                        elementTag: ET_VACCINES,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "vaccination_details"
                            }
                        ]
                    }
                ]
            },
            {
                pageTag: PT_ACUTE_INFECTIONS,
                title: "Recent infections",
                elements: [
                    {
                        type: "QuestionText",
                        text: "Have you had any infectious diseases in the last 3 months?",
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        horizontal: true,
                        showInstruction: false,
                        field: "infections_last3months",
                        options: yes_no_options
                    },
                    {
                        type: "QuestionText",
                        text: STR_DETAILS_IF_YES,
                        bold: true
                    },
                    {
                        elementTag: ET_ACUTE_INFECTIONS,
                        type: "QuestionMultipleResponse",
                        mandatory: false,
                        min_answers: 1,
                        instruction: TICK_ANY_THAT_APPLY,
                        options: INFECTIONLIST,
                        fields: [
                            'infection_recent_respiratory',
                            'infection_recent_gastroenteritis',
                            'infection_recent_urinary',
                            'infection_recent_sexual',
                            'infection_recent_hepatitis',
                            'infection_recent_other'
                        ]
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "infection_recent_details",
                                prompt: STR_DETAILS
                            }
                        ]
                    }
                ]
            },
            {
                pageTag: PT_CHRONIC_INFECTIONS,
                title: "Chronic infections",
                elements: [
                    {
                        type: "QuestionText",
                        text: "Are you currently experiencing or have you ever experienced any chronic infections?",
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        horizontal: true,
                        showInstruction: false,
                        field: "infections_chronic",
                        options: yes_no_options
                    },
                    {
                        type: "QuestionText",
                        text: STR_DETAILS_IF_YES,
                        bold: true
                    },
                    {
                        elementTag: ET_CHRONIC_INFECTIONS,
                        type: "QuestionMultipleResponse",
                        mandatory: false,
                        min_answers: 1,
                        instruction: TICK_ANY_THAT_APPLY,
                        options: INFECTIONLIST,
                        fields: [
                            'infection_chronic_respiratory',
                            'infection_chronic_gastroenteritis',
                            'infection_chronic_urinary',
                            'infection_chronic_sexual',
                            'infection_chronic_hepatitis',
                            'infection_chronic_other'
                        ]
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "infection_chronic_details",
                                prompt: STR_DETAILS
                            }
                        ]
                    }
                ]
            },
            {
                pageTag: PT_IMMUNE,
                title: "Immune disorders",
                elements: [
                    {
                        type: "QuestionText",
                        text: "Do you have any immune disorders?",
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        horizontal: true,
                        showInstruction: false,
                        field: "immune_disorders",
                        options: yes_no_options
                    },
                    {
                        type: "QuestionText",
                        text: STR_DETAILS_IF_YES,
                        bold: true
                    },
                    {
                        elementTag: ET_IMMUNE,
                        type: "QuestionMultipleResponse",
                        min_answers: 1,
                        mandatory: false,
                        instruction: TICK_ANY_THAT_APPLY,
                        options: [
                            "multiple sclerosis",
                            "lupus",
                            "arthritis",
                            "HIV/AIDS",
                            "Graves’ disease",
                            "diabetes",
                            "other"
                        ],
                        fields: [
                            'immunity_ms',
                            'immunity_sle',
                            'immunity_arthritis',
                            'immunity_hiv',
                            'immunity_graves',
                            'immunity_diabetes',
                            'immunity_other'
                        ]
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "immunity_details",
                                prompt: STR_DETAILS
                            }
                        ]
                    }
                ]
            },
            {
                pageTag: PT_FH,
                title: "Family history",
                elements: [
                    {
                        type: "QuestionText",
                        text: "Does anyone in your family have any of the disorders listed below?",
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        horizontal: true,
                        showInstruction: false,
                        field: "family_history",
                        options: yes_no_options
                    },
                    {
                        type: "QuestionText",
                        text: STR_DETAILS_IF_YES,
                        bold: true
                    },
                    {
                        elementTag: ET_FH,
                        type: "QuestionMultipleResponse",
                        mandatory: false,
                        min_answers: 1,
                        instruction: TICK_ANY_THAT_APPLY,
                        options: [
                            "multiple sclerosis",
                            "lupus",
                            "arthritis",
                            "Graves’ disease",
                            "psychosis/schizophrenia",
                            "mania/bipolar affective disorder"
                        ],
                        fields: [
                            'familyhistory_ms',
                            'familyhistory_sle',
                            'familyhistory_arthritis',
                            'familyhistory_graves',
                            'familyhistory_psychosis_sz',
                            'familyhistory_bipolar'
                        ]
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "familyhistory_details",
                                prompt: STR_DETAILS
                            }
                        ]
                    }
                ]
            },
            {
                pageTag: PT_HEALTH_OTHER,
                title: "Other aspects of health",
                elements: [
                    {
                        type: "QuestionText",
                        text: "Is there any other information about your general health that we should know?",
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        horizontal: true,
                        showInstruction: false,
                        field: "health_anything_else",
                        options: yes_no_options
                    },
                    {
                        type: "QuestionText",
                        text: STR_DETAILS_IF_YES,
                        bold: true
                    },
                    {
                        elementTag: ET_HEALTH_OTHER,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "health_anything_else_details"
                            }
                        ]
                    }
                ]
            },
            {
                title: "Medication",
                elements: [
                    {
                        type: "QuestionText",
                        text: "If you are taking prescribed medication please list below:",
                        bold: true
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "drug_history"
                            }
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: "If you are taking antipsychotic medication, when did you first take a medication of this kind?",
                        bold: true
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "first_antipsychotic_medication"
                            }
                        ]
                    }
                ]
            },
            {
                pageTag: PT_RECDRUGS,
                title: "Recreational drug use",
                elements: [
                    {
                        type: "QuestionText",
                        text: "Please answer the following questions about any history you may have with drug taking. It is very important that you are honest, because this history may affect your blood sample. Previous drug taking will not necessarily exclude you, and all information will be kept completely confidential.",
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: "Have you taken any recreational drugs in the last 3 months? (Recreational drugs include drugs used only occasionally without being dependent on them.)",
                        bold: true
                    },
                    {
                        type: "QuestionMCQ",
                        horizontal: true,
                        showInstruction: false,
                        field: "recreational_drug_in_last_3_months",
                        options: yes_no_options
                    },
                    {
                        type: "QuestionText",
                        text: "Have you ever had a period of very heavy use of any of the drugs listed below?",
                        bold: true
                    },
                    { type: "QuestionText", text: DRUGLIST.join(", ") },
                    {
                        type: "QuestionMCQ",
                        horizontal: true,
                        showInstruction: false,
                        field: "recdrug_prevheavy",
                        options: yes_no_options
                    },
                    {
                        type: "QuestionText",
                        text: "If you answered YES to either question, please give details (A–E below).",
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: "(A) Please use the grid below to specify which drugs you used in the past 3 months, and how often.",
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: "(B) If you have ever had a period of very heavy use of any of these drugs, please tick its “Previous heavy use?” box.",
                        bold: true
                    },
                    {
                        elementTag: ET_RECDRUGS,
                        type: "QuestionMCQGridWithSingleBoolean",
                        options: [
                            new KeyValuePair("Did not use", 0),
                            new KeyValuePair("Occasionally", 1),
                            new KeyValuePair("Monthly", 2),
                            new KeyValuePair("Weekly", 3),
                            new KeyValuePair("Daily", 4)
                        ],
                        mandatory: false,
                        booleanLabel: "Previous heavy use?",
                        questions: DRUGLIST,
                        mcqFields: [
                            "recdrug_tobacco_frequency",
                            "recdrug_cannabis_frequency",
                            "recdrug_alcohol_frequency",

                            "recdrug_mdma_frequency",
                            "recdrug_cocaine_frequency",
                            "recdrug_crack_frequency",
                            "recdrug_amphetamines_frequency",

                            "recdrug_heroin_frequency",
                            "recdrug_methadone_frequency",
                            "recdrug_benzodiazepines_frequency",

                            "recdrug_ketamine_frequency",
                            "recdrug_legalhighs_frequency",
                            "recdrug_inhalants_frequency",
                            "recdrug_hallucinogens_frequency"
                        ],
                        booleanFields: [
                            "recdrug_tobacco_prevheavy",
                            "recdrug_cannabis_prevheavy",
                            "recdrug_alcohol_prevheavy",

                            "recdrug_mdma_prevheavy",
                            "recdrug_cocaine_prevheavy",
                            "recdrug_crack_prevheavy",
                            "recdrug_amphetamines_prevheavy",

                            "recdrug_heroin_prevheavy",
                            "recdrug_methadone_prevheavy",
                            "recdrug_benzodiazepines_prevheavy",

                            "recdrug_ketamine_prevheavy",
                            "recdrug_legalhighs_prevheavy",
                            "recdrug_inhalants_prevheavy",
                            "recdrug_hallucinogens_prevheavy"
                        ],
                        subtitles: [
                            {beforeIndex: 3, subtitle: " " }, // invisible subtitles repeat the options bar
                            {beforeIndex: 7, subtitle: " " }, // invisible subtitles repeat the options bar
                            {beforeIndex: 10, subtitle: " " }  // invisible subtitles repeat the options bar
                        ],
                        radioColWidth: '12%',
                        boolColWidth: '12%'
                    },
                    {
                        type: "QuestionText",
                        text: "(C) Please give any further details of your recreational drug use in the previous 3 months:",
                        bold: true
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "recdrug_details"
                            }
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: "(D) If you have used tobacco, cannabis, or alcohol in the last 3 months, please give the quantities:",
                        bold: true
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "recdrug_tobacco_cigsperweek",
                                prompt: "Tobacco – cigarettes per week:"
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "recdrug_cannabis_jointsperweek",
                                prompt: "Cannabis – joints per week:"
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "recdrug_alcohol_unitsperweek",
                                prompt: "Alcohol – units per week:"
                            }
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: "(E) If you have had a period of very heavy drug use, please give details about when this was and how long you used the drug heavily:",
                        bold: true
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "recdrug_prevheavy_details"
                            }
                        ]
                    }
                ]
            },
            {
                pageTag: PT_MRI,
                title: "Questions related to MRI scanning",
                elements: [
                    {
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        mandatory: true,
                        options: yes_no_options,
                        questions: [
                            "Are you claustrophobic, or have difficulties in small spaces (e.g. lifts, confined spaces)?",
                            "Would you have any difficulties with lying down for 1 hour (e.g. problems with your back, neck, bladder, etc.)?",
                            "Is there any metal in your body which is not removable (e.g. piercings, splinters, etc.)?",
                            "Have you ever had any operations where metal has been left in your body?",
                            "Do you have any tattoos or nicotine patches?",
                            "Have you ever worked with metal (e.g. as a machinist, metalworker, etc.)?",
                            "Have you ever had any form of brain scan before? If so, please give details below.",
                            "Are there any points you feel may be relevant to your participation in the study? If so, please give details below."
                        ],
                        fields: [
                            'mri_claustrophobic',
                            'mri_difficulty_lying_1_hour',
                            'mri_nonremovable_metal',
                            'mri_metal_from_operations',
                            'mri_tattoos_nicotine_patches',
                            'mri_worked_with_metal',
                            'mri_previous_brain_scan',
                            'other_relevant_things'
                        ]
                    },
                    {
                        elementTag: ET_PREVSCAN,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "mri_previous_brain_scan_details",
                                prompt: "Details of previous brain scans, if applicable:"
                            }
                        ]
                    },
                    {
                        elementTag: ET_OTHERDETAILS,
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        useColumns: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "other_relevant_things_details",
                                prompt: "Any other points you feel may be relevant to your participation, if applicable:"
                            }
                        ]
                    },
                    { type: "QuestionText", text: "Finally:" },
                    {
                        type: "QuestionMCQGrid",
                        horizontal: true,
                        mandatory: true,
                        options: yes_no_options,
                        questions: [
                            "Would you be willing to participate in further studies run by our department?"
                        ],
                        fields: [
                            'willing_to_participate_in_further_studies'
                        ]
                    }
                ]
            },
            {
                title: L("finished"),
                elements: [
                    {
                        type: "QuestionText",
                        text: L('thank_you'),
                        bold: true
                    }
                ]
            }
        ];

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: function (fieldname, value) {
                self.defaultSetFieldFn(fieldname, value);
                // There's a tradeoff between integers (often helpful)
                // versus not knowing what the integers mean, so let's save a copy:
                if (fieldname === "ethnicity") {
                    self.defaultSetFieldFn(
                        "ethnicity_text",
                        // conversion.transliterateUtf8toAscii( lang.kvpGetKeyByValue(ethnicityoptions, value) )
                        // better: fix the database/server side so it can handle UTF8! Done.
                        lang.kvpGetKeyByValue(ethnicityoptions, value)
                    );
                }
            },
            fnFinished: function (result, editing_time_s) {
                self.defaultFinishedFn(result, editing_time_s);
                questionnaire = null; // for garbage collection, since we have closures referring to questionnaire
            },
            fnShowNext: function (currentPage, pageTag) {
                switch (pageTag) {
                case PT_ETHNICITY:
                    questionnaire.setMandatoryByTag(
                        ET_ETHNICITY_OTHER,
                        (self.ethnicity === 3 || self.ethnicity === 7 ||
                         self.ethnicity === 11 || self.ethnicity === 14 ||
                         self.ethnicity === 16)
                    );
                    break;
                case PT_ALLERGY:
                    questionnaire.setMandatoryByTag(
                        ET_ALLERGY,
                        self.allergies
                    );
                    break;
                case PT_VACCINES:
                    questionnaire.setMandatoryByTag(
                        ET_VACCINES,
                        self.vaccinations_last3months
                    );
                    break;
                case PT_ACUTE_INFECTIONS:
                    questionnaire.setMandatoryByTag(
                        ET_ACUTE_INFECTIONS,
                        self.infections_last3months
                    );
                    break;
                case PT_CHRONIC_INFECTIONS:
                    questionnaire.setMandatoryByTag(
                        ET_CHRONIC_INFECTIONS,
                        self.infections_chronic
                    );
                    break;
                case PT_IMMUNE:
                    questionnaire.setMandatoryByTag(
                        ET_IMMUNE,
                        self.immune_disorders
                    );
                    break;
                case PT_FH:
                    questionnaire.setMandatoryByTag(
                        ET_FH,
                        self.family_history
                    );
                    break;
                case PT_HEALTH_OTHER:
                    questionnaire.setMandatoryByTag(
                        ET_HEALTH_OTHER,
                        self.health_anything_else
                    );
                    break;
                case PT_RECDRUGS:
                    questionnaire.setMandatoryByTag(
                        ET_RECDRUGS,
                        self.recreational_drug_in_last_3_months ||
                            self.recdrug_prevheavy
                    );
                    break;
                case PT_MRI:
                    questionnaire.setMandatoryByTag(
                        ET_PREVSCAN,
                        self.mri_previous_brain_scan
                    );
                    questionnaire.setMandatoryByTag(
                        ET_OTHERDETAILS,
                        self.other_relevant_things
                    );
                    break;
                }
                return { care: false };
            }
        });
        questionnaire.open();
    }

});

module.exports = Deakin_1_HealthReview;
