// DemoQuestionnaire.js

/*
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
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

// Template for a task/task record:
//      ... the standard members of a record
//      ... isComplete()
//      ... getPatientID()
//      ... getCreationDateTime()
//      ... getSummary()
//      ... getSummaryView()
//      ... getDetail()
//      ... edit()

/*jslint node: true, newcap: true, nomen: true, plusplus: true */
"use strict";
/*global Titanium, L */

var DBCONSTANTS = require('common/DBCONSTANTS'),
    dbcommon = require('lib/dbcommon'),
    taskcommon = require('lib/taskcommon'),
    lang = require('lib/lang'),
    // DEMO TABLE
    tablename = "demoquestionnaire",
    fieldlist = dbcommon.standardTaskFields(true),
    // TASK
    IMAGE_PENGUIN = '/images/ace3/penguin.png',
    IMAGE_PATH = '/images/moca/path.png',
    IMAGE_ANIMALS = '/images/moca/animals.png',
    THERMOMETER_10_UNSEL = '/images/dt/dt_unsel_10.png',
    THERMOMETER_09_UNSEL = '/images/dt/dt_unsel_9.png',
    THERMOMETER_08_UNSEL = '/images/dt/dt_unsel_8.png',
    THERMOMETER_07_UNSEL = '/images/dt/dt_unsel_7.png',
    THERMOMETER_06_UNSEL = '/images/dt/dt_unsel_6.png',
    THERMOMETER_05_UNSEL = '/images/dt/dt_unsel_5.png',
    THERMOMETER_04_UNSEL = '/images/dt/dt_unsel_4.png',
    THERMOMETER_03_UNSEL = '/images/dt/dt_unsel_3.png',
    THERMOMETER_02_UNSEL = '/images/dt/dt_unsel_2.png',
    THERMOMETER_01_UNSEL = '/images/dt/dt_unsel_1.png',
    THERMOMETER_00_UNSEL = '/images/dt/dt_unsel_0.png',
    THERMOMETER_10_SEL = '/images/dt/dt_sel_10.png',
    THERMOMETER_09_SEL = '/images/dt/dt_sel_9.png',
    THERMOMETER_08_SEL = '/images/dt/dt_sel_8.png',
    THERMOMETER_07_SEL = '/images/dt/dt_sel_7.png',
    THERMOMETER_06_SEL = '/images/dt/dt_sel_6.png',
    THERMOMETER_05_SEL = '/images/dt/dt_sel_5.png',
    THERMOMETER_04_SEL = '/images/dt/dt_sel_4.png',
    THERMOMETER_03_SEL = '/images/dt/dt_sel_3.png',
    THERMOMETER_02_SEL = '/images/dt/dt_sel_2.png',
    THERMOMETER_01_SEL = '/images/dt/dt_sel_1.png',
    THERMOMETER_00_SEL = '/images/dt/dt_sel_0.png';

dbcommon.appendRepeatedFieldDef(fieldlist, "mcq", 1, 8,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "mcqbool", 1, 3,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "multipleresponse", 1, 6,
                                DBCONSTANTS.TYPE_INTEGER);
dbcommon.appendRepeatedFieldDef(fieldlist, "booltext", 1, 22,
                                DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendRepeatedFieldDef(fieldlist, "boolimage", 1, 2,
                                DBCONSTANTS.TYPE_BOOLEAN);
dbcommon.appendRepeatedFieldDef(fieldlist, "slider", 1, 2,
                                DBCONSTANTS.TYPE_REAL);
dbcommon.appendRepeatedFieldDef(fieldlist, "picker", 1, 2,
                                DBCONSTANTS.TYPE_INTEGER);
fieldlist.push(
    {name: 'mcqtext_1a', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'mcqtext_1b', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'mcqtext_2a', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'mcqtext_2b', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'mcqtext_3a', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'mcqtext_3b', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'typedvar_text', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'typedvar_text_multiline', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'typedvar_int', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'typedvar_real', type: DBCONSTANTS.TYPE_REAL},
    {name: 'date_only', type: DBCONSTANTS.TYPE_DATE},
    {name: 'date_time', type: DBCONSTANTS.TYPE_DATETIME},
    {name: 'thermometer', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'diagnosticcode_code', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'diagnosticcode_description', type: DBCONSTANTS.TYPE_TEXT},
    {name: 'photo_blobid', type: DBCONSTANTS.TYPE_BLOBID},
    {name: 'photo_rotation', type: DBCONSTANTS.TYPE_INTEGER},
    {name: 'canvas_blobid', type: DBCONSTANTS.TYPE_BLOBID}
);

// CREATE THE TABLE

dbcommon.createTable(tablename, fieldlist);

// TASK

function DemoQuestionnaire() {
    taskcommon.BaseTask.call(this); // call base constructor (ANONYMOUS TASK)
}

lang.inheritPrototype(DemoQuestionnaire, taskcommon.BaseTask);
lang.extendPrototype(DemoQuestionnaire, {

    // KEY DATABASE FIELDS (USED BY DatabaseObject)

    _objecttype: DemoQuestionnaire,
    _tablename: tablename,
    _fieldlist: fieldlist,

    // TASK CLASS FIELD OVERRIDES (USED BY BaseTask)

    _anonymous: true,

    // OTHER

    // Standard task functions
    isComplete: function () {
        return (this.q1 === null);
    },

    getSummary: function () {
        return "Demo summary... see details";
    },

    getDetail: function () {
        var msg = "",
            i;
        for (i = 0; i < fieldlist.length; ++i) {
            msg += (
                fieldlist[i].name + ": " +
                dbcommon.userString(this, fieldlist[i]) + "\n"
            );
        }
        return msg;
    },

    edit: function (readOnly) {
        var self = this,
            uifunc = require('lib/uifunc'),
            Questionnaire = require('questionnaire/Questionnaire'),
            KeyValuePair = require('lib/KeyValuePair'),
            UICONSTANTS = require('common/UICONSTANTS'),
            pages,
            questionnaire;

        // SEARCH AND REPLACE (Komodo Edit) -- a first approximation, anyway:
        //      \stype: (\w*),
        //      \stype: "\1",
        // And Perl: SKIP, broke a lot of things that way...
        //      IT IS NOT: perl -p -i -e "s/\stype: (\w*),/\stype: "$1",/g" *.js
        //      ... because that has the wrong capture group syntax
        // but then Container types need special work, and HorizontalRule

        pages = [
            {
                title: "Demo questionnaire: first page",
                elements: [
                    {
                        type: "QuestionText",
                        text: "We’ll demonstrate the elements from which questionnaire tasks can be made. Press the ‘Next’ button at the top right of the screen."
                    }
                ]
            },
            {
                title: "Demo questionnaire: EXTRA page with a longer piece of text",
                elements: [
                    {
                        type: "QuestionHeading",
                        text: "This is a heading. Some text follows."
                    },
                    {
                        type: "QuestionText",
                        text: L("qolbasic_tto_q")
                    }
                ]
            },
            {
                title: "Demo: MCQs",
                elements: [
                    {
                        type: "QuestionHeading",
                        text: "A heading. On this page: MCQs."
                    },
                    {
                        type: "QuestionText",
                        text: "On this page, some questions must be completed before the ‘Next’ button appears."
                    },
                    {
                        type: "QuestionText",
                        text: "Make the yellow disappear to continue!",
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: "Double-tap MCQs to clear them."
                    },
                    {
                        type: "QuestionText",
                        text: "An MCQ, one-from-many:"
                    },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair("option with value of 0", 0),
                            new KeyValuePair("option 1", 1),
                            new KeyValuePair("option two", 2),
                            new KeyValuePair("third option", 3)
                        ],
                        field: 'mcq1'
                    },
                    {
                        type: "QuestionText",
                        text: "A horizontal MCQ, without the instruction, with elements shuffled:"
                    },
                    {
                        type: "QuestionMCQ",
                        horizontal: true,
                        showInstruction: false,
                        randomize: true,
                        mandatory: false,
                        options: [
                            new KeyValuePair("0", 0),
                            new KeyValuePair("1", 1),
                            new KeyValuePair("2", 2),
                            new KeyValuePair("3", 3),
                            new KeyValuePair("4", 4),
                            new KeyValuePair("9", 9)
                        ],
                        field: 'mcq2'
                    }
                ]
            },
            {
                title: "Demo: other MCQ styles, MCQ grids, and horizontal rules",
                elements: [
                    {
                        type: "QuestionText",
                        text: "MCQs can look like text buttons, too:"
                    },
                    {
                        type: "QuestionMCQ",
                        options: [
                            new KeyValuePair("option with value of 0", 0),
                            new KeyValuePair("option 1", 1),
                            new KeyValuePair("option two", 2),
                            new KeyValuePair("third option", 3)
                        ],
                        field: 'mcq1',
                        mandatory: true,
                        asTextButton: true
                    },
                    {
                        type: "QuestionMCQ",
                        horizontal: true,
                        asTextButton: true,
                        showInstruction: false,
                        mandatory: false,
                        options: [
                            new KeyValuePair("0", 0),
                            new KeyValuePair("1", 1),
                            new KeyValuePair("2", 2),
                            new KeyValuePair("3", 3),
                            new KeyValuePair("4", 4),
                            new KeyValuePair("9", 9)
                        ],
                        field: 'mcq2'
                    },
                    {
                        type: "QuestionText",
                        text: "An MCQ grid:"
                    },
                    {
                        type: "QuestionMCQGrid",
                        mandatory: false,
                        options: [
                            new KeyValuePair("0", 0),
                            new KeyValuePair("1", 1),
                            new KeyValuePair("2", 2),
                            new KeyValuePair("3", 3)
                        ],
                        questions: [
                            "Question 3",
                            "Question 4",
                            "Question 5"
                        ],
                        fields: [ 'mcq3', 'mcq4', 'mcq5' ]
                    },
                    { type: "QuestionHorizontalRule" },
                    {
                        type: "QuestionText",
                        text: "MCQ grid with single boolean:"
                    },
                    {
                        type: "QuestionMCQGridWithSingleBoolean",
                        options: [
                            new KeyValuePair("absent", 0),
                            new KeyValuePair("mild", 1),
                            new KeyValuePair("moderate", 2),
                            new KeyValuePair("severe", 3)
                        ],
                        mandatory: false,
                        booleanLabel: "Tick if distressing",
                        questions: [
                            "Symptom A",
                            "Symptom B",
                            "Symptom C"
                        ],
                        mcqFields: [ 'mcq6', 'mcq7', 'mcq8' ],
                        booleanFields: [ 'mcqbool1', 'mcqbool2', 'mcqbool3' ],
                        boolColWidth: '20%',
                        subtitles: [
                            {beforeIndex: 1, subtitle: "A subtitle" }
                        ]
                    },
                    { type: "QuestionHorizontalRule" },
                    {
                        type: "QuestionText",
                        text: "Double MCQ grid"
                    },
                    {
                        type: "QuestionMCQGridDouble",
                        mandatory: false,
                        questions: [ "Q1", "Q2", "Q3" ],
                        fields_1: [
                            'mcqtext_1a',
                            'mcqtext_2a',
                            'mcqtext_3a'
                        ],
                        fields_2: [
                            'mcqtext_1b',
                            'mcqtext_2b',
                            'mcqtext_3b'
                        ],
                        options_1: [
                            new KeyValuePair("A", "A"),
                            new KeyValuePair("B", "B"),
                            new KeyValuePair("C", "C"),
                            new KeyValuePair("D", "D")
                        ],
                        options_2: [
                            new KeyValuePair("X", "X"),
                            new KeyValuePair("Y", "Y"),
                            new KeyValuePair("Z", "Z")
                        ]
                    }
                ]
            },
            {
                title: "Demo: pickers",
                elements: [
                    {
                        type: "QuestionText",
                        text: "Inline picker (which will autodefault to the first option, unless the task specifies a default; NULL is not well handled):"
                    },
                    {
                        type: "QuestionPickerInline",
                        mandatory: true,
                        field: "picker1",
                        options: [
                            new KeyValuePair("absent", 0),
                            new KeyValuePair("mild", 1),
                            new KeyValuePair("moderate", 2),
                            new KeyValuePair("severe", 3)
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: "Popup picker (which will cope with NULL starting values):"
                    },
                    {
                        type: "QuestionPickerPopup",
                        mandatory: true,
                        field: "picker2",
                        options: [
                            new KeyValuePair("absent", 0),
                            new KeyValuePair("mild", 1),
                            new KeyValuePair("moderate", 2),
                            new KeyValuePair("severe", 3)
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: "The yellow question mark indicates that input is required.",
                        bold: true
                    }
                ]
            },
            {
                title: "Demo: n-from-many",
                elements: [
                    {
                        type: "QuestionText",
                        text: "n-from-many question:"
                    },
                    {
                        type: "QuestionMultipleResponse",
                        // asTextButton: true,
                        mandatory: true,
                        min_answers: 2,
                        max_answers: 3,
                        options: [
                            "subquestion 1",
                            "subquestion 2",
                            "subquestion 3",
                            "subquestion 4",
                            "subquestion 5",
                            "subquestion 6"
                        ],
                        fields: [
                            'multipleresponse1',
                            'multipleresponse2',
                            'multipleresponse3',
                            'multipleresponse4',
                            'multipleresponse5',
                            'multipleresponse6'
                        ]
                    }
                ]
            },
            {
                title: "Demo: Images, layout, yes/no fields",
                elements: [
                    {
                        type: "QuestionHeading",
                        text: "A plain image"
                    },
                    {
                        type: "QuestionImage",
                        image: IMAGE_ANIMALS
                    },
                    {
                        type: "QuestionHeading",
                        text: "A boolean image: touch image or box to toggle yes/no"
                    },
                    {
                        type: "QuestionBooleanImage",
                        field: "boolimage1",
                        allowUnsetting: true,
                        image: IMAGE_PENGUIN
                    },
                    {
                        type: "QuestionHeading",
                        text: "Horizontal, vertical, and table layouts (in which other elements can be placed)"
                    },
                    {
                        type: "QuestionText",
                        text: "The fields are boolean text fields. Touch the text or the box. Some different styles are shown."
                    },
                    {
                        type: "QuestionText",
                        text: "For some, you can double-click to unset the field."
                    },
                    {
                        type: "ContainerTable",
                        elements: [
                            {
                                type: "ContainerVertical",
                                elements: [
                                    {
                                        type: "QuestionText",
                                        text: L("ace3_trial") + " 1"
                                    },
                                    {
                                        type: "ContainerHorizontal",
                                        elements: [
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_1"),
                                                field: "booltext1",
                                                mandatory: false
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_2"),
                                                field: "booltext2",
                                                mandatory: false
                                            }
                                        ]
                                    },
                                    {
                                        type: "ContainerHorizontal",
                                        elements: [
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_3"),
                                                field: "booltext3",
                                                mandatory: false
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_4"),
                                                field: "booltext4",
                                                mandatory: false
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_5"),
                                                field: "booltext5",
                                                mandatory: false
                                            }
                                        ]
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        text: L("ace3_address_6"),
                                        field: "booltext6",
                                        mandatory: false
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        text: L("ace3_address_7"),
                                        field: "booltext7",
                                        mandatory: false
                                    }
                                ]
                            },
                            {
                                type: "ContainerVertical",
                                elements: [
                                    {
                                        type: "QuestionText",
                                        text: L("ace3_trial") + " 2"
                                    },
                                    {
                                        type: "ContainerHorizontal",
                                        elements: [
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_1"),
                                                field: "booltext8",
                                                asTextButton: true,
                                                mandatory: false
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_2"),
                                                field: "booltext9",
                                                asTextButton: true,
                                                mandatory: false
                                            }
                                        ]
                                    },
                                    {
                                        type: "ContainerHorizontal",
                                        elements: [
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_3"),
                                                field: "booltext10",
                                                asTextButton: true,
                                                mandatory: false
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_4"),
                                                field: "booltext11",
                                                asTextButton: true,
                                                mandatory: false
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_5"),
                                                field: "booltext12",
                                                asTextButton: true,
                                                mandatory: false
                                            }
                                        ]
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        text: L("ace3_address_6"),
                                        field: "booltext13",
                                        asTextButton: true,
                                        mandatory: false
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        text: L("ace3_address_7"),
                                        field: "booltext14",
                                        asTextButton: true,
                                        mandatory: false
                                    }
                                ]
                            },
                            {
                                type: "ContainerVertical",
                                elements: [
                                    {
                                        type: "QuestionText",
                                        text: L("ace3_trial") + " 3"
                                    },
                                    {
                                        type: "ContainerHorizontal",
                                        elements: [
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_1"),
                                                field: "booltext15",
                                                asTextButton: true,
                                                allowUnsetting: true,
                                                mandatory: true
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_2"),
                                                field: "booltext16",
                                                asTextButton: true,
                                                allowUnsetting: true,
                                                mandatory: true
                                            }
                                        ]
                                    },
                                    {
                                        type: "ContainerHorizontal",
                                        elements: [
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_3"),
                                                field: "booltext17",
                                                asTextButton: true,
                                                allowUnsetting: true,
                                                mandatory: true
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_4"),
                                                field: "booltext18",
                                                asTextButton: true,
                                                allowUnsetting: true,
                                                mandatory: true
                                            },
                                            {
                                                type: "QuestionBooleanText",
                                                text: L("ace3_address_5"),
                                                field: "booltext19",
                                                asTextButton: true,
                                                allowUnsetting: true,
                                                mandatory: true
                                            }
                                        ]
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        text: L("ace3_address_6"),
                                        field: "booltext20",
                                        asTextButton: true,
                                        allowUnsetting: true,
                                        mandatory: true
                                    },
                                    {
                                        type: "QuestionBooleanText",
                                        text: L("ace3_address_7"),
                                        field: "booltext21",
                                        asTextButton: true,
                                        allowUnsetting: true,
                                        mandatory: true
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: "More options for boolean text and image fields:"
                    },
                    {
                        type: "QuestionBooleanText",
                        text: L("ace3_address_1"),
                        field: "booltext22",
                        mandatory: false,
                        indicatorOnLeft: true,
                        big: true,
                        bigTick: true,
                        valign: UICONSTANTS.ALIGN_CENTRE
                    },
                    {
                        type: "QuestionBooleanImage",
                        field: "boolimage2",
                        image: IMAGE_PENGUIN,
                        mandatory: false,
                        indicatorOnLeft: true,
                        bigTick: true,
                        valign: UICONSTANTS.ALIGN_CENTRE
                    }
                ]
            },
            {
                title: "Demo: photo",
                elements: [
                    {
                        type: "QuestionHeading",
                        text: "Photo"
                    },
                    {
                        type: "QuestionPhoto",
                        field: "photo_blobid",
                        mandatory: false,
                        rotationField: "photo_rotation"
                    }
                ]
            },
            {
                title: "Demo: Typed variables",
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: "Pages for clinicians have a different background colour.",
                        bold: true
                    },
                    {
                        type: "QuestionHeading",
                        text: "Typed variables"
                    },
                    {
                        type: "QuestionTypedVariables",
                        mandatory: false,
                        variables: [
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT,
                                field: "typedvar_text",
                                prompt: "Text",
                                mandatory: true
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_TEXT_MULTILINE,
                                field: "typedvar_text_multiline",
                                prompt: "Text (multiline)"
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_INTEGER,
                                field: "typedvar_int",
                                prompt: "Integer (constrained to range 0-100)",
                                min: 0,
                                max: 100
                            },
                            {
                                type: UICONSTANTS.TYPEDVAR_REAL,
                                field: "typedvar_real",
                                prompt: "Real (floating-point) number"
                            }
                        ]
                    }
                ]
            },
            {
                title: "Demo: date/time",
                clinician: true,
                elements: [
                    {
                        type: "QuestionHeading",
                        text: "Dates and times"
                    },
                    {
                        type: "QuestionText",
                        text: (
                            "The clock/timeline button sets the fields to " +
                            "NOW. The erasure button wipes the value of the " +
                            "field."
                        ),
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: (
                            "Since the spinner and calendar widgets are " +
                            "often a bit slow to use, text entry is offered " +
                            "by default as well."
                        )
                    },
                    {
                        type: "QuestionText",
                        text: "Date only:"
                    },
                    {
                        type: "QuestionDateTime",
                        field: "date_only",
                        showTime: false,
                        offerNowButton: true,
                        offerNullButton: true,
                        textInput: true,
                        useWidgets: true
                    },
                    {
                        type: "QuestionText",
                        text: "Date and time:"
                    },
                    {
                        type: "QuestionDateTime",
                        field: "date_time",
                        showTime: true,
                        textInput: true,
                        useWidgets: true
                    }
                ]
            },
            {
                title: "Demo: Countdown, button",
                clinician: true,
                elements: [
                    {
                        type: "QuestionHeading",
                        text: "Countdown"
                    },
                    {
                        type: "QuestionCountdown",
                        seconds: 60
                    },
                    {
                        type: "QuestionHeading",
                        text: "Button"
                    },
                    {
                        type: "QuestionButton",
                        text: "Greet",
                        fnClicked: function () {
                            uifunc.alert("Hello!");
                        }
                    }
                ]
            },
            {
                title: "Demo: Diagnostic code",
                clinician: true,
                elements: [
                    {
                        type: "QuestionHeading",
                        text: "Diagnostic code (in this example, ICD-10)"
                    },
                    {
                        type: "QuestionDiagnosticCode",
                        code_field: "diagnosticcode_code",
                        description_field: "diagnosticcode_description",
                        codelist_filename: "common/CODES_ICD10"
                    }
                ]
            },
            {
                title: "Demo: Slider",
                clinician: true,
                elements: [
                    {
                        type: "QuestionHeading",
                        text: "Slider"
                    },
                    {
                        type: "QuestionText",
                        text: "Drag the slider to set the value.",
                        bold: true
                    },
                    {
                        type: "QuestionText",
                        text: "... with 1dp, no step size:"
                    },
                    {
                        type: "QuestionSlider",
                        field: "slider1",
                        min: 0,
                        max: 10,
                        showCurrentValueNumerically: true,
                        numberFormatDecimalPlaces: 1,
                        labels: [
                            { left: 0, text: "0" },
                            { center: "10%", text: "1" },
                            { center: "20%", text: "2" },
                            { center: "30%", text: "3" },
                            { center: "40%", text: "4" },
                            { center: "50%", text: "5" },
                            { center: "60%", text: "6" },
                            { center: "70%", text: "7" },
                            { center: "80%", text: "8" },
                            { center: "90%", text: "9" },
                            { right: 0, text: "10" }
                        ]
                    },
                    {
                        type: "QuestionText",
                        text: "... with 0dp and a step size of 1:"
                    },
                    {
                        type: "QuestionSlider",
                        field: "slider2",
                        min: 0,
                        max: 10,
                        step: 1,
                        showCurrentValueNumerically: true,
                        numberFormatDecimalPlaces: 0,
                        labels: [
                            { left: 0, text: "Zero" },
                            { center: "10%", text: "One" },
                            { center: "20%", text: "Two" },
                            { center: "30%", text: "Three" },
                            { center: "40%", text: "Four" },
                            { center: "50%", text: "Five\nMiddling" },
                            { center: "60%", text: "Six" },
                            { center: "70%", text: "Seven" },
                            { center: "80%", text: "Eight" },
                            { center: "90%", text: "Nine" },
                            { right: 0, text: "Ten" }
                        ]
                    }
                ]
            },
            {
                title: "Demo: Image stack",
                clinician: true,
                elements: [
                    {
                        type: "QuestionHeading",
                        text: "Thermometer-like image stack"
                    },
                    {
                        type: "QuestionText",
                        text: "Touch the thermometer to set it.",
                        bold: true
                    },
                    {
                        type: "QuestionThermometer",
                        mandatory: false,
                        inactiveImages: [
                            THERMOMETER_10_UNSEL,
                            THERMOMETER_09_UNSEL,
                            THERMOMETER_08_UNSEL,
                            THERMOMETER_07_UNSEL,
                            THERMOMETER_06_UNSEL,
                            THERMOMETER_05_UNSEL,
                            THERMOMETER_04_UNSEL,
                            THERMOMETER_03_UNSEL,
                            THERMOMETER_02_UNSEL,
                            THERMOMETER_01_UNSEL,
                            THERMOMETER_00_UNSEL
                        ],
                        activeImages: [
                            THERMOMETER_10_SEL,
                            THERMOMETER_09_SEL,
                            THERMOMETER_08_SEL,
                            THERMOMETER_07_SEL,
                            THERMOMETER_06_SEL,
                            THERMOMETER_05_SEL,
                            THERMOMETER_04_SEL,
                            THERMOMETER_03_SEL,
                            THERMOMETER_02_SEL,
                            THERMOMETER_01_SEL,
                            THERMOMETER_00_SEL
                        ],
                        text: [
                            L('distressthermometer_distress_extreme'),
                            "", "", "", "", "",
                            "", "", "", "",
                            L('distressthermometer_distress_none')
                        ],
                        imageWidth: 192,
                        values: [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
                        field: 'thermometer'
                    }
                ]
            },
            {
                title: "Demo: Sketching canvas",
                clinician: true,
                disableScroll: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: "Touch below to sketch. Press the reload button to reset the image.",
                        bold: true
                    },
                    {
                        type: "QuestionCanvas",
                        image: IMAGE_PATH,
                        field: "canvas_blobid"
                    }
                ]
            },
            {
                title: "Demo: Audio player",
                clinician: true,
                elements: [
                    {
                        type: "QuestionText",
                        text: "Press the speaker to play/stop the sound.",
                        bold: true
                    },
                    {
                        type: "QuestionAudioPlayer",
                        filename: UICONSTANTS.SOUND_TEST
                    }
                ]
            }
        ];

        questionnaire = new Questionnaire({
            readOnly: readOnly,
            pages: pages,
            callbackThis: self,
            fnGetFieldValue: self.defaultGetFieldValueFn,
            fnSetField: self.defaultSetFieldFn,
            fnFinished: self.defaultFinishedFn
        });
        questionnaire.open();
    }

});

module.exports = DemoQuestionnaire;
