#include "demoquestionnaire.h"
#include "diagnosis/icd10.h"
#include "diagnosis/icd9cm.h"
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
#include "questionnairelib/qumultipleresponse.h"
#include "questionnairelib/quphoto.h"
#include "questionnairelib/qupickerinline.h"
#include "questionnairelib/qupickerpopup.h"
#include "questionnairelib/quslider.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/quspinboxinteger.h"
#include "questionnairelib/quspinboxdouble.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "questionnairelib/quthermometer.h"


DemoQuestionnaire::DemoQuestionnaire(const QSqlDatabase& db, int load_pk) :
    Task(db, "demoquestionnaire", false, false, false)
{
    // *** change to match previous version in terms of field names
    addField("q1", QVariant::Bool);
    addField("q2", QVariant::Int);
    addField("q3", QVariant::Int);
    addField("q4", QVariant::Int);
    addField("q5", QVariant::Int);
    addField("q6", QVariant::Int);
    addField("q7", QVariant::Int);
    addField("q8", QVariant::Double);
    addField("q9", QVariant::Int);
    addField("q10", QVariant::DateTime);
    addField("q11", QVariant::Date);
    addField("q12", QVariant::Time);
    addField("q13", QVariant::Int);
    addField("q14", QVariant::Double);
    addField("q15", QVariant::String);
    addField("q16", QVariant::String);
    addField("q17", QVariant::String);
    addField("q18", QVariant::Int);
    addField("q19", QVariant::Double);
    addField("q20a", QVariant::Bool);
    addField("q20b", QVariant::Bool);
    addField("q20c", QVariant::Bool);
    addField("q20d", QVariant::Bool);
    addField("q20e", QVariant::Bool);
    addField("q21", QVariant::ByteArray);
    addField("q22", QVariant::ByteArray);
    addField("q23", QVariant::ByteArray);
    addField("q24", QVariant::String);
    addField("q25", QVariant::String);
    addField("q26", QVariant::String);
    addField("q27", QVariant::String);

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


OpenableWidget* DemoQuestionnaire::editor(CamcopsApp& app, bool read_only)
{
    qDebug() << Q_FUNC_INFO;
    QString longtext = (  // http://www.lipsum.com/
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent "
        "sed cursus mauris. Ut vulputate felis quis dolor molestie convallis. "
        "Donec lectus diam, accumsan quis tortor at, congue laoreet augue. Ut "
        "mollis consectetur elit sit amet tincidunt. Vivamus facilisis, mi et "
        "eleifend ullamcorper, lorem metus faucibus ante, ut commodo urna "
        "neque bibendum magna. Lorem ipsum dolor sit amet, consectetur "
        "adipiscing elit. Praesent nec nisi ante. Sed vitae sem et eros "
        "elementum condimentum. Proin porttitor purus justo, sit amet "
        "vulputate velit imperdiet nec. Nam posuere ipsum id nunc accumsan "
        "tristique. Etiam pellentesque ornare tortor, a scelerisque dui "
        "accumsan ac. Ut tincidunt dolor ultrices, placerat urna nec, "
        "scelerisque mi."
    );
    QString lipsum2 = "Nunc vitae neque eu odio feugiat consequat ac id neque."
                      " Suspendisse id libero massa.";
    QString url = "http://doc.qt.io/qt-5.7/richtext-html-subset.html";
    QString html = QString(
        "Text with embedded HTML markup, providing <b>bold</b>, "
        "<i>italic</i>, and others as per Qt rich text syntax at "
        "<a href=\"%1\">%1</a>."
    ).arg(url);

    // ========================================================================
    // Page 1: text
    // ========================================================================

    QuPagePtr p1((new QuPage{
        (new QuText("normal text"))->addTag("tag1"),
        (new QuText("bold text"))->bold(),
        (new QuText("italic text"))->italic(),
        (new QuText(html))->setOpenLinks(),
        (new QuText("big text"))->big(),
        (new QuText("warning text"))->warning(),
        new QuText("Below here: space fillers, just to test scrolling"),
        (new QuText(longtext))->big(),
    })->setTitle("Page 1: text "
                 "[With a long title: Lorem ipsum dolor sit amet, "
                 "consectetur adipiscing elit. Praesent sed cursus mauris. "
                 "Ut vulputate felis quis dolor molestie convallis.]"));
    for (int i = 0; i < 20; ++i) {
        p1->addElement((new QuText("big text"))->big());
    }
    p1->addElement(
        (new QuText("... was that enough to scroll vertically?"))->bold()
    );

    // ========================================================================
    // Page 2: buttons
    // ========================================================================

    QuPagePtr p2((new QuPage{
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
    })->setTitle("Page 2: buttons"));

    // ========================================================================
    // Page 3: headings, containers, text alignment, lines, images
    // ========================================================================

    QuPagePtr p3((new QuPage{
        new QuHeading("This is a heading"),
        new QuHeading("Horizontal container:"),
        new QuContainerHorizontal{
            new QuText("Text 1 (left/vcentre) " + lipsum2),
            new QuText("Text 2 (left/vcentre) " + lipsum2),
            new QuText("Text 3 (left/vcentre) " + lipsum2),
        },
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
        new QuHeading("Another grid:"),
        new QuContainerGrid{
            QuGridCell(new QuText("<b>r0 c0</b> " + lipsum2), 0, 0, 1, 1),
            QuGridCell(new QuText("<b>r0 c1 [+1]</b> " + lipsum2), 0, 1, 1, 2),
            QuGridCell(new QuText("<b>r1 c0</b> " + lipsum2), 1, 0, 1, 1),
            QuGridCell(new QuText("<b>r1 c1 [+1]</b> " + lipsum2), 1, 1, 1, 2),
        },
        new QuHeading("Another grid:"),
        new QuContainerGrid{
            QuGridCell(new QuText("<b>r0 c0</b> " + lipsum2), 0, 0),
            QuGridCell(new QuText("<b>r0 c1</b> " + lipsum2), 0, 1),
            QuGridCell(new QuText("<b>r1 c0</b> " + lipsum2), 1, 0),
            QuGridCell(new QuText("<b>r1 c1</b> " + lipsum2), 1, 1),
        },
        new QuHeading("More automated grid (of label/element pairs):"),
        QuestionnaireFunc::defaultGridRawPointer({
            {lipsum2, new QuText(lipsum2)},
            {lipsum2, new QuText(lipsum2)},
            {lipsum2, new QuText(lipsum2)},
        }),
        new QuHeading("Image:"),
        new QuImage(UiFunc::iconFilename(UiConst::ICON_CAMCOPS)),
    })->setTitle("Page 3: headings, containers, text alignment, lines, "
                 "images"));

    // ========================================================================
    // Page 4: audio players, countdown
    // ========================================================================

    QuPagePtr p4((new QuPage{
        new QuHeading("Simple audio player:"),
        (new QuAudioPlayer(UiConst::DEMO_SOUND_URL_2))->setVolume(25),
        new QuHeading("Audio player with volume control:"),
        (new QuAudioPlayer(UiConst::DEMO_SOUND_URL))->setOfferVolumeControl(),
        new QuHeading("Countdown:"),
        new QuCountdown(20),
    })->setTitle("Page 4: audio players, countdowns"));

    // ========================================================================
    // Page 5: boolean
    // ========================================================================

    QuPagePtr p5((new QuPage{
        new QuHeading("Boolean text, not allowing ‘unset’:"),
        new QuBoolean("Click me to toggle (null → true → false → true → …)",
                      fieldRef("q1")),
        new QuHeading("Boolean text, allowing ‘unset’, on the "
                                   "<i>same</i> field, with a smaller icon, "
                                   "and non-clickable content:"),
        (new QuBoolean("Click me (null → true → false → null → …)",
                      fieldRef("q1")))
                      ->setBigIndicator(false)
                      ->setAllowUnset()
                      ->setContentClickable(false),
        new QuHeading("Text field from the Boolean field used above:"),
        new QuText(fieldRef("q1")),
        new QuHeading("Another boolean field, using an image:"),
        new QuBoolean(UiFunc::iconFilename(UiConst::ICON_CAMCOPS),
                      QSize(), fieldRef("q1")),
    })->setTitle("Page 5: booleans; multiple views on a single field"));

    // ========================================================================
    // Page 5: MCQ
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
    QuPagePtr page_mcq((new QuPage{
        new QuHeading("Plain MCQ:"),
        new QuMCQ(fieldRef("q2"), options_A),
        new QuHeading("Same MCQ/field, reconfigured (randomized, "
                      "instructions, horizontal, as text button):"),
        (new QuMCQ(fieldRef("q2"), options_A))
                            ->setRandomize(true)
                            ->setShowInstruction(true)
                            ->setHorizontal(true)
                            ->setAsTextButton(true),
        new QuHeading("Same MCQ/field, reconfigured:"),
        (new QuMCQ(fieldRef("q2"), options_A))
                            ->setAsTextButton(true),
        new QuHeading("A second MCQ:"),
        new QuMCQ(fieldRef("q4"), options_C),
        new QuHeading("Another:"),
        new QuMCQ(fieldRef("q3"), options_B),
        new QuHeading("The previous MCQ, reconfigured:"),
        (new QuMCQ(fieldRef("q3"), options_B))
                            ->setHorizontal(true),
        new QuHeading("The previous MCQ, as text:"),
        (new QuMCQ(fieldRef("q3"), options_B))
                            ->setHorizontal(true)
                            ->setAsTextButton(true),
    })->setTitle("Multiple-choice questions (MCQs)"));

    // ========================================================================
    // Multiple responses
    // ========================================================================

    QuPagePtr page_multiple_response((new QuPage{
        QuElementPtr((new QuMultipleResponse({
            QuMultipleResponseItem(fieldRef("q20a"), "(a) First stem"),
            QuMultipleResponseItem(fieldRef("q20b"), "(b) First stem"),
            QuMultipleResponseItem(fieldRef("q20c"), "(c) First stem"),
            QuMultipleResponseItem(fieldRef("q20d"), "(d) First stem"),
            QuMultipleResponseItem(fieldRef("q20e"), "(e) First stem"),
        }))->setMinimumAnswers(2)->setMaximumAnswers(3)),
    })->setTitle("Multiple-response questions"));

    // ========================================================================
    // Pickers
    // ========================================================================

    QuPagePtr page_pickers((new QuPage{
        new QuHeading("Inline picker:"),
        new QuPickerInline(fieldRef("q5"), options_A),
        new QuHeading("Its clone:"),
        new QuPickerInline(fieldRef("q5"), options_A),
        new QuHeading("Popup picker:"),
        (new QuPickerPopup(fieldRef("q5"), options_A))
                                ->setPopupTitle("Pickers; question 5"),
    })->setTitle("Pickers"));

    // ========================================================================
    // *** MCQ variants
    // ========================================================================

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
        (new QuSlider(fieldRef("q7"), 0, 10, 1))
                                ->setTickInterval(1)
                                ->setTickPosition(QSlider::TicksBothSides)
                                ->setShowValue(true),
        new QuHeading("Integer slider (same field as above):"),
        (new QuSlider(fieldRef("q7"), 0, 10, 1))
                                ->setShowValue(true)
                                ->setTickInterval(2)
                                ->setTickPosition(QSlider::TicksBothSides)
                                ->setUseDefaultTickLabels(true)
                                ->setTickLabelPosition(QSlider::TicksBothSides)
                                ->setHorizontal(false),
        new QuHeading("Real/float slider:"),
        (new QuSlider(fieldRef("q8"), 0, 10, 1))
                                ->setShowValue(true)
                                ->setTickInterval(1)
                                ->setTickPosition(QSlider::TicksBelow)
                                ->setConvertForRealField(true, 5, 6),
        new QuHeading("Integer slider with custom labels:"),
        (new QuSlider(fieldRef("q9"), 1, 5, 1))
                                ->setShowValue(false)
                                ->setTickInterval(1)
                                ->setTickPosition(QSlider::TicksAbove)
                                ->setTickLabelPosition(QSlider::TicksBelow)
                                ->setTickLabels({
                                    {1, "one: low"},
                                    {3, "three: medium"},
                                    {5, "five: maximum!"},
                                })
                                ->setShowValue(true),
        new QuHeading("Thermometer:"),
        (new QuThermometer(fieldRef("q7"), thermometer_items))
                                ->setRescale(true, 0.4),
    })->setTitle("Sliders and thermometers"));

    // ========================================================================
    // Editable variables inc. datetime
    // ========================================================================

    QuPagePtr page_vars((new QuPage{
        new QuHeading("Date/time:"),
        new QuDateTime(fieldRef("q10")),
        new QuHeading("Date/time (custom format):"),
        (new QuDateTime(fieldRef("q10")))
                             ->setMode(QuDateTime::CustomDateTime)
                             ->setCustomFormat("yyyy MM dd HH:mm:ss:zzz"),
        new QuHeading("Date:"),
        (new QuDateTime(fieldRef("q11")))
                             ->setMode(QuDateTime::DefaultDate),
        new QuHeading("Date (custom format):"),
        (new QuDateTime(fieldRef("q11")))
                             ->setMode(QuDateTime::CustomDate)
                             ->setCustomFormat("yyyy MM dd"),
        new QuHeading("Time:"),
        (new QuDateTime(fieldRef("q12")))
                             ->setMode(QuDateTime::DefaultTime),
        new QuHeading("Time (custom format):"),
        (new QuDateTime(fieldRef("q12")))
                             ->setMode(QuDateTime::CustomTime)
                             ->setCustomFormat("HH:mm:ss"),
        new QuHeading("Integer spinbox (range 5–10):"),
        new QuSpinBoxInteger(fieldRef("q13"), 5, 10),
        new QuHeading("Double spinbox (range 7.1–7.9):"),
        new QuSpinBoxDouble(fieldRef("q14"), 7.1, 7.9),
        new QuHeading("Text editor (plain text):"),
        new QuTextEdit(fieldRef("q15"), false),
        new QuHeading("Text editor (clone of previous):"),
        new QuTextEdit(fieldRef("q15"), false),
        new QuHeading("Text editor (rich text):"),
        (new QuTextEdit(fieldRef("q16"), true))
                             ->setHint("This one has a hint "
                                       "(placeholder text)"),
        new QuHeading("Line editor (plain):"),
        (new QuLineEdit(fieldRef("q17")))
                             ->setHint("hint: plain text"),
        new QuHeading("Line editor (integer, range 13–19):"),
        (new QuLineEditInteger(fieldRef("q18"), 13, 19))
                             ->setHint("hint: integer, range 13–19"),
        new QuHeading("Line editor (double, "
                             "range -0.05 to -0.09, 2dp):"),
        (new QuLineEditDouble(fieldRef("q19"), -0.05, -0.09, 2))
                             ->setHint("hint: double"),
        new QuHeading("Variables in a grid:"),
        QuestionnaireFunc::defaultGridRawPointer({
            {"label 1", new QuLineEdit(fieldRef("q17"))},
            {"label 2", new QuLineEditInteger(fieldRef("q18"), 13, 19)},
            {"label 3", new QuHeading("Just a heading: " + lipsum2)},
            {"label 4", new QuDateTime(fieldRef("q10"))},
        }, 1, 2),
    })->setTitle("Editable variable including dates/times"));

    // ========================================================================
    // Diagnostic codes
    // ========================================================================

    QSharedPointer<Icd10> icd10 = QSharedPointer<Icd10>(new Icd10(app));
    QSharedPointer<Icd9cm> icd9cm = QSharedPointer<Icd9cm>(new Icd9cm(app));
    QuPagePtr page_diag((new QuPage{
        new QuHeading("Diagnostic code, ICD-10:"),
        new QuDiagnosticCode(icd10, fieldRef("q24"), fieldRef("q25")),
        new QuHeading("Diagnostic code, clone of the preceding:"),
        new QuDiagnosticCode(icd10, fieldRef("q24"), fieldRef("q25")),
        new QuHeading("Diagnostic code, ICD-9-CM:"),
        new QuDiagnosticCode(icd9cm, fieldRef("q26"), fieldRef("q27")),
    })->setTitle("Canvas"));

    // ========================================================================
    // Canvas
    // ========================================================================

    QuPagePtr page_canvas((new QuPage{
        new QuHeading("Canvas, blank start:"),
        new QuCanvas(fieldRef("q21")),
        new QuHeading("Canvas, using files:"),
        new QuCanvas(
            fieldRef("q22"),
            UiFunc::resourceFilename("ace3/rhinoceros.png")),
        new QuHeading("Canvas, clone of the first one:"),
        new QuCanvas(fieldRef("q21")),
    })->setTitle("Canvas"));

    // ========================================================================
    // Photo
    // ========================================================================

    QuPagePtr page_photo((new QuPage{
        new QuHeading("Photo:"),
        new QuPhoto(fieldRef("q23")),
    })->setTitle("Canvas"));

    // ========================================================================
    // Questionnaire
    // ========================================================================

    Questionnaire* questionnaire = new Questionnaire(app, {
        p1, p2, p3, p4, p5,
        page_mcq, page_multiple_response, page_pickers,
        page_sliders, page_vars, page_diag, page_canvas, page_photo,
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
