#include "demoquestionnaire.h"
#include "common/camcopsapp.h"
#include "common/uiconstants.h"
#include "diagnosis/icd10.h"
#include "diagnosis/icd9cm.h"
#include "lib/uifunc.h"
#include "lib/stringfunc.h"
#include "tasklib/taskfactory.h"

#include "questionnairelib/questionnaire.h"

#include "questionnairelib/qupage.h"
#include "questionnairelib/quelement.h"

#include "questionnairelib/qucontainerhorizontal.h"
#include "questionnairelib/qucontainervertical.h"
#include "questionnairelib/qucontainergrid.h"

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


DemoQuestionnaire::DemoQuestionnaire(CamcopsApp& app,
                                     const QSqlDatabase& db, int load_pk) :
    Task(app, db, "demoquestionnaire", false, false, false)
{
    using StringFunc::strseq;

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
    addField("photo_blobid", QVariant::String);  // FK to BLOB table
    addField("photo_rotation", QVariant::String);  // DEFUNCT in v2
    addField("canvas_blobid", QVariant::String);  // FK to BLOB table
    addField("canvas2_blobid", QVariant::String);  // FK to BLOB table; v2

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


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


bool DemoQuestionnaire::isComplete() const
{
    return true;
}


QString DemoQuestionnaire::summary() const
{
    return "Demonstration questionnaire; no summary";
}


OpenableWidget* DemoQuestionnaire::editor(bool read_only)
{
    qDebug() << Q_FUNC_INFO;
    const QString& longtext = UiConst::LOREM_IPSUM_1;
    const QString& lipsum2 = UiConst::LOREM_IPSUM_2;
    const QString url = "http://doc.qt.io/qt-5.7/richtext-html-subset.html";
    const QString html = QString(
        "Text with embedded HTML markup, providing <b>bold</b>, "
        "<i>italic</i>, and others as per Qt rich text syntax at "
        "<a href=\"%1\">%1</a>."
    ).arg(url);

    // ========================================================================
    // Text
    // ========================================================================

    QuPagePtr page_text((new QuPage{
        new QuText(tr("We’ll demonstrate the elements from which questionnaire"
                      " tasks can be made. Press the ‘Next’ button at the top "
                      "right of the screen.\n")),
        (new QuText("normal text"))->addTag("tag1"),
        (new QuText("bold text"))->bold(),
        (new QuText("italic text"))->italic(),
        (new QuText(html))->setOpenLinks(),
        (new QuText("big text"))->big(),
        (new QuText("warning text"))->warning(),
        new QuText("Below here: space fillers, just to test scrolling"),
        (new QuText(longtext))->big(),
    })->setTitle("Text "
                 "[With a long title: Lorem ipsum dolor sit amet, "
                 "consectetur adipiscing elit. Praesent sed cursus mauris. "
                 "Ut vulputate felis quis dolor molestie convallis.]"));
    for (int i = 0; i < 20; ++i) {
        page_text->addElement((new QuText("big text"))->big());
    }
    page_text->addElement(
        (new QuText("... was that enough to scroll vertically?"))->bold()
    );

    // ========================================================================
    // Headings, containers, text alignment, lines, images
    // ========================================================================

    QuPagePtr page_headings_layout_images((new QuPage{
        new QuHeading("This is a heading"),
        new QuHeading("Horizontal container (with stretch on right):"),
        (new QuContainerHorizontal{
            new QuText("Text 1 (left/vcentre) " + lipsum2),
            new QuText("Text 2 (left/vcentre) " + lipsum2),
            new QuText("Text 3 (left/vcentre) " + lipsum2),
        })->setAddStretchRight(true),
        new QuHeading("Horizontal container (without stretch on right):"),
        (new QuContainerHorizontal{
            new QuText("Text 1 (left/vcentre) " + lipsum2),
            new QuText("Text 2 (left/vcentre) " + lipsum2),
            new QuText("Text 3 (left/vcentre) " + lipsum2),
        })->setAddStretchRight(false),
        new QuHeading("Horizontal line, line, spacer, line:"),
        new QuHorizontalLine(),
        new QuHorizontalLine(),
        new QuSpacer(),
        new QuHorizontalLine(),
        new QuHeading("Horizontal container:"),
        new QuContainerHorizontal{
            (new QuText("Text 1 (right/top)"))->setAlignment(Qt::AlignRight | Qt::AlignTop),
            (new QuText("Text 2 (centre/vcentre)"))->setAlignment(Qt::AlignCenter | Qt::AlignVCenter),
            (new QuText("Text 3 (left/bottom)"))->setAlignment(Qt::AlignLeft | Qt::AlignBottom),
            new QuText("Text 4: " + lipsum2),
        },
        new QuHeading("Vertical container:"),
        new QuContainerVertical{
            (new QuText("Text 1 (right/top)"))->setAlignment(Qt::AlignRight | Qt::AlignTop),
            (new QuText("Text 2 (centre/vcentre)"))->setAlignment(Qt::AlignCenter | Qt::AlignVCenter),
            (new QuText("Text 3 (left/bottom)"))->setAlignment(Qt::AlignLeft | Qt::AlignBottom),
            new QuText("Text 4: " + lipsum2),
        },
        new QuHeading("Grid container:"),
        new QuContainerGrid{
            QuGridCell(new QuText("<b>row 0, col 0:</b> " + lipsum2), 0, 0),
            QuGridCell(new QuText("<b>row 0, col 1 [+1]:</b> " + lipsum2), 0, 1, 1, 2),
            QuGridCell(new QuText("<b>row 1, col 0 [+1]:</b> " + lipsum2), 1, 0, 1, 2),
            QuGridCell(new QuText("<b>row 1 [+1], col 2:</b> " + lipsum2), 1, 2, 2, 1),
            QuGridCell(new QuText("<b>row 2, col 0:</b> " + lipsum2), 2, 0),
            QuGridCell(new QuText("<b>row 2, col 1:</b> " + lipsum2), 2, 1),
        },
        new QuHeading("Another grid (2:1 columns):"),
        (new QuContainerGrid{
            QuGridCell(new QuText("<b>r0 c0</b> " + lipsum2), 0, 0, 1, 1),
            QuGridCell(new QuText("<b>r0 c1 [+1]</b> " + lipsum2), 0, 1, 1, 2),
            QuGridCell(new QuText("<b>r1 c0</b> " + lipsum2), 1, 0, 1, 1),
            QuGridCell(new QuText("<b>r1 c1 [+1]</b> " + lipsum2), 1, 1, 1, 2),
        })
            ->setColumnStretch(0, 2)
            ->setColumnStretch(1, 1),
        new QuHeading("Another grid (1:1 columns):"),
        (new QuContainerGrid{
            QuGridCell(new QuText("<b>r0 c0</b> " + lipsum2), 0, 0),
            QuGridCell(new QuText("<b>r0 c1</b> " + lipsum2), 0, 1),
            QuGridCell(new QuText("<b>r1 c0</b> " + lipsum2), 1, 0),
            QuGridCell(new QuText("<b>r1 c1</b> " + lipsum2), 1, 1),
        })
            ->setColumnStretch(0, 1)
            ->setColumnStretch(1, 1),
        new QuHeading("Another grid (1:1:1 columns, fixed column style = default):"),
        (new QuContainerGrid{
            QuGridCell(new QuText("1. Short"), 0, 0),
            QuGridCell(new QuText("2. Medium sort of length"), 0, 1),
            QuGridCell(new QuText("3. Longer " + lipsum2), 0, 2),
        })
            ->setColumnStretch(0, 1)
            ->setColumnStretch(1, 1)
            ->setColumnStretch(2, 1)
            ->setFixedGrid(true),
        new QuHeading("Another grid (1:1:1 columns, non-fixed style):"),
        (new QuContainerGrid{
            QuGridCell(new QuText("1. Short"), 0, 0),
            QuGridCell(new QuText("2. Medium sort of length"), 0, 1),
            QuGridCell(new QuText("3. Longer " + lipsum2), 0, 2),
        })
            ->setColumnStretch(0, 1)
            ->setColumnStretch(1, 1)
            ->setColumnStretch(2, 1)
            ->setFixedGrid(false),
        new QuHeading("More automated grid (of label/element pairs):"),
        QuestionnaireFunc::defaultGridRawPointer({
            {"<b>LHS:</b> " + lipsum2,
             new QuText("<b>RHS:</b> " + lipsum2)},
            {"<b>LHS:</b> " + lipsum2,
             new QuText("<b>RHS:</b> " + lipsum2)},
            {"<b>LHS:</b> " + lipsum2,
             new QuText("<b>RHS:</b> " + lipsum2)},
        }),
        new QuHeading("Image:"),
        new QuImage(UiFunc::iconFilename(UiConst::ICON_CAMCOPS)),
    })->setTitle("Headings, containers, text alignment, lines, images"));

    // ========================================================================
    // Audio players, countdown
    // ========================================================================

    QuPagePtr page_audio_countdown((new QuPage{
        new QuHeading("Simple audio player:"),
        (new QuAudioPlayer(UiConst::DEMO_SOUND_URL_2))->setVolume(25),
        new QuHeading("Audio player with volume control:"),
        (new QuAudioPlayer(UiConst::DEMO_SOUND_URL))->setOfferVolumeControl(),
        new QuHeading("Countdown:"),
        new QuCountdown(20),
    })->setTitle("Audio players, countdowns"));

    // ========================================================================
    // Boolean
    // ========================================================================

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
        new QuBoolean(UiFunc::iconFilename(UiConst::ICON_CAMCOPS),
                      QSize(), fieldRef("boolimage1")),
        new QuHeading("... clone with non-clickable image:"),
        (new QuBoolean(UiFunc::iconFilename(UiConst::ICON_CAMCOPS),
                      QSize(), fieldRef("boolimage1")))->setContentClickable(false),
        // Now the ACE-III address example:
        new QuContainerGrid{
            QuGridCell(new QuContainerVertical{
                (new QuContainerHorizontal{
                    aceBoolean("address_1", "booltext2"),
                    aceBoolean("address_2", "booltext3"),
                })->setAddStretchRight(true),
                (new QuContainerHorizontal{
                    aceBoolean("address_3", "booltext4"),
                    aceBoolean("address_4", "booltext5"),
                    aceBoolean("address_5", "booltext6"),
                })->setAddStretchRight(true),
                aceBoolean("address_6", "booltext7"),
                aceBoolean("address_7", "booltext8"),
            }, 0, 0),
            QuGridCell(new QuContainerVertical{
                (new QuContainerHorizontal{
                    aceBoolean("address_1", "booltext9"),
                    aceBoolean("address_2", "booltext10"),
                })->setAddStretchRight(true),
                (new QuContainerHorizontal{
                    aceBoolean("address_3", "booltext11"),
                    aceBoolean("address_4", "booltext12"),
                    aceBoolean("address_5", "booltext13"),
                })->setAddStretchRight(true),
                aceBoolean("address_6", "booltext14"),
                aceBoolean("address_7", "booltext15"),
            }, 0, 1),
            QuGridCell(new QuContainerVertical{
                (new QuContainerHorizontal{
                    aceBoolean("address_1", "booltext16"),
                    aceBoolean("address_2", "booltext17"),
                })->setAddStretchRight(true),
                (new QuContainerHorizontal{
                    aceBoolean("address_3", "booltext18"),
                    aceBoolean("address_4", "booltext19"),
                    aceBoolean("address_5", "booltext20"),
                })->setAddStretchRight(true),
                aceBoolean("address_6", "booltext21"),
                aceBoolean("address_7", "booltext22"),
            }, 1, 0),
        },
        (new QuBoolean(
            UiFunc::resourceFilename("ace3/penguin.png"),
            QSize(),
            fieldRef("boolimage2"))
        )->setBigIndicator(false),

    })->setTitle("Booleans; multiple views on a single field"));

    // ========================================================================
    // MCQ
    // ========================================================================

    NameValueOptions options_A{
        {"option_1", 1},
        {"option_2", 2},
        {"option_3, with much longer text: " + longtext, 3},
    };
    NameValueOptions options_B{
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
    NameValueOptions options_C{
        {"option_1", 1},
        {"option_2", 2},
        // {"option_NULL", QVariant()},  // will assert
        {"option_99", 99},
    };
    NameValueOptions options_D{
        {"Not at all", 0},
        {"Several days", 1},
        {"More than half the days", 2},
        {"Nearly every day", 3},
    };
    NameValueOptions options_E{
        {"A", "A"},
        {"B", "B"},
        {"C", "C"},
        {"D", "D"},
    };
    NameValueOptions options_F{
        {"X", "X"},
        {"Y", "Y"},
        {"Z", "Z"},
    };
    QuPagePtr page_mcq((new QuPage{
        new QuHeading("Plain MCQ:"),
        new QuMCQ(fieldRef("mcq1"), options_A),
        new QuHeading("Same MCQ/field, reconfigured (randomized, "
                      "instructions, horizontal, as text button):"),
        (new QuMCQ(fieldRef("mcq1"), options_A))
                            ->setRandomize(true)
                            ->setShowInstruction(true)
                            ->setHorizontal(true)
                            ->setAsTextButton(true),
        new QuHeading("Same MCQ/field, reconfigured:"),
        (new QuMCQ(fieldRef("mcq1"), options_A))
                            ->setAsTextButton(true),
        new QuHeading("A second MCQ:"),
        new QuMCQ(fieldRef("mcq2"), options_C),
        new QuHeading("Another:"),
        new QuMCQ(fieldRef("mcq3"), options_B),
        new QuHeading("The previous MCQ, reconfigured:"),
        (new QuMCQ(fieldRef("mcq3"), options_B))
                            ->setHorizontal(true),
        new QuHeading("A fourth MCQ, as text:"),
        (new QuMCQ(fieldRef("mcq4"), options_B))
                            ->setHorizontal(true)
                            ->setAsTextButton(true),
    })->setTitle("Multiple-choice questions (MCQs)"));

    // ========================================================================
    // MCQ variants
    // ========================================================================

    QuPagePtr page_mcq_variants((new QuPage{
         new QuHeading("MCQ grid:"),
         (new QuMCQGrid(
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
        (new QuMCQGrid(
            {
                QuestionWithOneField("Question A", fieldRef("mcq8")),
                QuestionWithOneField("Question B; " + lipsum2, fieldRef("mcq9")),
                QuestionWithOneField("Question C", fieldRef("mcq10")),
            },
        options_A
        ))->setTitle("MCQ 2 title; " + lipsum2),
        new QuHeading("Double MCQ grid:"),
        (new QuMCQGridDouble(
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
        (new QuMCQGridSingleBoolean(
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
        (new QuMCQGridSingleBoolean(
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

    // ========================================================================
    // Multiple responses
    // ========================================================================

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

    // ========================================================================
    // Pickers
    // ========================================================================

    QuPagePtr page_pickers((new QuPage{
        new QuHeading("Inline picker:"),
        new QuPickerInline(fieldRef("picker1"), options_A),
        new QuHeading("Its clone:"),
        new QuPickerInline(fieldRef("picker1"), options_A),
        new QuHeading("Popup picker:"),
        (new QuPickerPopup(fieldRef("picker2"), options_A))
                                ->setPopupTitle("Pickers; question 5"),
    })->setTitle("Pickers"));

    // ========================================================================
    // Sliders, thermometer
    // ========================================================================

    QList<QuThermometerItem> thermometer_items;
    for (int i = 0; i <= 10; ++i) {
        QString text = QString::number(i);
        if (i == 10) {
            text += " - very distressed";
        } else if (i == 0) {
            text += " - chilled out";
        }
        QuThermometerItem item(
            UiFunc::resourceFilename(
                        QString("distressthermometer/dt_sel_%1.png").arg(i)),
            UiFunc::resourceFilename(
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

    // ========================================================================
    // Editable variables inc. datetime
    // ========================================================================

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
        QuestionnaireFunc::defaultGridRawPointer({
            {"label 1", new QuLineEdit(fieldRef("typedvar_text"))},
            {"label 2", new QuLineEditInteger(fieldRef("typedvar_int"), 13, 19)},
            {"label 3", new QuHeading("Just a heading: " + lipsum2)},
            {"label 4", new QuDateTime(fieldRef("date_time"))},
        }, 1, 2),
    })
        ->setTitle("Editable variable including dates/times")
        ->setType(QuPage::PageType::Clinician));

    // ========================================================================
    // Diagnostic codes
    // ========================================================================

    QSharedPointer<Icd10> icd10 = QSharedPointer<Icd10>(new Icd10(m_app));
    QSharedPointer<Icd9cm> icd9cm = QSharedPointer<Icd9cm>(new Icd9cm(m_app));
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

    // ========================================================================
    // Canvas
    // ========================================================================

    QuPagePtr page_canvas((new QuPage{
        (new QuText("Page style: ClinicianWithPatient"))->italic(true),
        new QuHeading("Canvas, blank start:"),
        new QuCanvas(fieldRef("canvas2_blobid", true, true, true)),
        new QuHeading("Canvas, using files:"),
        new QuCanvas(
            fieldRef("canvas_blobid", true, true, true),
            UiFunc::resourceFilename("ace3/rhinoceros.png")),
        new QuHeading("Canvas, clone of the first one:"),
        new QuCanvas(fieldRef("canvas2_blobid", true, true, true)),
    })
        ->setTitle("Canvas")
        ->setType(QuPage::PageType::ClinicianWithPatient));

    // ========================================================================
    // Buttons
    // ========================================================================

    // Safe object lifespan signal: can use std::bind
    QuPagePtr page_buttons((new QuPage{
        new QuButton(
            "Say hello",
            std::bind(&DemoQuestionnaire::callback_hello, this)),
        new QuButton(
            "Button with args ('foo')",
            std::bind(&DemoQuestionnaire::callback_arg, this, "foo")),
        new QuButton(
            "Button with args ('bar')",
            std::bind(&DemoQuestionnaire::callback_arg, this, "bar")),
        new QuButton(
            UiConst::CBS_ADD, true, true,
            std::bind(&DemoQuestionnaire::callback_hello, this)),
    })->setTitle("Buttons"));

    // ========================================================================
    // Photo (for a mandatory photo: last page in case we have no camera)
    // ========================================================================

    QuPagePtr page_photo((new QuPage{
        new QuHeading("Photo [last page]:"),
        new QuPhoto(fieldRef("photo_blobid", true, true, true)),
    })->setTitle("Photo"));

    // ========================================================================
    // Questionnaire
    // ========================================================================

    Questionnaire* questionnaire = new Questionnaire(m_app, {
        page_text, page_headings_layout_images,
        page_audio_countdown, page_boolean,
        page_mcq, page_mcq_variants, page_multiple_response, page_pickers,
        page_sliders, page_vars, page_diag, page_canvas, page_buttons,
        page_photo,
    });
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


void initializeDemoQuestionnaire(TaskFactory& factory)
{
    static TaskRegistrar<DemoQuestionnaire> registered(factory);
}


void DemoQuestionnaire::callback_hello()
{
    UiFunc::alert("Hello!");
}


void DemoQuestionnaire::callback_arg(const QString& arg)
{
    UiFunc::alert("Function argument was: " + arg);
}


QuBoolean* DemoQuestionnaire::aceBoolean(const QString& stringname,
                                         const QString& fieldname)
{
    return (new QuBoolean(
        m_app.xstring("ace3", stringname),
        fieldRef(fieldname, false)
    ))->setBigIndicator(false);
}
