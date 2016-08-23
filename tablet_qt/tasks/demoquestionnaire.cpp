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
#include "questionnairelib/quheading.h"
#include "questionnairelib/quhorizontalline.h"
#include "questionnairelib/quimage.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"


DemoQuestionnaire::DemoQuestionnaire(const QSqlDatabase& db, int load_pk) :
    Task(db, "demoquestionnaire", false, false, false)
{
    // *** change to match previous version in terms of field names
    addField("q1", QVariant::Bool);

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
            QuElementPtr(new QuText("Text 1 (left/vcentre)" + lipsum2)),
            QuElementPtr(new QuText("Text 2 (left/vcentre)" + lipsum2)),
            QuElementPtr(new QuText("Text 3 (left/vcentre)" + lipsum2)),
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

    // *** mcq
    // *** pickers
    // *** text
    // *** datetime
    // *** slider
    // *** thermometer
    // *** diagnostic code
    // *** canvas
    // *** photo

    // ========================================================================
    // Questionnaire
    // ========================================================================

    Questionnaire* questionnaire = new Questionnaire(app, {
        p1, p2, p3, p4, p5
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
