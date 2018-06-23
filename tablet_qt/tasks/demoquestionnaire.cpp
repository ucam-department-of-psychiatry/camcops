/*
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
*/

// #define DEBUG_BIG_HEADER_ONLY_PAGE
// #define DEBUG_DIAGNOSTIC_SET_CREATION_SPEED

#include "demoquestionnaire.h"
#include "core/camcopsapp.h"
#include "common/textconst.h"
#include "common/uiconst.h"
#include "diagnosis/icd10.h"
#include "diagnosis/icd9cm.h"
#include "lib/uifunc.h"
#include "lib/stringfunc.h"
#include "tasklib/taskfactory.h"

#include "questionnairelib/questionnaire.h"

#include "questionnairelib/qupage.h"
#include "questionnairelib/quelement.h"

#include "questionnairelib/quflowcontainer.h"
#include "questionnairelib/quhorizontalcontainer.h"
#include "questionnairelib/quverticalcontainer.h"
#include "questionnairelib/qugridcontainer.h"

#include "questionnairelib/quaudioplayer.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/qubutton.h"
#include "questionnairelib/qucanvas.h"
#include "questionnairelib/qucountdown.h"
#include "questionnairelib/qudatetime.h"
#include "questionnairelib/qudiagnosticcode.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/quhorizontalline.h"
#include "questionnairelib/quimage.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditdouble.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qumcqgriddouble.h"
#include "questionnairelib/qumcqgridsingleboolean.h"
#include "questionnairelib/qumultipleresponse.h"
#include "questionnairelib/quphoto.h"
#include "questionnairelib/qupickerinline.h"
#include "questionnairelib/qupickerpopup.h"
#include "questionnairelib/quslider.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/quspinboxdouble.h"
#include "questionnairelib/quspinboxinteger.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "questionnairelib/quthermometer.h"

const QString DemoQuestionnaire::DEMOQUESTIONNAIRE_TABLENAME("demoquestionnaire");

const int SOUNDTEST_1_VOLUME = 50;


void initializeDemoQuestionnaire(TaskFactory& factory)
{
    static TaskRegistrar<DemoQuestionnaire> registered(factory);
}


DemoQuestionnaire::DemoQuestionnaire(CamcopsApp& app,
                                     DatabaseManager& db, const int load_pk) :
    Task(app, db, DEMOQUESTIONNAIRE_TABLENAME, true, false, false)
{
    using stringfunc::strseq;

    addFields(strseq("mcq", 1, 10), QVariant::Int);  // 9-10: v2
    addFields(strseq("mcqbool", 1, 3), QVariant::Bool);
    addFields(strseq("multipleresponse", 1, 6), QVariant::Bool);
    addFields(strseq("booltext", 1, 22), QVariant::Bool);
    addFields(strseq("boolimage", 1, 2), QVariant::Bool);
    addFields(strseq("slider", 1, 2), QVariant::Double);
    addFields(strseq("picker", 1, 2), QVariant::Int);
    addFields(strseq("mcqtext_", 1, 3, {"a", "b"}), QVariant::String);
    addField("typedvar_text", QVariant::String);
    addField("typedvar_text_multiline", QVariant::String);
    addField("typedvar_text_rich", QVariant::String);  // v2
    addField("typedvar_int", QVariant::Int);
    addField("typedvar_real", QVariant::Double);
    addField("spinbox_int", QVariant::Int);  // v2
    addField("spinbox_real", QVariant::Double);  // v2
    addField("date_time", QVariant::DateTime);
    addField("date_only", QVariant::Date);
    addField("time_only", QVariant::Time);  // v2
    addField("thermometer", QVariant::Int);
    addField("diagnosticcode_code", QVariant::String);
    addField("diagnosticcode_description", QVariant::String);
    addField("diagnosticcode2_code", QVariant::String);  // v2
    addField("diagnosticcode2_description", QVariant::String);  // v2
    addField("photo_blobid", QVariant::Int);  // FK to BLOB table
    // addField("photo_rotation", QVariant::String);  // DEFUNCT in v2
    addField("canvas_blobid", QVariant::Int);  // FK to BLOB table
    addField("canvas2_blobid", QVariant::Int);  // FK to BLOB table; v2

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class overrides
// ============================================================================

QString DemoQuestionnaire::shortname() const
{
    return "Demo";
}


QString DemoQuestionnaire::longname() const
{
    return "Demonstration task";
}


QString DemoQuestionnaire::menusubtitle() const
{
    return "Tutorial and illustration of questionnaire task elements";
}


// ============================================================================
// Instance overrides
// ============================================================================

bool DemoQuestionnaire::isComplete() const
{
    return true;
}


QStringList DemoQuestionnaire::summary() const
{
    return QStringList{"Demonstration questionnaire; no summary"};
}


OpenableWidget* DemoQuestionnaire::editor(const bool read_only)
{
    const QString& longtext = textconst::LOREM_IPSUM_1;
    const QString& lipsum2 = textconst::LOREM_IPSUM_2;
    const QString url("http://doc.qt.io/qt-5.7/richtext-html-subset.html");
    const QString html(QString(
        "Text with embedded HTML markup, providing <b>bold</b>, "
        "<i>italic</i>, and others as per Qt rich text syntax at "
        "<a href=\"%1\">%1</a>."
    ).arg(url));

    // ------------------------------------------------------------------------
    // Text
    // ------------------------------------------------------------------------

    QuPagePtr page_text((new QuPage{
        new QuText(tr("We’ll demonstrate the elements from which questionnaire"
                      " tasks can be made. Press the ‘Next’ button at the top "
                      "right of the screen.\n")),
        (new QuText("normal text"))->addTag("tag1"),
        (new QuText("bold text"))->setBold(),
        (new QuText("italic text"))->setItalic(),
        (new QuText(html))->setOpenLinks(),
        (new QuText("big text"))->setBig(),
        (new QuText("warning text"))->setWarning(),
        new QuText("Below here: space fillers, just to test scrolling"),
        (new QuText(longtext))->setBig(),
    })->setTitle(QString("Text [With a long title: %1]")
                 .arg(textconst::LOREM_IPSUM_3)));
    for (int i = 0; i < 20; ++i) {
        page_text->addElement((new QuText("big text"))->setBig());
    }
    page_text->addElement(
        (new QuText("... was that enough to scroll vertically?"))->setBold()
    );

#ifdef DEBUG_BIG_HEADER_ONLY_PAGE
    QuPagePtr page_text_header_only((new QuPage{
        new QuText("Very long title, to check sizing."),
    })->setTitle(textconst::LOREM_IPSUM_1));
#endif

    // ------------------------------------------------------------------------
    // Image
    // ------------------------------------------------------------------------

    QuPagePtr page_image((new QuPage{
        new QuHeading("Image:"),
        new QuImage(uifunc::iconFilename(uiconst::ICON_CAMCOPS)),
        new QuHeading("... heading under image, to check vertical size"),
    })->setTitle("Headings, images"));

    // ------------------------------------------------------------------------
    // Headings, containers, text alignment, lines
    // ------------------------------------------------------------------------

    const Qt::Alignment bottomleft = Qt::AlignLeft | Qt::AlignBottom;
    const Qt::Alignment centre = Qt::AlignHCenter | Qt::AlignVCenter;
    const Qt::Alignment topright = Qt::AlignRight | Qt::AlignTop;

    QuHorizontalContainer* horiz1 = new QuHorizontalContainer();
    horiz1->addElement((new QuText("Text 1 (right/top)"))->setAlignment(topright), topright);
    horiz1->addElement((new QuText("Text 2 (centre/vcentre)"))->setAlignment(centre), centre);
    horiz1->addElement((new QuText("Text 3 (left/bottom)"))->setAlignment(bottomleft), bottomleft);
    horiz1->addElement(new QuText("Text 4: " + longtext));
    horiz1->setAddStretchRight(false);

    QuVerticalContainer* vert1 = new QuVerticalContainer;
    vert1->addElement((new QuText("Text 1 (right/top)"))->setAlignment(topright), topright);
    vert1->addElement((new QuText("Text 2 (centre/vcentre)"))->setAlignment(centre), centre);
    vert1->addElement((new QuText("Text 3 (left/bottom)"))->setAlignment(bottomleft), bottomleft);
    vert1->addElement(new QuText("Text 4: " + lipsum2));

    QuPagePtr page_headings_layout((new QuPage{
        new QuHeading("This is a heading"),
        new QuHeading("Horizontal line, line, spacer, line:"),
        new QuHorizontalLine(),
        new QuHorizontalLine(),
        new QuSpacer(),
        new QuHorizontalLine(),
        new QuHeading("Flow container (generally preferred to horizontal "
                      "container; better on small screens):"),
        new QuFlowContainer{
            (new QuText("Text 1 (right/top)"))->setAlignment(topright),
            (new QuText("Text 2 (centre/vcentre)"))->setAlignment(centre),
            (new QuText("Text 3 (left/bottom)"))->setAlignment(bottomleft),
            new QuText("Text 4: " + lipsum2),
        },
        new QuHeading("Horizontal container (with stretch on right):"),
        (new QuHorizontalContainer{
            new QuText("Text 1"),
            new QuText("Text 2"),
            new QuText("Text 3"),
        })->setAddStretchRight(true),
        new QuHeading("Horizontal container (without stretch on right; blank widget alignment):"),
        (new QuHorizontalContainer{
            (new QuText("Text 1 (right/top)"))->setAlignment(topright),
            (new QuText("Text 2 (centre/vcentre)"))->setAlignment(centre),
            (new QuText("Text 3 (left/bottom)"))->setAlignment(bottomleft),
        })->setAddStretchRight(false)->setWidgetAlignment(Qt::Alignment()),
        new QuHeading("Horizontal container (no stretch on right, showing alignments):"),
        horiz1,
        new QuHeading("Vertical container:"),
        vert1,
        new QuHeading("Grid container:"),
        new QuGridContainer{
            QuGridCell(new QuText("<b>row 0, col 0:</b> " + lipsum2), 0, 0),
            QuGridCell(new QuText("<b>row 0, col 1 [+1]:</b> " + lipsum2), 0, 1, 1, 2),
            QuGridCell(new QuText("<b>row 1, col 0 [+1]:</b> " + lipsum2), 1, 0, 1, 2),
            QuGridCell(new QuText("<b>row 1 [+1], col 2:</b> " + lipsum2), 1, 2, 2, 1),
            QuGridCell(new QuText("<b>row 2, col 0:</b> " + lipsum2), 2, 0),
            QuGridCell(new QuText("<b>row 2, col 1:</b> " + lipsum2), 2, 1),
        },
        new QuHeading("Another grid (2:1 columns):"),
        (new QuGridContainer{
            QuGridCell(new QuText("<b>r0 c0</b> " + lipsum2), 0, 0, 1, 1),
            QuGridCell(new QuText("<b>r0 c1 [+1]</b> " + lipsum2), 0, 1, 1, 2),
            QuGridCell(new QuText("<b>r1 c0</b> " + lipsum2), 1, 0, 1, 1),
            QuGridCell(new QuText("<b>r1 c1 [+1]</b> " + lipsum2), 1, 1, 1, 2),
        })
            ->setColumnStretch(0, 2)
            ->setColumnStretch(1, 1),
        new QuHeading("Another grid (1:1 columns):"),
        (new QuGridContainer{
            QuGridCell(new QuText("<b>r0 c0</b> " + lipsum2), 0, 0),
            QuGridCell(new QuText("<b>r0 c1</b> " + lipsum2), 0, 1),
            QuGridCell(new QuText("<b>r1 c0</b> " + lipsum2), 1, 0),
            QuGridCell(new QuText("<b>r1 c1</b> " + lipsum2), 1, 1),
        })
            ->setColumnStretch(0, 1)
            ->setColumnStretch(1, 1),
        new QuHeading("Another grid (1:1:1 columns, expanding horizontally, "
                      "fixed column style = default):"),
        (new QuGridContainer{
            QuGridCell(new QuText("1. Short"), 0, 0),
            QuGridCell(new QuText("2. Medium sort of length"), 0, 1),
            QuGridCell(new QuText("3. Longer " + lipsum2), 0, 2),
        })
            ->setColumnStretch(0, 1)
            ->setColumnStretch(1, 1)
            ->setColumnStretch(2, 1)
            ->setExpandHorizontally(true)
            ->setFixedGrid(true),
        new QuHeading("Another grid (1:1:1 columns, non-expanding, "
                      "non-fixed style):"),
        (new QuGridContainer{
            QuGridCell(new QuText("1. Short"), 0, 0),
            QuGridCell(new QuText("2. Medium sort of length"), 0, 1),
            QuGridCell(new QuText("3. Longer " + lipsum2), 0, 2),
        })
            ->setColumnStretch(0, 1)
            ->setColumnStretch(1, 1)
            ->setColumnStretch(2, 1)
            ->setExpandHorizontally(false)
            ->setFixedGrid(false),
        new QuHeading("More automated grid (of label/element pairs):"),
        questionnairefunc::defaultGridRawPointer({
            {"<b>LHS:</b> " + lipsum2,
             new QuText("<b>RHS:</b> " + lipsum2)},
            {"<b>LHS:</b> " + lipsum2,
             new QuText("<b>RHS:</b> " + lipsum2)},
            {"<b>LHS:</b> " + lipsum2,
             new QuText("<b>RHS:</b> " + lipsum2)},
        }),
    })->setTitle("Headings, containers, text alignment, lines"));

    // ------------------------------------------------------------------------
    // Audio players, countdown
    // ------------------------------------------------------------------------

    QuPagePtr page_audio_countdown((new QuPage{
        new QuHeading("Simple audio player:"),
        (new QuAudioPlayer(uiconst::DEMO_SOUND_URL_2))->setVolume(SOUNDTEST_1_VOLUME),
        new QuHeading("Audio player with volume control:"),
        (new QuAudioPlayer(uiconst::DEMO_SOUND_URL_1))->setOfferVolumeControl(),
        new QuHeading("Countdown:"),
        new QuCountdown(20),
    })->setTitle("Audio players, countdowns"));

    // ------------------------------------------------------------------------
    // Boolean
    // ------------------------------------------------------------------------

    QuPagePtr page_boolean((new QuPage{
        new QuText(tr(
            "On this page, some questions must be completed before the ‘Next’ "
            "button appears. <b>Make the yellow disappear to continue!</b>")),
        new QuHeading("Boolean text, not allowing ‘unset’, with clickable "
                                "content:"),
        new QuBoolean("Click me to toggle (null → true → false → true → …)",
                      fieldRef("booltext1")),
        new QuHeading("Boolean text, allowing ‘unset’, on the "
                                   "<i>same</i> field, with a smaller icon, "
                                   "and non-clickable content:"),
        (new QuBoolean("Click me (null → true → false → null → …)",
                      fieldRef("booltext1")))
                      ->setBigIndicator(false)
                      ->setAllowUnset()
                      ->setContentClickable(false),
        new QuHeading("Same field, with text-style widget:"),
        (new QuBoolean("Boolean-as-text",
                      fieldRef("booltext1")))
                      ->setAsTextButton(),
        new QuHeading("Text field from the Boolean field used above:"),
        new QuText(fieldRef("booltext1")),
        new QuHeading("Another boolean field, using an image:"),
        new QuBoolean(uifunc::iconFilename(uiconst::ICON_CAMCOPS),
                      QSize(), fieldRef("boolimage1")),
        new QuHeading("... clone with non-clickable image:"),
        (new QuBoolean(uifunc::iconFilename(uiconst::ICON_CAMCOPS),
                      QSize(), fieldRef("boolimage1")))->setContentClickable(false),
        // Now the ACE-III address example:
        new QuGridContainer{
            QuGridCell(new QuVerticalContainer{
                new QuFlowContainer{
                    aceBoolean("address_1", "booltext2"),
                    aceBoolean("address_2", "booltext3"),
                },
                new QuFlowContainer{
                    aceBoolean("address_3", "booltext4"),
                    aceBoolean("address_4", "booltext5"),
                    aceBoolean("address_5", "booltext6"),
                },
                aceBoolean("address_6", "booltext7"),
                aceBoolean("address_7", "booltext8"),
            }, 0, 0),
            QuGridCell(new QuVerticalContainer{
                new QuFlowContainer{
                    aceBoolean("address_1", "booltext9"),
                    aceBoolean("address_2", "booltext10"),
                },
                new QuFlowContainer{
                    aceBoolean("address_3", "booltext11"),
                    aceBoolean("address_4", "booltext12"),
                    aceBoolean("address_5", "booltext13"),
                },
                aceBoolean("address_6", "booltext14"),
                aceBoolean("address_7", "booltext15"),
            }, 0, 1),
            QuGridCell(new QuVerticalContainer{
                new QuFlowContainer{
                    aceBoolean("address_1", "booltext16"),
                    aceBoolean("address_2", "booltext17"),
                },
                new QuFlowContainer{
                    aceBoolean("address_3", "booltext18"),
                    aceBoolean("address_4", "booltext19"),
                    aceBoolean("address_5", "booltext20"),
                },
                aceBoolean("address_6", "booltext21"),
                aceBoolean("address_7", "booltext22"),
            }, 1, 0),
        },
        (new QuBoolean(
            uifunc::resourceFilename("ace3/penguin.png"),
            QSize(),
            fieldRef("boolimage2"))
        )->setBigIndicator(false),

    })->setTitle("Booleans; multiple views on a single field"));

    // ------------------------------------------------------------------------
    // MCQ
    // ------------------------------------------------------------------------

    const NameValueOptions options_A{
        {"option_1", 1},
        {"option_2", 2},
        {"option_3, with much longer text: " + longtext, 3},
    };
    const NameValueOptions options_B{
        {"option_1", 1},
        {"option_2", 2},
        {"option_3", 3},
        {"option_4", 4},
        {"option_5", 5},
        {"option_6", 6},
        {"option_7", 7},
        {"option_8", 8},
        {"option_9", 9},
        {"option_10", 10},
        {"option_11", 11},
        {"option_12", 12},
        {"option_13", 13},
        {"option_14", 14},
        {"option_15", 15},
        {"option_16", 16},
        {"option_17", 17},
    };
    const NameValueOptions options_C{
        {"option_1", 1},
        {"option_2", 2},
        // {"option_NULL", QVariant()},  // will assert
        {"option_99", 99},
    };
    const NameValueOptions options_D{
        {"Not at all", 0},
        {"Several days", 1},
        {"More than half the days", 2},
        {"Nearly every day", 3},
    };
    const NameValueOptions options_E{
        {"A", "A"},
        {"B", "B"},
        {"C", "C"},
        {"D", "D"},
    };
    const NameValueOptions options_F{
        {"X", "X"},
        {"Y", "Y"},
        {"Z", "Z"},
    };
    QuPagePtr page_mcq((new QuPage{
        new QuHeading("Plain MCQ:"),
        new QuMcq(fieldRef("mcq1"), options_A),
        new QuHeading("Same MCQ/field, reconfigured (randomized, "
                      "instructions, horizontal, as text button):"),
        (new QuMcq(fieldRef("mcq1"), options_A))
                            ->setRandomize(true)
                            ->setShowInstruction(true)
                            ->setHorizontal(true)
                            ->setAsTextButton(true),
        new QuHeading("Same MCQ/field, reconfigured:"),
        (new QuMcq(fieldRef("mcq1"), options_A))
                            ->setAsTextButton(true),
        new QuHeading("A second MCQ:"),
        new QuMcq(fieldRef("mcq2"), options_C),
        new QuHeading("Another:"),
        new QuMcq(fieldRef("mcq3"), options_B),
        new QuHeading("The previous MCQ, reconfigured:"),
        (new QuMcq(fieldRef("mcq3"), options_B))
                            ->setHorizontal(true),
        new QuHeading("A fourth MCQ, as text:"),
        (new QuMcq(fieldRef("mcq4"), options_B))
                            ->setHorizontal(true)
                            ->setAsTextButton(true),
    })->setTitle("Multiple-choice questions (MCQs)"));

    // ------------------------------------------------------------------------
    // MCQ variants
    // ------------------------------------------------------------------------

    QuPagePtr page_mcq_variants((new QuPage{
         new QuHeading("MCQ grid:"),
         (new QuMcqGrid(
            {
                QuestionWithOneField("Question A", fieldRef("mcq5")),
                QuestionWithOneField("Question B", fieldRef("mcq6")),
                QuestionWithOneField("Question C", fieldRef("mcq7")),
                QuestionWithOneField("Question D (= A)", fieldRef("mcq5")),
                QuestionWithOneField("Question E (= B)", fieldRef("mcq6")),
            },
            options_D
        ))->setSubtitles({{3, "subtitle before D"}}),
        new QuHeading("Another MCQ grid:"),
        (new QuMcqGrid(
            {
                QuestionWithOneField("Question A", fieldRef("mcq8")),
                QuestionWithOneField("Question B; " + lipsum2, fieldRef("mcq9")),
                QuestionWithOneField("Question C", fieldRef("mcq10")),
            },
        options_A
        ))->setTitle("MCQ 2 title; " + lipsum2),
        new QuHeading("Double MCQ grid:"),
        (new QuMcqGridDouble(
            {
                QuestionWithTwoFields("Question A",
                                         fieldRef("mcqtext_1a"),
                                         fieldRef("mcqtext_1b")),
                QuestionWithTwoFields("Question B; " + lipsum2,
                                         fieldRef("mcqtext_2a"),
                                         fieldRef("mcqtext_2b")),
                QuestionWithTwoFields("Question C",
                                         fieldRef("mcqtext_3a"),
                                         fieldRef("mcqtext_3b")),
            },
        options_E, options_F
        ))  ->setTitle("Double-MCQ title")
            ->setSubtitles({{2, "subtitle before C"}}),
        new QuHeading("MCQ grid with single Boolean (right):"),
        (new QuMcqGridSingleBoolean(
            {
                QuestionWithTwoFields("Question A",
                                         fieldRef("mcq5"), fieldRef("mcqbool1")),
                QuestionWithTwoFields("Question B; " + lipsum2,
                                         fieldRef("mcq6"), fieldRef("mcqbool2")),
                QuestionWithTwoFields("Question C",
                                         fieldRef("mcq7"), fieldRef("mcqbool3")),
            },
            options_D,
            "Happy?"
        ))  ->setTitle("Title for MCQ grid with single boolean")
            ->setSubtitles({{2, "subtitle before C"}}),
        new QuHeading("MCQ grid with single Boolean (left):"),
        (new QuMcqGridSingleBoolean(
            {
                QuestionWithTwoFields("Question A",
                                         fieldRef("mcq5"), fieldRef("mcqbool1")),
                QuestionWithTwoFields("Question B; " + lipsum2,
                                         fieldRef("mcq6"), fieldRef("mcqbool2")),
                QuestionWithTwoFields("Question C",
                                         fieldRef("mcq7"), fieldRef("mcqbool3")),
            },
            options_D,
            "Happy?"
        ))  ->setTitle("Title for MCQ grid with single boolean")
            ->setBooleanLeft(true),
    })->setTitle("MCQ variants"));

    // ------------------------------------------------------------------------
    // Multiple responses
    // ------------------------------------------------------------------------

    QuPagePtr page_multiple_response((new QuPage{
        new QuHeading("Standard n-from-many format:"),
        (new QuMultipleResponse({
            QuestionWithOneField(fieldRef("multipleresponse1"), "(a) First stem"),
            QuestionWithOneField(fieldRef("multipleresponse2"), "(b) Second stem"),
            QuestionWithOneField(fieldRef("multipleresponse3"), "(c) Third stem"),
            QuestionWithOneField(fieldRef("multipleresponse4"), "(d) Fourth stem"),
            QuestionWithOneField(fieldRef("multipleresponse5"), "(e) Fifth stem"),
            QuestionWithOneField(fieldRef("multipleresponse6"), "(f) Sixth stem"),
        }))->setMinimumAnswers(2)->setMaximumAnswers(3),
        new QuHeading("With instructions off, horizontally, and text-button style:"),
        (new QuMultipleResponse({
            QuestionWithOneField(fieldRef("multipleresponse1"), "(a) First stem"),
            QuestionWithOneField(fieldRef("multipleresponse2"), "(b) Second stem"),
            QuestionWithOneField(fieldRef("multipleresponse3"), "(c) Third stem"),
            QuestionWithOneField(fieldRef("multipleresponse4"), "(d) Fourth stem"),
            QuestionWithOneField(fieldRef("multipleresponse5"), "(e) Fifth stem"),
            QuestionWithOneField(fieldRef("multipleresponse6"), "(f) Sixth stem"),
        }))->setMinimumAnswers(2)
            ->setMaximumAnswers(3)
            ->setShowInstruction(false)
            ->setHorizontal(true)
            ->setAsTextButton(true),
    })->setTitle("Multiple-response questions"));

    // ------------------------------------------------------------------------
    // Pickers
    // ------------------------------------------------------------------------

    QuPagePtr page_pickers((new QuPage{
        new QuHeading("Inline picker:"),
        new QuPickerInline(fieldRef("picker1"), options_A),
        new QuHeading("Its clone:"),
        new QuPickerInline(fieldRef("picker1"), options_A),
        new QuHeading("Popup picker:"),
        (new QuPickerPopup(fieldRef("picker2"), options_A))
                                ->setPopupTitle("Pickers; question 5"),
    })->setTitle("Pickers"));

    // ------------------------------------------------------------------------
    // Sliders, thermometer
    // ------------------------------------------------------------------------

    QVector<QuThermometerItem> thermometer_items;
    for (int i = 0; i <= 10; ++i) {
        QString text = QString::number(i);
        if (i == 10) {
            text += " - very distressed";
        } else if (i == 0) {
            text += " - chilled out";
        }
        QuThermometerItem item(
            uifunc::resourceFilename(
                        QString("distressthermometer/dt_sel_%1.png").arg(i)),
            uifunc::resourceFilename(
                        QString("distressthermometer/dt_unsel_%1.png").arg(i)),
            text,
            i
        );
        thermometer_items.append(item);
    }
    QuPagePtr page_sliders((new QuPage{
        new QuHeading("Integer slider:"),
        (new QuSlider(fieldRef("thermometer"), 0, 10, 1))
                                ->setTickInterval(1)
                                ->setTickPosition(QSlider::TicksBothSides)
                                ->setShowValue(true),
        new QuHeading("Integer slider (same field as above)"),
        (new QuSlider(fieldRef("thermometer"), 0, 10, 1))
                                ->setShowValue(true)
                                ->setTickInterval(2)
                                ->setTickPosition(QSlider::TicksBothSides)
                                ->setUseDefaultTickLabels(true)
                                ->setTickLabelPosition(QSlider::TicksBothSides)
                                ->setHorizontal(false),
        new QuHeading("Real/float slider:"),
        (new QuSlider(fieldRef("slider1"), 0, 10, 1))
                                ->setShowValue(true)
                                ->setTickInterval(1)
                                ->setTickPosition(QSlider::TicksBelow)
                                ->setConvertForRealField(true, 5, 6),
        new QuHeading("Real slider with custom labels (edging in extreme labels):"),
        (new QuSlider(fieldRef("slider2"), 100, 500, 1))
                                ->setConvertForRealField(true, 1, 5)
                                ->setShowValue(false)
                                ->setTickInterval(1)
                                ->setTickPosition(QSlider::TicksAbove)
                                ->setTickLabelPosition(QSlider::TicksBelow)
                                ->setTickLabels({
                                    {100, "one: low"},
                                    {300, "three: medium"},
                                    {500, "five: maximum!"},
                                })
                                ->setShowValue(true)
                                ->setEdgeInExtremeLabels(true),
        new QuHeading("Thermometer:"),
        (new QuThermometer(fieldRef("thermometer"), thermometer_items))
                                ->setRescale(true, 0.4),
    })
        ->setTitle("Sliders and thermometers")
        ->setType(QuPage::PageType::ClinicianWithPatient));

    // ------------------------------------------------------------------------
    // Editable variables inc. datetime
    // ------------------------------------------------------------------------

    QuPagePtr page_vars((new QuPage{
        new QuText("Pages for clinicians have a different background colour."),
        new QuHeading("Date/time:"),
        new QuDateTime(fieldRef("date_time")),
        new QuHeading("Date/time (with ‘now’ and ‘nullify’ buttons):"),
        (new QuDateTime(fieldRef("date_time")))
                             ->setOfferNowButton(true)
                             ->setOfferNullButton(true),
        new QuHeading("Date/time (custom format):"),
        (new QuDateTime(fieldRef("date_time")))
                             ->setMode(QuDateTime::CustomDateTime)
                             ->setCustomFormat("yyyy MM dd HH:mm:ss:zzz"),
        new QuHeading("Date:"),
        (new QuDateTime(fieldRef("date_only")))
                             ->setMode(QuDateTime::DefaultDate),
        new QuHeading("Date (custom format):"),
        (new QuDateTime(fieldRef("date_only")))
                             ->setMode(QuDateTime::CustomDate)
                             ->setCustomFormat("yyyy MM dd"),
        new QuHeading("Time:"),
        (new QuDateTime(fieldRef("time_only")))
                             ->setMode(QuDateTime::DefaultTime),
        new QuHeading("Time (custom format):"),
        (new QuDateTime(fieldRef("time_only")))
                             ->setMode(QuDateTime::CustomTime)
                             ->setCustomFormat("HH:mm:ss"),
        new QuHeading("Integer spinbox (range 5–10):"),
        new QuSpinBoxInteger(fieldRef("spinbox_int"), 5, 10),
        new QuHeading("Double spinbox (range 7.1–7.9):"),
        new QuSpinBoxDouble(fieldRef("spinbox_real"), 7.1, 7.9),
        new QuHeading("Text editor (plain text):"),
        new QuTextEdit(fieldRef("typedvar_text_multiline"), false),
        new QuHeading("Text editor (clone of previous):"),
        new QuTextEdit(fieldRef("typedvar_text_multiline"), false),
        new QuHeading("Text editor (rich text):"),
        (new QuTextEdit(fieldRef("typedvar_text_rich"), true))
                             ->setHint("This one has a hint "
                                       "(placeholder text)"),
        new QuHeading("Line editor (plain):"),
        (new QuLineEdit(fieldRef("typedvar_text")))
                             ->setHint("hint: plain text"),
        new QuHeading("Line editor (integer, range 13–19):"),
        new QuLineEditInteger(fieldRef("typedvar_int"), 13, 19),
        new QuHeading("Line editor (double, "
                             "range -0.05 to -0.09, 2dp):"),
        new QuLineEditDouble(fieldRef("typedvar_real"), -0.05, -0.09, 2),
        new QuHeading("Variables in a grid:"),
        questionnairefunc::defaultGridRawPointer({
            {"label 1 (text)", new QuLineEdit(fieldRef("typedvar_text"))},
            {"label 2 (int 13-19)", new QuLineEditInteger(fieldRef("typedvar_int"), 13, 19)},
            {"label 3", new QuHeading("Just a heading: " + lipsum2)},
            {"label 4", new QuDateTime(fieldRef("date_time"))},
            {"label 5 (multiline text)", new QuTextEdit(fieldRef("typedvar_text"))},
        }, uiconst::DEFAULT_COLSPAN_Q, uiconst::DEFAULT_COLSPAN_A),
    })
        ->setTitle("Editable variable including dates/times")
        ->setType(QuPage::PageType::Clinician));

    // ------------------------------------------------------------------------
    // Diagnostic codes
    // ------------------------------------------------------------------------

#ifdef DEBUG_DIAGNOSTIC_SET_CREATION_SPEED
    qDebug() << Q_FUNC_INFO << "Making ICD-10 data set...";
#endif
    QSharedPointer<Icd10> icd10 = QSharedPointer<Icd10>(new Icd10(m_app));
#ifdef DEBUG_DIAGNOSTIC_SET_CREATION_SPEED
    qDebug() << Q_FUNC_INFO << "... done";
    qDebug() << Q_FUNC_INFO << "Making ICD-9-CM data set...";
#endif
    QSharedPointer<Icd9cm> icd9cm = QSharedPointer<Icd9cm>(new Icd9cm(m_app));
#ifdef DEBUG_DIAGNOSTIC_SET_CREATION_SPEED
    qDebug() << Q_FUNC_INFO << "... done";
#endif
    QuPagePtr page_diag((new QuPage{
        new QuHeading("Diagnostic code, ICD-10:"),
        new QuDiagnosticCode(icd10,
                             fieldRef("diagnosticcode_code"),
                             fieldRef("diagnosticcode_description")),
        new QuHeading("Diagnostic code, clone of the preceding:"),
        new QuDiagnosticCode(icd10,
                             fieldRef("diagnosticcode_code"),
                             fieldRef("diagnosticcode_description")),
        new QuHeading("Diagnostic code, ICD-9-CM:"),
        new QuDiagnosticCode(icd9cm,
                             fieldRef("diagnosticcode2_code"),
                             fieldRef("diagnosticcode2_description")),
    })->setTitle("Diagnostic codes"));

    // ------------------------------------------------------------------------
    // Canvas
    // ------------------------------------------------------------------------

    QuPagePtr page_canvas_1((new QuPage{
        (new QuText("Page style: ClinicianWithPatient"))->setItalic(true),
        (new QuText("WATCH OUT: scrolling enabled for this page; may conflict "
                    "with canvas; see next page too"))->setWarning(true),
        new QuHeading("Canvas, blank start:"),
        new QuCanvas(blobFieldRef("canvas2_blobid", true)),
        new QuHeading("Canvas, using files:"),
        new QuCanvas(
            blobFieldRef("canvas_blobid", true),
            uifunc::resourceFilename("ace3/rhinoceros.png")),
        new QuHeading("Canvas, clone of the first one:"),
        new QuCanvas(blobFieldRef("canvas2_blobid", true)),
    })
        ->setTitle("Canvas (allowing scrolling)")
        ->setType(QuPage::PageType::ClinicianWithPatient));

    QuPagePtr page_canvas_2((new QuPage{
        new QuHeading("As before, but with scrolling disabled:"),
        new QuCanvas(
            blobFieldRef("canvas_blobid", true),
            uifunc::resourceFilename("ace3/rhinoceros.png")),
    })
        ->setTitle("Canvas (disabling scrolling)")
        ->allowScroll(false)
        ->setType(QuPage::PageType::ClinicianWithPatient));

    // ------------------------------------------------------------------------
    // Buttons
    // ------------------------------------------------------------------------

    // Safe object lifespan signal: can use std::bind
    QuPagePtr page_buttons((new QuPage{
        new QuButton(
            "Say hello",
            std::bind(&DemoQuestionnaire::callbackHello, this)),
        (new QuButton(
            "Say hello [disabled]",
            std::bind(&DemoQuestionnaire::callbackHello, this)))
                                ->setActive(false),
        new QuButton(
            "Button with args ('foo')",
            std::bind(&DemoQuestionnaire::callbackArg, this, "foo")),
        new QuButton(
            "Button with args ('bar')",
            std::bind(&DemoQuestionnaire::callbackArg, this, "bar")),
        new QuButton(
            uiconst::CBS_ADD, true, true,
            std::bind(&DemoQuestionnaire::callbackHello, this)),
    })->setTitle("Buttons"));

    // ------------------------------------------------------------------------
    // Photo (for a mandatory photo: last page in case we have no camera)
    // ... make it non-mandatory...
    // ------------------------------------------------------------------------

    QuPagePtr page_photo((new QuPage{
        new QuHeading("Photo:"),
        new QuPhoto(blobFieldRef("photo_blobid", false)),
    })->setTitle("Photo"));

    // ------------------------------------------------------------------------
    // Layout test: cf. WidgetTestMenu::testQuestionnaire()
    // ------------------------------------------------------------------------

    QuPagePtr page_minimal_layout((new QuPage{
        new QuText(textconst::LOREM_IPSUM_1),
    })->setTitle("Reasonably long title with several words"));

    // ------------------------------------------------------------------------
    // Questionnaire
    // ------------------------------------------------------------------------

    Questionnaire* questionnaire = new Questionnaire(m_app, {
        page_text,
#ifdef DEBUG_BIG_HEADER_ONLY_PAGE
        page_text_header_only,
#endif
        page_image, page_headings_layout,
        page_audio_countdown, page_boolean,
        page_mcq, page_mcq_variants, page_multiple_response, page_pickers,
        page_sliders, page_vars, page_diag,
        page_canvas_1, page_canvas_2,
        page_buttons,
        page_photo, page_minimal_layout,
    });
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Extra
// ============================================================================

void DemoQuestionnaire::callbackHello()
{
    uifunc::alert("Hello!");
}


void DemoQuestionnaire::callbackArg(const QString& arg)
{
    uifunc::alert("Function argument was: " + arg);
}


QuBoolean* DemoQuestionnaire::aceBoolean(const QString& stringname,
                                         const QString& fieldname)
{
    return (new QuBoolean(
        m_app.xstring("ace3", stringname),
        fieldRef(fieldname, false)
    ))->setBigIndicator(false);
}
