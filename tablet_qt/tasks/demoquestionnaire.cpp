#include "demoquestionnaire.h"
#include "tasklib/taskfactory.h"

#include "questionnairelib/questionnaire.h"

#include "questionnairelib/qupage.h"
#include "questionnairelib/quelement.h"

#include "questionnairelib/qucontainerhorizontal.h"
#include "questionnairelib/qucontainervertical.h"
#include "questionnairelib/qucontainertable.h"

#include "questionnairelib/quaudioplayer.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/qubutton.h"
#include "questionnairelib/qucountdown.h"
#include "questionnairelib/qudatetime.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/quhorizontalline.h"
#include "questionnairelib/quimage.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditdouble.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
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
    qDebug() << "DemoQuestionnaire::edit()";
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
        QuElementPtr((new QuText("normal text"))->addTag("tag1")),
        QuElementPtr((new QuText("bold text"))->bold()),
        QuElementPtr((new QuText("italic text"))->italic()),
        QuElementPtr((new QuText(html))->setOpenLinks()),
        QuElementPtr((new QuText("big text"))->big()),
        QuElementPtr((new QuText("warning text"))->warning()),
        QuElementPtr(new QuText("Below here: space fillers, just to test scrolling")),
        QuElementPtr((new QuText(longtext))->big()),
    })->setTitle("Page 1: text "
                 "[With a long title: Lorem ipsum dolor sit amet, "
                 "consectetur adipiscing elit. Praesent sed cursus mauris. "
                 "Ut vulputate felis quis dolor molestie convallis.]"));
    for (int i = 0; i < 20; ++i) {
        p1->addElement(QuElementPtr((new QuText("big text"))->big()));
    }
    p1->addElement(QuElementPtr(
        (new QuText("... was that enough to scroll vertically?"))->bold()
    ));

    // ========================================================================
    // Page 2: buttons
    // ========================================================================

    QuPagePtr p2((new QuPage{
        QuElementPtr(new QuButton(
            "Say hello",
            std::bind(&DemoQuestionnaire::callback_hello, this))),
        QuElementPtr(new QuButton(
            "Button with args ('foo')",
            std::bind(&DemoQuestionnaire::callback_arg, this, "foo"))),
        QuElementPtr(new QuButton(
            "Button with args ('bar')",
            std::bind(&DemoQuestionnaire::callback_arg, this, "bar"))),
        QuElementPtr(new QuButton(
            UiConst::CBS_ADD, true, true,
            std::bind(&DemoQuestionnaire::callback_hello, this))),
    })->setTitle("Page 2: buttons"));

    // ========================================================================
    // Page 3: headings, containers, text alignment, lines, images
    // ========================================================================

    QuPagePtr p3((new QuPage{
        QuElementPtr(new QuHeading("This is a heading")),
        QuElementPtr(new QuHeading("Horizontal container:")),
        QuElementPtr(new QuContainerHorizontal{
            QuElementPtr(new QuText("Text 1 (left/vcentre) " + lipsum2)),
            QuElementPtr(new QuText("Text 2 (left/vcentre) " + lipsum2)),
            QuElementPtr(new QuText("Text 3 (left/vcentre) " + lipsum2)),
        }),
        QuElementPtr(new QuHeading("Horizontal line, line, spacer, line:")),
        QuElementPtr(new QuHorizontalLine()),
        QuElementPtr(new QuHorizontalLine()),
        QuElementPtr(new QuSpacer()),
        QuElementPtr(new QuHorizontalLine()),
        QuElementPtr(new QuHeading("Horizontal container:")),
        QuElementPtr(new QuContainerHorizontal{
            QuElementPtr((new QuText("Text 1 (right/top)"))->setAlignment(Qt::AlignRight | Qt::AlignTop)),
            QuElementPtr((new QuText("Text 2 (centre/vcentre)"))->setAlignment(Qt::AlignCenter | Qt::AlignVCenter)),
            QuElementPtr((new QuText("Text 3 (left/bottom)"))->setAlignment(Qt::AlignLeft | Qt::AlignBottom)),
            QuElementPtr(new QuText("Text 4: " + lipsum2)),
        }),
        QuElementPtr(new QuHeading("Vertical container:")),
        QuElementPtr(new QuContainerVertical{
            QuElementPtr((new QuText("Text 1 (right/top)"))->setAlignment(Qt::AlignRight | Qt::AlignTop)),
            QuElementPtr((new QuText("Text 2 (centre/vcentre)"))->setAlignment(Qt::AlignCenter | Qt::AlignVCenter)),
            QuElementPtr((new QuText("Text 3 (left/bottom)"))->setAlignment(Qt::AlignLeft | Qt::AlignBottom)),
            QuElementPtr(new QuText("Text 4: " + lipsum2)),
        }),
        QuElementPtr(new QuHeading("Table container:")),
        QuElementPtr(new QuContainerTable{
            QuTableCell(QuElementPtr(new QuText("<b>row 0, col 0:</b> " + lipsum2)), 0, 0),
            QuTableCell(QuElementPtr(new QuText("<b>row 0, col 1 [+1]:</b> " + lipsum2)), 0, 1, 1, 2),
            QuTableCell(QuElementPtr(new QuText("<b>row 1, col 0 [+1]:</b> " + lipsum2)), 1, 0, 1, 2),
            QuTableCell(QuElementPtr(new QuText("<b>row 1 [+1], col 2:</b> " + lipsum2)), 1, 2, 2, 1),
            QuTableCell(QuElementPtr(new QuText("<b>row 2, col 0:</b> " + lipsum2)), 2, 0),
            QuTableCell(QuElementPtr(new QuText("<b>row 2, col 1:</b> " + lipsum2)), 2, 1),
        }),
        QuElementPtr(new QuHeading("Image:")),
        QuElementPtr(new QuImage(UiFunc::iconFilename(UiConst::ICON_CAMCOPS))),
    })->setTitle("Page 3: headings, containers, text alignment, lines, "
                 "images"));

    // ========================================================================
    // Page 4: audio players, countdown
    // ========================================================================

    QuPagePtr p4((new QuPage{
        QuElementPtr(new QuHeading("Simple audio player:")),
        QuElementPtr((new QuAudioPlayer(UiConst::DEMO_SOUND_URL_2))->setVolume(25)),
        QuElementPtr(new QuHeading("Audio player with volume control:")),
        QuElementPtr((new QuAudioPlayer(UiConst::DEMO_SOUND_URL))->setOfferVolumeControl()),
        QuElementPtr(new QuHeading("Countdown:")),
        QuElementPtr(new QuCountdown(20)),
    })->setTitle("Page 4: audio players, countdowns"));

    // ========================================================================
    // Page 5: boolean
    // ========================================================================

    QuPagePtr p5((new QuPage{
        QuElementPtr(new QuHeading("Boolean text, not allowing ‘unset’:")),
        QuElementPtr(new QuBoolean("Click me to toggle (null → true → false → true → …)",
                      fieldRef("q1"))),
        QuElementPtr(new QuHeading("Boolean text, allowing ‘unset’, on the "
                                   "<i>same</i> field, with a smaller icon, "
                                   "and non-clickable content:")),
        QuElementPtr(
            (new QuBoolean("Click me (null → true → false → null → …)",
                           fieldRef("q1")))
            ->setBigIndicator(false)
            ->setAllowUnset()
            ->setContentClickable(false)
        ),
        QuElementPtr(new QuHeading("Text field from the Boolean field used above:")),
        QuElementPtr(new QuText(fieldRef("q1"))),
        QuElementPtr(new QuHeading("Another boolean field, using an image:")),
        QuElementPtr(new QuBoolean(UiFunc::iconFilename(UiConst::ICON_CAMCOPS),
                                   QSize(), fieldRef("q1"))),
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
    QuPagePtr p6((new QuPage{
        QuElementPtr(new QuHeading("Plain MCQ:")),
        QuElementPtr(new QuMCQ(fieldRef("q2"), options_A)),
        QuElementPtr(new QuHeading("Same MCQ/field, reconfigured (randomized, "
                      "instructions, horizontal, as text button):")),
        QuElementPtr((new QuMCQ(fieldRef("q2"), options_A))
                      ->setRandomize(true)
                      ->setShowInstruction(true)
                      ->setHorizontal(true)
                      ->setAsTextButton(true)),
        QuElementPtr(new QuHeading("Same MCQ/field, reconfigured:")),
        QuElementPtr((new QuMCQ(fieldRef("q2"), options_A))
                        ->setAsTextButton(true)),
        QuElementPtr(new QuHeading("A second MCQ:")),
        QuElementPtr(new QuMCQ(fieldRef("q4"), options_C)),
        QuElementPtr(new QuHeading("Another:")),
        QuElementPtr(new QuMCQ(fieldRef("q3"), options_B)),
        QuElementPtr(new QuHeading("The previous MCQ, reconfigured:")),
        QuElementPtr((new QuMCQ(fieldRef("q3"), options_B))
                        ->setHorizontal(true)),
        QuElementPtr(new QuHeading("The previous MCQ, as text:")),
        QuElementPtr((new QuMCQ(fieldRef("q3"), options_B))
                          ->setHorizontal(true)
                          ->setAsTextButton(true)),
    })->setTitle("Page 6: multiple-choice questions (MCQs)"));

    // ========================================================================
    // Pickers
    // ========================================================================

    QuPagePtr page_pickers((new QuPage{
        QuElementPtr(new QuHeading("Inline picker:")),
        QuElementPtr(new QuPickerInline(fieldRef("q5"), options_A)),
        QuElementPtr(new QuHeading("Its clone:")),
        QuElementPtr(new QuPickerInline(fieldRef("q5"), options_A)),
        QuElementPtr(new QuHeading("Popup picker:")),
        QuElementPtr((new QuPickerPopup(fieldRef("q5"), options_A))
                      ->setPopupTitle("Pickers; question 5")),
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
            UiFunc::imageFilename(QString("dt/dt_sel_%1.png").arg(i)),
            UiFunc::imageFilename(QString("dt/dt_unsel_%1.png").arg(i)),
            text,
            i
        );
        thermometer_items.append(item);
    }
    QuPagePtr page_sliders((new QuPage{
        QuElementPtr(new QuHeading("Integer slider:")),
        QuElementPtr((new QuSlider(fieldRef("q7"), 0, 10, 1))
                                ->setTickInterval(1)
                                ->setTickPosition(QSlider::TicksBothSides)
                                ->setShowValue(true)),
        QuElementPtr(new QuHeading("Integer slider (same field as above):")),
        QuElementPtr((new QuSlider(fieldRef("q7"), 0, 10, 1))
                                ->setShowValue(true)
                                ->setTickInterval(2)
                                ->setTickPosition(QSlider::TicksBothSides)
                                ->setUseDefaultTickLabels(true)
                                ->setTickLabelPosition(QSlider::TicksBothSides)
                                ->setHorizontal(false)),
        QuElementPtr(new QuHeading("Real/float slider:")),
        QuElementPtr((new QuSlider(fieldRef("q8"), 0, 10, 1))
                                ->setShowValue(true)
                                ->setTickInterval(1)
                                ->setTickPosition(QSlider::TicksBelow)
                                ->setConvertForRealField(true, 5, 6)),
        QuElementPtr(new QuHeading("Integer slider with custom labels:")),
        QuElementPtr((new QuSlider(fieldRef("q9"), 1, 5, 1))
                                ->setShowValue(false)
                                ->setTickInterval(1)
                                ->setTickPosition(QSlider::TicksAbove)
                                ->setTickLabelPosition(QSlider::TicksBelow)
                                ->setTickLabels({
                                    {1, "one: low"},
                                    {3, "three: medium"},
                                    {5, "five: maximum!"},
                                })
                                ->setShowValue(true)),
        QuElementPtr(new QuHeading("Thermometer:")),
        QuElementPtr((new QuThermometer(fieldRef("q7"), thermometer_items))
                                    ->setRescale(true, 0.4)),
    })->setTitle("Sliders and thermometers"));

    // ========================================================================
    // Editable variables inc. datetime
    // ========================================================================

    QuPagePtr page_vars((new QuPage{
        QuElementPtr(new QuHeading("Date/time:")),
        QuElementPtr(new QuDateTime(fieldRef("q10"))),
        QuElementPtr(new QuHeading("Date/time (custom format):")),
        QuElementPtr((new QuDateTime(fieldRef("q10")))
                             ->setMode(QuDateTime::CustomDateTime)
                             ->setCustomFormat("yyyy MM dd HH:mm:ss:zzz")),
        QuElementPtr(new QuHeading("Date:")),
        QuElementPtr((new QuDateTime(fieldRef("q11")))
                             ->setMode(QuDateTime::DefaultDate)),
        QuElementPtr(new QuHeading("Date (custom format):")),
        QuElementPtr((new QuDateTime(fieldRef("q11")))
                             ->setMode(QuDateTime::CustomDate)
                             ->setCustomFormat("yyyy MM dd")),
        QuElementPtr(new QuHeading("Time:")),
        QuElementPtr((new QuDateTime(fieldRef("q12")))
                             ->setMode(QuDateTime::DefaultTime)),
        QuElementPtr(new QuHeading("Time (custom format):")),
        QuElementPtr((new QuDateTime(fieldRef("q12")))
                             ->setMode(QuDateTime::CustomTime)
                             ->setCustomFormat("HH:mm:ss")),
        QuElementPtr(new QuHeading("Integer spinbox (range 5–10):")),
        QuElementPtr(new QuSpinBoxInteger(fieldRef("q13"), 5, 10)),
        QuElementPtr(new QuHeading("Double spinbox (range 7.1–7.9):")),
        QuElementPtr(new QuSpinBoxDouble(fieldRef("q14"), 7.1, 7.9)),
        QuElementPtr(new QuHeading("Text editor (plain text):")),
        QuElementPtr(new QuTextEdit(fieldRef("q15"), false)),
        QuElementPtr(new QuHeading("Text editor (clone of previous):")),
        QuElementPtr(new QuTextEdit(fieldRef("q15"), false)),
        QuElementPtr(new QuHeading("Text editor (rich text):")),
        QuElementPtr((new QuTextEdit(fieldRef("q16"), true))
                    ->setHint("This one has a hint (placeholder text)")),
        QuElementPtr(new QuHeading("Line editor (plain):")),
        QuElementPtr((new QuLineEdit(fieldRef("q17")))
                             ->setHint("hint: plain text")),
        QuElementPtr(new QuHeading("Line editor (integer, range 13–19):")),
        QuElementPtr((new QuLineEditInteger(fieldRef("q18"), 13, 19))
                             ->setHint("hint: integer, range 13–19")),
        QuElementPtr(new QuHeading("Line editor (double, range -0.05–-0.09, 2dp):")),
        QuElementPtr((new QuLineEditDouble(fieldRef("q19"), -0.05, -0.09, 2))
                             ->setHint("hint: double")),
    })->setTitle("Editable variable including dates/times"));

    // ========================================================================
    // *** diagnostic code
    // ========================================================================

    // ========================================================================
    // *** canvas
    // ========================================================================

    // ========================================================================
    // *** photo
    // ========================================================================

    // ========================================================================
    // Questionnaire
    // ========================================================================

    Questionnaire* questionnaire = new Questionnaire(app, {
        p1, p2, p3, p4, p5, p6, page_pickers,
        page_sliders, page_vars,
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
