/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

// #define DEBUG_BIG_HEADER_ONLY_PAGE
// #define DEBUG_DIAGNOSTIC_SET_CREATION_SPEED
// #define DEBUG_DISABLE_MOST_SLIDERS

#include "demoquestionnaire.h"

#include "common/textconst.h"
#include "common/uiconst.h"
#include "core/camcopsapp.h"
#include "diagnosis/icd10.h"
#include "diagnosis/icd9cm.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/quaudioplayer.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/qubutton.h"
#include "questionnairelib/qucanvas.h"
#include "questionnairelib/qucountdown.h"
#include "questionnairelib/qudatetime.h"
#include "questionnairelib/qudiagnosticcode.h"
#include "questionnairelib/quelement.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/quflowcontainer.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/quhorizontalcontainer.h"
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
#include "questionnairelib/qupage.h"
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
#include "questionnairelib/quverticalcontainer.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"

const QString DemoQuestionnaire::DEMOQUESTIONNAIRE_TABLENAME(
    QStringLiteral("demoquestionnaire")
);

const int SOUNDTEST_1_VOLUME = 50;

void initializeDemoQuestionnaire(TaskFactory& factory)
{
    static TaskRegistrar<DemoQuestionnaire> registered(factory);
}

DemoQuestionnaire::DemoQuestionnaire(
    CamcopsApp& app, DatabaseManager& db, const int load_pk
) :
    Task(app, db, DEMOQUESTIONNAIRE_TABLENAME, true, false, false)
{
    using stringfunc::strseq;

    addFields(
        strseq(QStringLiteral("mcq"), 1, 10), QMetaType::fromType<int>()
    );
    // ... 9-10: v2
    addFields(
        strseq(QStringLiteral("mcqbool"), 1, 3), QMetaType::fromType<bool>()
    );
    addFields(
        strseq(QStringLiteral("multipleresponse"), 1, 6),
        QMetaType::fromType<bool>()
    );
    addFields(
        strseq(QStringLiteral("booltext"), 1, 22), QMetaType::fromType<bool>()
    );
    addFields(
        strseq(QStringLiteral("boolimage"), 1, 2), QMetaType::fromType<bool>()
    );
    addFields(
        strseq(QStringLiteral("slider"), 1, 2), QMetaType::fromType<double>()
    );
    addFields(
        strseq(QStringLiteral("picker"), 1, 2), QMetaType::fromType<int>()
    );
    addFields(
        strseq(QStringLiteral("mcqtext_"), 1, 3, {"a", "b"}),
        QMetaType::fromType<QString>()
    );
    addField(QStringLiteral("typedvar_text"), QMetaType::fromType<QString>());
    addField(
        QStringLiteral("typedvar_text_multiline"),
        QMetaType::fromType<QString>()
    );
    addField(
        QStringLiteral("typedvar_text_rich"), QMetaType::fromType<QString>()
    );
    // ... v2
    addField(QStringLiteral("typedvar_int"), QMetaType::fromType<int>());
    addField(QStringLiteral("typedvar_real"), QMetaType::fromType<double>());
    addField(QStringLiteral("spinbox_int"), QMetaType::fromType<int>());
    // ... v2
    addField(QStringLiteral("spinbox_real"), QMetaType::fromType<double>());
    // ... v2
    addField(QStringLiteral("date_time"), QMetaType::fromType<QDateTime>());
    addField(QStringLiteral("date_only"), QMetaType::fromType<QDate>());
    addField(QStringLiteral("time_only"), QMetaType::fromType<QTime>());
    // ... v2
    addField(QStringLiteral("thermometer"), QMetaType::fromType<int>());
    addField(
        QStringLiteral("diagnosticcode_code"), QMetaType::fromType<QString>()
    );
    addField(
        QStringLiteral("diagnosticcode_description"),
        QMetaType::fromType<QString>()
    );
    addField(
        QStringLiteral("diagnosticcode2_code"), QMetaType::fromType<QString>()
    );
    // ... v2
    addField(
        QStringLiteral("diagnosticcode2_description"),
        QMetaType::fromType<QString>()
    );
    // ... v2
    addField(QStringLiteral("photo_blobid"), QMetaType::fromType<int>());
    // ... FK to BLOB table
    // addField(QStringLiteral("photo_rotation"),
    //          QMetaType::fromType<QString>());  // DEFUNCT in v2
    addField(QStringLiteral("canvas_blobid"), QMetaType::fromType<int>());
    // ... FK to BLOB table
    addField(QStringLiteral("canvas2_blobid"), QMetaType::fromType<int>());
    // ... FK to BLOB table; v2

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class overrides
// ============================================================================

QString DemoQuestionnaire::shortname() const
{
    return QStringLiteral("Demo");
}

QString DemoQuestionnaire::longname() const
{
    return tr("Demonstration task");
}

QString DemoQuestionnaire::description() const
{
    return tr("Tutorial and illustration of questionnaire task elements.");
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
    return QStringList{tr("Demonstration questionnaire; no summary")};
}

OpenableWidget* DemoQuestionnaire::editor(const bool read_only)
{
    const QString& longtext = TextConst::LOREM_IPSUM_1;
    const QString& lipsum2 = TextConst::LOREM_IPSUM_2;
    const QString url(
        QStringLiteral("https://doc.qt.io/qt-6.5/richtext-html-subset.html")
    );
    const QString html(
        tr("Text with embedded HTML markup, providing <b>bold</b>, "
           "<i>italic</i>, and others as per Qt rich text syntax at "
           "<a href=\"%1\">%1</a>.")
            .arg(url)
    );

    // ------------------------------------------------------------------------
    // Text
    // ------------------------------------------------------------------------

    QuPagePtr page_text(
        (new QuPage{
             new QuText(
                 tr("We’ll demonstrate the elements from which questionnaire"
                    " tasks can be made. Press the ‘Next’ button at the top "
                    "right of the screen.")
                 + "\n"
             ),
             (new QuText(tr("normal text")))->addTag(QStringLiteral("tag1")),
             (new QuText(tr("bold text")))->setBold(),
             (new QuText(tr("italic text")))->setItalic(),
             (new QuText(html))->setOpenLinks(),
             (new QuText(tr("big text")))->setBig(),
             (new QuText(tr("warning text")))->setWarning(),
             new QuText(tr("Below here: space fillers, just to test scrolling")
             ),
             (new QuText(longtext))->setBig(),
         })
            ->setTitle(tr("Text [With a long title: %1]")
                           .arg(TextConst::LOREM_IPSUM_3))
    );
    for (int i = 0; i < 20; ++i) {
        page_text->addElement((new QuText(tr("big text")))->setBig());
    }
    page_text->addElement(
        (new QuText(tr("... was that enough to scroll vertically?")))
            ->setBold()
    );

#ifdef DEBUG_BIG_HEADER_ONLY_PAGE
    QuPagePtr page_text_header_only(
        (new QuPage{
             new QuText(tr("Very long title, to check sizing.")),
         })
            ->setTitle(textconst::LOREM_IPSUM_1)
    );
#endif

    // ------------------------------------------------------------------------
    // Image
    // ------------------------------------------------------------------------

    QuPagePtr page_image(
        (new QuPage{
             new QuHeading(tr("Image:")),
             new QuImage(uifunc::iconFilename(uiconst::ICON_CAMCOPS)),
             new QuHeading(tr("... heading under image, to check vertical size"
             )),
         })
            ->setTitle(tr("Headings, images"))
    );

    // ------------------------------------------------------------------------
    // Headings, containers, text alignment, lines
    // ------------------------------------------------------------------------

    const Qt::Alignment bottomleft = Qt::AlignLeft | Qt::AlignBottom;
    const Qt::Alignment centre = Qt::AlignHCenter | Qt::AlignVCenter;
    const Qt::Alignment topright = Qt::AlignRight | Qt::AlignTop;

    auto horiz1 = new QuHorizontalContainer();
    horiz1->addElement((new QuText(tr("Text 1 (right/top)")))
                           ->setTextAndWidgetAlignment(topright));
    horiz1->addElement((new QuText(tr("Text 2 (centre/vcentre)")))
                           ->setTextAndWidgetAlignment(centre));
    horiz1->addElement((new QuText(tr("Text 3 (left/bottom)")))
                           ->setTextAndWidgetAlignment(bottomleft));
    horiz1->addElement(new QuText(tr("Text 4: ") + longtext));
    horiz1->setOverrideWidgetAlignment(false);
    horiz1->setAddStretchRight(false);

    auto vert1 = new QuVerticalContainer;
    vert1->addElement((new QuText(tr("Text 1 (right/top)")))
                          ->setTextAndWidgetAlignment(topright));
    vert1->addElement((new QuText(tr("Text 2 (centre/vcentre)")))
                          ->setTextAndWidgetAlignment(centre));
    vert1->addElement((new QuText(tr("Text 3 (left/bottom)")))
                          ->setTextAndWidgetAlignment(bottomleft));
    vert1->addElement(new QuText(tr("Text 4: ") + lipsum2));
    vert1->setOverrideWidgetAlignment(false);

    QuPagePtr page_headings_layout(
        (new QuPage{
             new QuHeading(tr("This is a heading")),
             new QuHeading(tr("Horizontal line, line, spacer, line:")),
             new QuHorizontalLine(),
             new QuHorizontalLine(),
             new QuSpacer(),
             new QuHorizontalLine(),
             new QuHeading(
                 tr("Flow container (generally preferred to horizontal "
                    "container; better on small screens):")
             ),
             new QuFlowContainer{
                 (new QuText(tr("Text 1 (right/top)")))
                     ->setTextAlignment(topright),
                 (new QuText(tr("Text 2 (centre/vcentre)")))
                     ->setTextAlignment(centre),
                 (new QuText(tr("Text 3 (left/bottom)")))
                     ->setTextAlignment(bottomleft),
                 new QuText(tr("Text 4: ") + lipsum2),
             },
             new QuHeading(tr("Horizontal container (with stretch on right):")
             ),
             (new QuHorizontalContainer{
                  new QuText(tr("Text 1")),
                  new QuText(tr("Text 2")),
                  new QuText(tr("Text 3")),
              })
                 ->setAddStretchRight(true),
             new QuHeading(tr("Horizontal container (without stretch on "
                              "right; blank widget alignment):")),
             (new QuHorizontalContainer{
                  (new QuText(tr("Text 1 (right/top)")))
                      ->setTextAlignment(topright),
                  (new QuText(tr("Text 2 (centre/vcentre)")))
                      ->setTextAlignment(centre),
                  (new QuText(tr("Text 3 (left/bottom)")))
                      ->setTextAlignment(bottomleft),
              })
                 ->setAddStretchRight(false)
                 ->setContainedWidgetAlignments(Qt::Alignment()),
             new QuHeading(tr("Horizontal container (no stretch on right, "
                              "showing alignments):")),
             horiz1,
             new QuHeading(tr("Vertical container:")),
             vert1,
             new QuHeading(tr("Grid container:")),
             new QuGridContainer{
                 QuGridCell(
                     new QuText("<b>row 0, col 0:</b> " + lipsum2), 0, 0
                 ),
                 QuGridCell(
                     new QuText("<b>row 0, col 1 [+1]:</b> " + lipsum2),
                     0,
                     1,
                     1,
                     2
                 ),
                 QuGridCell(
                     new QuText("<b>row 1, col 0 [+1]:</b> " + lipsum2),
                     1,
                     0,
                     1,
                     2
                 ),
                 QuGridCell(
                     new QuText(
                         "<b>row 1 [+1], col 2, with top-right alignment:</b> "
                         + lipsum2
                     ),
                     1,
                     2,
                     2,
                     1,
                     Qt::AlignRight | Qt::AlignTop
                 ),
                 QuGridCell(
                     new QuText("<b>row 2, col 0:</b> " + lipsum2), 2, 0
                 ),
                 QuGridCell(
                     new QuText("<b>row 2, col 1:</b> " + lipsum2), 2, 1
                 ),
             },
             new QuHeading(tr("Another grid (2:1 columns):")),
             (new QuGridContainer{
                  QuGridCell(
                      new QuText("<b>r0 c0</b> " + lipsum2), 0, 0, 1, 1
                  ),
                  QuGridCell(
                      new QuText("<b>r0 c1 [+1]</b> " + lipsum2), 0, 1, 1, 2
                  ),
                  QuGridCell(
                      new QuText("<b>r1 c0</b> " + lipsum2), 1, 0, 1, 1
                  ),
                  QuGridCell(
                      new QuText("<b>r1 c1 [+1]</b> " + lipsum2), 1, 1, 1, 2
                  ),
              })
                 ->setColumnStretch(0, 2)
                 ->setColumnStretch(1, 1),
             new QuHeading(tr("Another grid (5 equal columns), with image "
                              "alignment settings (L/T, HC/VC, R/B):")),
             (new QuGridContainer{
                  QuGridCell(
                      new QuImage(uifunc::iconFilename(uiconst::ICON_CAMCOPS)),
                      0,
                      0,
                      1,
                      1,
                      Qt::AlignLeft | Qt::AlignTop
                  ),
                  QuGridCell(
                      new QuText(lipsum2 + lipsum2 + lipsum2 + lipsum2),
                      0,
                      1,
                      1,
                      1
                  ),
                  QuGridCell(
                      new QuImage(uifunc::iconFilename(uiconst::ICON_CAMCOPS)),
                      0,
                      2,
                      1,
                      1,
                      Qt::AlignHCenter | Qt::AlignVCenter
                  ),
                  QuGridCell(
                      new QuText(lipsum2 + lipsum2 + lipsum2 + lipsum2),
                      0,
                      3,
                      1,
                      1
                  ),
                  QuGridCell(
                      new QuImage(uifunc::iconFilename(uiconst::ICON_CAMCOPS)),
                      0,
                      4,
                      1,
                      1,
                      Qt::AlignRight | Qt::AlignBottom
                  ),
              })
                 ->setColumnStretch(0, 1)
                 ->setColumnStretch(1, 1)
                 ->setColumnStretch(2, 1)
                 ->setColumnStretch(3, 1)
                 ->setColumnStretch(4, 1),
             new QuHeading(tr("Another grid (1:1 columns):")),
             (new QuGridContainer{
                  QuGridCell(new QuText("<b>r0 c0</b> " + lipsum2), 0, 0),
                  QuGridCell(new QuText("<b>r0 c1</b> " + lipsum2), 0, 1),
                  QuGridCell(new QuText("<b>r1 c0</b> " + lipsum2), 1, 0),
                  QuGridCell(new QuText("<b>r1 c1</b> " + lipsum2), 1, 1),
              })
                 ->setColumnStretch(0, 1)
                 ->setColumnStretch(1, 1),
             new QuHeading(
                 tr("Another grid (1:1:1 columns, expanding horizontally, "
                    "fixed column style = default):")
             ),
             (new QuGridContainer{
                  QuGridCell(new QuText(tr("1. Short")), 0, 0),
                  QuGridCell(new QuText(tr("2. Medium sort of length")), 0, 1),
                  QuGridCell(new QuText(tr("3. Longer ") + lipsum2), 0, 2),
              })
                 ->setColumnStretch(0, 1)
                 ->setColumnStretch(1, 1)
                 ->setColumnStretch(2, 1)
                 ->setExpandHorizontally(true)
                 ->setFixedGrid(true),
             new QuHeading(tr("Another grid (1:1:1 columns, non-expanding, "
                              "non-fixed style):")),
             (new QuGridContainer{
                  QuGridCell(new QuText(tr("1. Short")), 0, 0),
                  QuGridCell(new QuText(tr("2. Medium sort of length")), 0, 1),
                  QuGridCell(new QuText(tr("3. Longer ") + lipsum2), 0, 2),
              })
                 ->setColumnStretch(0, 1)
                 ->setColumnStretch(1, 1)
                 ->setColumnStretch(2, 1)
                 ->setExpandHorizontally(false)
                 ->setFixedGrid(false),
             new QuHeading(tr("More automated grid (of label/element pairs):")
             ),
             questionnairefunc::defaultGridRawPointer({
                 {"<b>LHS:</b> " + lipsum2,
                  new QuText("<b>RHS:</b> " + lipsum2)},
                 {"<b>LHS:</b> " + lipsum2,
                  new QuText("<b>RHS:</b> " + lipsum2)},
                 {"<b>LHS:</b> " + lipsum2,
                  new QuText("<b>RHS:</b> " + lipsum2)},
             }),
         })
            ->setTitle(tr("Headings, containers, text alignment, lines"))
    );

    // ------------------------------------------------------------------------
    // Audio players, countdown
    // ------------------------------------------------------------------------

    QuPagePtr page_audio_countdown(
        (new QuPage{
             new QuHeading(tr("Simple audio player:")),
             new QuText(tr("Excerpt from Mozart WA, <i>Vesperae solennes de "
                           "confessore</i> "
                           "(K.339), fifth movement, <i>Laudate Dominum</i>, "
                           "by the Advent "
                           "Chamber Orchestra (see docs).")),
             (new QuAudioPlayer(uiconst::DEMO_SOUND_URL_2))
                 ->setVolume(SOUNDTEST_1_VOLUME),
             new QuHeading(tr("Audio player with volume control:")),
             new QuText(tr(
                 "Excerpt from Bach JS, <i>Brandenburg Concerto No. 3, third "
                 "movement (Allegro)</i>, by the Advent Chamber Orchestra "
                 "(see docs)."
             )),
             (new QuAudioPlayer(uiconst::DEMO_SOUND_URL_1))
                 ->setOfferVolumeControl(),
             new QuHeading(tr("Countdown:")),
             new QuCountdown(20),
         })
            ->setTitle(tr("Audio players, countdowns"))
    );

    // ------------------------------------------------------------------------
    // Boolean
    // ------------------------------------------------------------------------

    const QString booltext1(QStringLiteral("booltext1"));
    const QString boolimage1(QStringLiteral("boolimage1"));
    QuPagePtr page_boolean(
        (new QuPage{
             new QuText(tr("On this page, some questions must be completed "
                           "before the ‘Next’ "
                           "button appears. <b>Make the yellow disappear to "
                           "continue!</b>")),
             new QuHeading(
                 tr("Boolean text, not allowing ‘unset’, with clickable "
                    "content:")
             ),
             new QuBoolean(
                 tr("Click me to toggle (null → true → false → true → …)"),
                 fieldRef(booltext1)
             ),
             new QuHeading(tr("Boolean text, allowing ‘unset’, on the "
                              "<i>same</i> field, with a smaller icon, "
                              "and non-clickable content:")),
             (new QuBoolean(
                  tr("Click me (null → true → false → null → …)"),
                  fieldRef(booltext1)
              ))
                 ->setBigIndicator(false)
                 ->setAllowUnset()
                 ->setContentClickable(false),
             new QuHeading(tr("Same field, with text-style widget:")),
             (new QuBoolean(tr("Boolean-as-text"), fieldRef(booltext1)))
                 ->setAsTextButton(),
             new QuHeading(tr("Text field from the Boolean field used above:")
             ),
             new QuText(fieldRef(booltext1)),
             new QuHeading(tr("Another boolean field, using an image:")),
             new QuBoolean(
                 uifunc::iconFilename(uiconst::ICON_CAMCOPS),
                 QSize(),
                 fieldRef(boolimage1)
             ),
             new QuHeading(tr("... clone with non-clickable image:")),
             (new QuBoolean(
                  uifunc::iconFilename(uiconst::ICON_CAMCOPS),
                  QSize(),
                  fieldRef(boolimage1)
              ))
                 ->setContentClickable(false),
             // Now the ACE-III address example:
             new QuGridContainer{
                 QuGridCell(
                     new QuVerticalContainer{
                         new QuFlowContainer{
                             aceBoolean(
                                 QStringLiteral("address_1"),
                                 QStringLiteral("booltext2")
                             ),
                             aceBoolean(
                                 QStringLiteral("address_2"),
                                 QStringLiteral("booltext3")
                             ),
                         },
                         new QuFlowContainer{
                             aceBoolean(
                                 QStringLiteral("address_3"),
                                 QStringLiteral("booltext4")
                             ),
                             aceBoolean(
                                 QStringLiteral("address_4"),
                                 QStringLiteral("booltext5")
                             ),
                             aceBoolean(
                                 QStringLiteral("address_5"),
                                 QStringLiteral("booltext6")
                             ),
                         },
                         aceBoolean(
                             QStringLiteral("address_6"),
                             QStringLiteral("booltext7")
                         ),
                         aceBoolean(
                             QStringLiteral("address_7"),
                             QStringLiteral("booltext8")
                         ),
                     },
                     0,
                     0
                 ),
                 QuGridCell(
                     new QuVerticalContainer{
                         new QuFlowContainer{
                             aceBoolean(
                                 QStringLiteral("address_1"),
                                 QStringLiteral("booltext9")
                             ),
                             aceBoolean(
                                 QStringLiteral("address_2"),
                                 QStringLiteral("booltext10")
                             ),
                         },
                         new QuFlowContainer{
                             aceBoolean(
                                 QStringLiteral("address_3"),
                                 QStringLiteral("booltext11")
                             ),
                             aceBoolean(
                                 QStringLiteral("address_4"),
                                 QStringLiteral("booltext12")
                             ),
                             aceBoolean(
                                 QStringLiteral("address_5"),
                                 QStringLiteral("booltext13")
                             ),
                         },
                         aceBoolean(
                             QStringLiteral("address_6"),
                             QStringLiteral("booltext14")
                         ),
                         aceBoolean(
                             QStringLiteral("address_7"),
                             QStringLiteral("booltext15")
                         ),
                     },
                     0,
                     1
                 ),
                 QuGridCell(
                     new QuVerticalContainer{
                         new QuFlowContainer{
                             aceBoolean(
                                 QStringLiteral("address_1"),
                                 QStringLiteral("booltext16")
                             ),
                             aceBoolean(
                                 QStringLiteral("address_2"),
                                 QStringLiteral("booltext17")
                             ),
                         },
                         new QuFlowContainer{
                             aceBoolean(
                                 QStringLiteral("address_3"),
                                 QStringLiteral("booltext18")
                             ),
                             aceBoolean(
                                 QStringLiteral("address_4"),
                                 QStringLiteral("booltext19")
                             ),
                             aceBoolean(
                                 QStringLiteral("address_5"),
                                 QStringLiteral("booltext20")
                             ),
                         },
                         aceBoolean(
                             QStringLiteral("address_6"),
                             QStringLiteral("booltext21")
                         ),
                         aceBoolean(
                             QStringLiteral("address_7"),
                             QStringLiteral("booltext22")
                         ),
                     },
                     1,
                     0
                 ),
             },
             (new QuBoolean(
                  uifunc::resourceFilename("ace3/penguin.png"),
                  QSize(),
                  fieldRef(QStringLiteral("boolimage2"))
              ))
                 ->setBigIndicator(false),

         })
            ->setTitle(tr("Booleans; multiple views on a single field"))
    );

    // ------------------------------------------------------------------------
    // MCQ
    // ------------------------------------------------------------------------

    const QString soption(tr("option"));
    auto makeoptn = [&soption](int n) {
        return QString(QStringLiteral("%1_%2"))
            .arg(soption, QString::number(n));
    };
    const NameValueOptions options_A{
        {makeoptn(1), 1},
        {makeoptn(2), 2},
        {makeoptn(3) + ", " + tr("with much longer text: ") + longtext, 3},
    };
    const NameValueOptions options_B{
        {makeoptn(1), 1},
        {makeoptn(2), 2},
        {makeoptn(3), 3},
        {makeoptn(4), 4},
        {makeoptn(5), 5},
        {makeoptn(6), 6},
        {makeoptn(7), 7},
        {makeoptn(8), 8},
        {makeoptn(9), 9},
        {makeoptn(10), 10},
        {makeoptn(11), 11},
        {makeoptn(12), 12},
        {makeoptn(13), 13},
        {makeoptn(14), 14},
        {makeoptn(15), 15},
        {makeoptn(16), 16},
        {makeoptn(17), 17},
    };
    const NameValueOptions options_C{
        {makeoptn(1), 1},
        {makeoptn(2), 2},
        // {"option_NULL", QVariant()},  // will assert
        {makeoptn(99), 99},
    };
    const NameValueOptions options_D{
        {tr("Not at all"), 0},
        {tr("Several days"), 1},
        {tr("More than half the days"), 2},
        {tr("Nearly every day"), 3},
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
    const NameValueOptions options_G{
        {tr("%1 (Red)").arg(makeoptn(1)), 1},
        {tr("%1 (Yellow)").arg(makeoptn(2)), 2},
        {tr("%1 (Green)").arg(makeoptn(3)), 3}};


    QStringList mcq_styles
        = {"color:white; background-color:red;",
           "color:black; background-color:yellow;",
           "color:white; background-color:green;"};

    QuPagePtr page_mcq(
        (new QuPage{
             new QuHeading(tr("Plain MCQ:")),
             new QuMcq(fieldRef(QStringLiteral("mcq1")), options_A),
             new QuHeading(tr("Same MCQ/field, reconfigured (randomized, "
                              "instructions, horizontal, as text button):")),
             (new QuMcq(fieldRef(QStringLiteral("mcq1")), options_A))
                 ->setRandomize(true)
                 ->setShowInstruction(true)
                 ->setHorizontal(true)
                 ->setAsTextButton(true),
             new QuHeading(tr("Same MCQ/field, reconfigured:")),
             (new QuMcq(fieldRef(QStringLiteral("mcq1")), options_A))
                 ->setAsTextButton(true),
             new QuHeading(tr("Same MCQ/field, randomized with styles:")),
             (new QuMcq(
                  fieldRef(QStringLiteral("mcq1")), options_G, &mcq_styles
              ))
                 ->setRandomize(true),
             new QuHeading(tr("A second MCQ:")),
             new QuMcq(fieldRef(QStringLiteral("mcq2")), options_C),
             new QuHeading(tr("Another:")),
             new QuMcq(fieldRef(QStringLiteral("mcq3")), options_B),
             new QuHeading(tr("The previous MCQ, reconfigured:")),
             (new QuMcq(fieldRef(QStringLiteral("mcq3")), options_B))
                 ->setHorizontal(true),
             new QuHeading(tr("A fourth MCQ, as text:")),
             (new QuMcq(fieldRef(QStringLiteral("mcq4")), options_B))
                 ->setHorizontal(true)
                 ->setAsTextButton(true),
         })
            ->setTitle(tr("Multiple-choice questions (MCQs)"))
    );

    // ------------------------------------------------------------------------
    // MCQ variants
    // ------------------------------------------------------------------------

    const QString squestion(tr("Question"));
    QuPagePtr page_mcq_variants(
        (new QuPage{
             new QuHeading(tr("MCQ grid:")),
             (new QuMcqGrid(
                  {
                      QuestionWithOneField(
                          squestion + " A", fieldRef(QStringLiteral("mcq5"))
                      ),
                      QuestionWithOneField(
                          squestion + " B", fieldRef(QStringLiteral("mcq6"))
                      ),
                      QuestionWithOneField(
                          squestion + " C", fieldRef(QStringLiteral("mcq7"))
                      ),
                      QuestionWithOneField(
                          squestion + " D (= A)",
                          fieldRef(QStringLiteral("mcq5"))
                      ),
                      QuestionWithOneField(
                          squestion + " E (= B)",
                          fieldRef(QStringLiteral("mcq6"))
                      ),
                  },
                  options_D
              ))
                 ->setSubtitles({{3, tr("subtitle before D")}}),
             new QuHeading(tr("Another MCQ grid:")),
             (new QuMcqGrid(
                  {
                      QuestionWithOneField(
                          squestion + " A", fieldRef(QStringLiteral("mcq8"))
                      ),
                      QuestionWithOneField(
                          squestion + " B; " + lipsum2,
                          fieldRef(QStringLiteral("mcq9"))
                      ),
                      QuestionWithOneField(
                          squestion + " C", fieldRef(QStringLiteral("mcq10"))
                      ),
                  },
                  options_A
              ))
                 ->setTitle(tr("MCQ 2 title; ") + lipsum2),
             new QuHeading(tr("Double MCQ grid:")),
             (new QuMcqGridDouble(
                  {
                      QuestionWithTwoFields(
                          squestion + " A",
                          fieldRef(QStringLiteral("mcqtext_1a")),
                          fieldRef(QStringLiteral("mcqtext_1b"))
                      ),
                      QuestionWithTwoFields(
                          squestion + " B; " + lipsum2,
                          fieldRef(QStringLiteral("mcqtext_2a")),
                          fieldRef(QStringLiteral("mcqtext_2b"))
                      ),
                      QuestionWithTwoFields(
                          squestion + " C",
                          fieldRef(QStringLiteral("mcqtext_3a")),
                          fieldRef(QStringLiteral("mcqtext_3b"))
                      ),
                  },
                  options_E,
                  options_F
              ))
                 ->setTitle(tr("Double-MCQ title"))
                 ->setSubtitles({{2, tr("subtitle before C")}}),
             new QuHeading(tr("MCQ grid with single Boolean (right):")),
             (new QuMcqGridSingleBoolean(
                  {
                      QuestionWithTwoFields(
                          squestion + " A",
                          fieldRef(QStringLiteral("mcq5")),
                          fieldRef(QStringLiteral("mcqbool1"))
                      ),
                      QuestionWithTwoFields(
                          squestion + " B; " + lipsum2,
                          fieldRef(QStringLiteral("mcq6")),
                          fieldRef(QStringLiteral("mcqbool2"))
                      ),
                      QuestionWithTwoFields(
                          squestion + " C",
                          fieldRef(QStringLiteral("mcq7")),
                          fieldRef(QStringLiteral("mcqbool3"))
                      ),
                  },
                  options_D,
                  tr("Happy?")
              ))
                 ->setTitle(tr("Title for MCQ grid with single boolean"))
                 ->setSubtitles({{2, tr("subtitle before C")}}),
             new QuHeading(tr("MCQ grid with single Boolean (left):")),
             (new QuMcqGridSingleBoolean(
                  {
                      QuestionWithTwoFields(
                          squestion + " A",
                          fieldRef(QStringLiteral("mcq5")),
                          fieldRef(QStringLiteral("mcqbool1"))
                      ),
                      QuestionWithTwoFields(
                          squestion + " B; " + lipsum2,
                          fieldRef(QStringLiteral("mcq6")),
                          fieldRef(QStringLiteral("mcqbool2"))
                      ),
                      QuestionWithTwoFields(
                          squestion + " C",
                          fieldRef(QStringLiteral("mcq7")),
                          fieldRef(QStringLiteral("mcqbool3"))
                      ),
                  },
                  options_D,
                  tr("Happy?")
              ))
                 ->setTitle(tr("Title for MCQ grid with single boolean"))
                 ->setBooleanLeft(true),
         })
            ->setTitle(tr("MCQ variants"))
    );

    // ------------------------------------------------------------------------
    // Multiple responses
    // ------------------------------------------------------------------------

    QuPagePtr page_multiple_response(
        (new QuPage{
             new QuHeading(tr("Standard n-from-many format:")),
             (new QuMultipleResponse({
                  QuestionWithOneField(
                      fieldRef(QStringLiteral("multipleresponse1")),
                      tr("(a) First stem")
                  ),
                  QuestionWithOneField(
                      fieldRef(QStringLiteral("multipleresponse2")),
                      tr("(b) Second stem")
                  ),
                  QuestionWithOneField(
                      fieldRef(QStringLiteral("multipleresponse3")),
                      tr("(c) Third stem")
                  ),
                  QuestionWithOneField(
                      fieldRef(QStringLiteral("multipleresponse4")),
                      tr("(d) Fourth stem")
                  ),
                  QuestionWithOneField(
                      fieldRef(QStringLiteral("multipleresponse5")),
                      tr("(e) Fifth stem")
                  ),
                  QuestionWithOneField(
                      fieldRef(QStringLiteral("multipleresponse6")),
                      tr("(f) Sixth stem")
                  ),
              }))
                 ->setMinimumAnswers(2)
                 ->setMaximumAnswers(3),
             new QuHeading(tr(
                 "With instructions off, horizontally, and text-button style:"
             )),
             (new QuMultipleResponse({
                  QuestionWithOneField(
                      fieldRef(QStringLiteral("multipleresponse1")),
                      tr("(a) First stem")
                  ),
                  QuestionWithOneField(
                      fieldRef(QStringLiteral("multipleresponse2")),
                      tr("(b) Second stem")
                  ),
                  QuestionWithOneField(
                      fieldRef(QStringLiteral("multipleresponse3")),
                      tr("(c) Third stem")
                  ),
                  QuestionWithOneField(
                      fieldRef(QStringLiteral("multipleresponse4")),
                      tr("(d) Fourth stem")
                  ),
                  QuestionWithOneField(
                      fieldRef(QStringLiteral("multipleresponse5")),
                      tr("(e) Fifth stem")
                  ),
                  QuestionWithOneField(
                      fieldRef(QStringLiteral("multipleresponse6")),
                      tr("(f) Sixth stem")
                  ),
              }))
                 ->setMinimumAnswers(2)
                 ->setMaximumAnswers(3)
                 ->setShowInstruction(false)
                 ->setHorizontal(true)
                 ->setAsTextButton(true),
         })
            ->setTitle(tr("Multiple-response questions"))
    );

    // ------------------------------------------------------------------------
    // Pickers
    // ------------------------------------------------------------------------

    FieldRefPtr fr_picker1 = fieldRef(QStringLiteral("picker1"));
    FieldRefPtr fr_picker2 = fieldRef(QStringLiteral("picker2"));
    QuPagePtr page_pickers(
        (new QuPage{
             new QuHeading(tr("Inline picker:")),
             new QuPickerInline(fr_picker1, options_A),
             new QuHeading(tr("Its clone:")),
             new QuPickerInline(fr_picker1, options_A),
             new QuHeading(tr("Its clone, randomized:")),
             (new QuPickerInline(fr_picker1, options_A))->setRandomize(true),
             new QuHeading(tr("Popup picker:")),
             (new QuPickerPopup(fr_picker2, options_A))
                 ->setPopupTitle(tr("Pickers; question 5")),
             new QuHeading(tr("Its clone, randomized:")),
             (new QuPickerPopup(fr_picker2, options_A))->setRandomize(true)})
            ->setTitle(tr("Pickers"))
    );

    // ------------------------------------------------------------------------
    // Sliders, thermometer
    // ------------------------------------------------------------------------

    QVector<QuThermometerItem> thermometer_items;
    for (int i = 0; i <= 10; ++i) {
        QString text = QString::number(i);
        if (i == 10) {
            text += tr(" - very distressed");
        } else if (i == 0) {
            text += tr(" - chilled out");
        }
        QuThermometerItem item(
            uifunc::resourceFilename(
                QString(QStringLiteral("distressthermometer/dt_sel_%1.png"))
                    .arg(i)
            ),
            uifunc::resourceFilename(
                QString(QStringLiteral("distressthermometer/dt_unsel_%1.png"))
                    .arg(i)
            ),
            text,
            i
        );
        thermometer_items.append(item);
    }

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // Likert-style slider
    // See example in creating_tasks.rst
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    const QString ROSES_FIELDNAME(QStringLiteral("thermometer"));
    const int STRONGLY_DISAGREE = 1;
    const int DISAGREE = 2;
    const int NEUTRAL = 3;
    const int AGREE = 4;
    const int STRONGLY_AGREE = 5;

    // --------------------------------------------------------------------
    // Question
    // --------------------------------------------------------------------

#ifndef DEBUG_DISABLE_MOST_SLIDERS
    auto rose_q = new QuText(tr("Roses are best when red."));
#endif

    // --------------------------------------------------------------------
    // Likert-style slider
    // --------------------------------------------------------------------
    // Create the horizontal slider
    QuSlider* likert_slider = new QuSlider(
        fieldRef(ROSES_FIELDNAME), STRONGLY_DISAGREE, STRONGLY_AGREE, 1
    );
    likert_slider->setHorizontal(true);
    likert_slider->setBigStep(1);

    // Ticks for every interval, above and below
    likert_slider->setTickInterval(1);
    likert_slider->setTickPosition(QSlider::TicksBothSides);

    // Labels
    likert_slider->setTickLabels({
        {STRONGLY_DISAGREE, tr("Strongly\ndisagree")},  // or an xstring()
        {DISAGREE, tr("Disagree")},
        {NEUTRAL, tr("Neutral")},
        {AGREE, tr("Agree")},
        {STRONGLY_AGREE, tr("Strongly\nagree")},
    });
    likert_slider->setTickLabelPosition(QSlider::TicksAbove);

    // Don't show the numerical value
    likert_slider->setShowValue(false);

    // Symmetry
    likert_slider->setNullApparentValue(NEUTRAL);
    likert_slider->setSymmetric(true);

    // --------------------------------------------------------------------
    // Grid to improve layout
    // --------------------------------------------------------------------
    // Prevent the edge labels overflowing the screen, without having to
    // use setEdgeInExtremeLabels(true) (which might distort the scale).

    const int MARGIN_WIDTH = 15;  // each side
    const int LIKERT_WIDTH = 70;
    auto likert_slider_grid = new QuGridContainer();
    likert_slider_grid->setColumnStretch(0, MARGIN_WIDTH);
    likert_slider_grid->setColumnStretch(1, LIKERT_WIDTH);
    likert_slider_grid->setColumnStretch(2, MARGIN_WIDTH);
    likert_slider_grid->addCell(QuGridCell(likert_slider, 0, 1));

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // VAS-style slider
    // See example in creating_tasks.rst
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    const QString VAS_FIELDNAME(QStringLiteral("slider1"));
    const int VAS_MIN_INT = 0;  // the internal integer minimum
    const int VAS_CENTRAL_INT = 500;  // centre, for initial display
    const int VAS_MAX_INT = 1000;  // the internal integer maximum
    const double VAS_MIN = 0.0;  // the database/display minimum
    const double VAS_MAX = 1.0;  // the database/display maximum
    const int VAS_DISPLAY_DP = 3;
    const int VAS_ABSOLUTE_SIZE_CM = 10.0;
    const bool VAS_CAN_SHRINK = true;

    // --------------------------------------------------------------------
    // VAS-style slider
    // --------------------------------------------------------------------

    // Create the horizontal slider
    QuSlider* vas_slider
        = new QuSlider(fieldRef(VAS_FIELDNAME), VAS_MIN_INT, VAS_MAX_INT, 1);
    vas_slider->setConvertForRealField(true, VAS_MIN, VAS_MAX, VAS_DISPLAY_DP);
    vas_slider->setHorizontal(true);
    vas_slider->setBigStep(1);

    // Ticks just at the extremes
    vas_slider->setTickInterval(VAS_MAX_INT);
    vas_slider->setTickPosition(QSlider::TickPosition::TicksBothSides);

    // Labels
    vas_slider->setTickLabels({
        {VAS_MIN_INT, QString::number(VAS_MIN)},  // or whatever
        {VAS_MAX_INT, QString::number(VAS_MAX)},
    });
    vas_slider->setTickLabelPosition(QSlider::TickPosition::TicksAbove);

    // Show the numerical value
    vas_slider->setShowValue(true);

    // Symmetry
    vas_slider->setNullApparentValue(VAS_CENTRAL_INT);
    vas_slider->setSymmetric(true);
    vas_slider->setEdgeInExtremeLabels(false);

    // Absolute size, if absolutely required (beware small screens -- you
    // may want the can_shrink parameter to be true for those; if the
    // screen is too small, the slider goes below the specified absolute
    // size).
    vas_slider->setAbsoluteLengthCm(VAS_ABSOLUTE_SIZE_CM, VAS_CAN_SHRINK);

    // --------------------------------------------------------------------
    // VAS-style slider -- a vertical version
    // --------------------------------------------------------------------

    QuSlider* vas_slider2
        = new QuSlider(fieldRef(VAS_FIELDNAME), VAS_MIN_INT, VAS_MAX_INT, 1);
    vas_slider2->setConvertForRealField(
        true, VAS_MIN, VAS_MAX, VAS_DISPLAY_DP
    );
    vas_slider2->setHorizontal(false);
    vas_slider2->setBigStep(1);

    vas_slider2->setTickInterval(VAS_MAX_INT);
    vas_slider2->setTickPosition(QSlider::TickPosition::TicksBothSides);

    vas_slider2->setTickLabels({
        {VAS_MIN_INT, QString::number(VAS_MIN)},  // or whatever
        {VAS_MAX_INT, QString::number(VAS_MAX)},
    });
    vas_slider2->setTickLabelPosition(QSlider::TickPosition::TicksAbove);

    vas_slider2->setShowValue(true);

    vas_slider2->setNullApparentValue(VAS_CENTRAL_INT);
    vas_slider2->setSymmetric(true);
    vas_slider2->setEdgeInExtremeLabels(false);

    vas_slider2->setAbsoluteLengthCm(VAS_ABSOLUTE_SIZE_CM, VAS_CAN_SHRINK);

    const QString vas_description
        = tr("Slider is set to %1 cm; can_shrink = %2")
              .arg(
                  QString::number(VAS_ABSOLUTE_SIZE_CM),
                  uifunc::trueFalse(VAS_CAN_SHRINK)
              );

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // End of those examples. On to the page...
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    FieldRefPtr fr_thermometer = fieldRef(QStringLiteral("thermometer"));
    FieldRefPtr fr_slider1 = fieldRef(QStringLiteral("slider1"));
    FieldRefPtr fr_slider2 = fieldRef(QStringLiteral("slider2"));
    QuPagePtr page_sliders(
        (new QuPage{
#ifndef DEBUG_DISABLE_MOST_SLIDERS
             new QuHeading(tr("Integer slider:")),
             (new QuSlider(fr_thermometer, 0, 10, 1))
                 ->setTickInterval(1)
                 ->setTickPosition(QSlider::TicksBothSides)
                 ->setShowValue(true),
#endif
             new QuHeading(tr("Integer slider (same field as above), vertical")
             ),
             (new QuSlider(fr_thermometer, 0, 10, 1))
                 ->setShowValue(true)
                 ->setTickInterval(2)
                 ->setTickPosition(QSlider::TicksBothSides)
                 ->setUseDefaultTickLabels(true)
                 ->setTickLabelPosition(QSlider::TicksBothSides)
                 ->setHorizontal(false),
#ifndef DEBUG_DISABLE_MOST_SLIDERS
             new QuHeading(tr("Real number/floating-point slider:")),
             (new QuSlider(fr_slider1, 0, 10, 1))
                 ->setShowValue(true)
                 ->setTickInterval(1)
                 ->setTickPosition(QSlider::TicksBelow)
                 ->setConvertForRealField(true, 0, 1),
             new QuHeading(tr("Real number slider with custom labels (edging "
                              "in extreme labels):")),
             (new QuSlider(fr_slider2, 100, 500, 1))
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
             new QuHeading(
                 tr("Real number slider with custom labels (standard labels):")
             ),
             (new QuSlider(fr_slider2, 100, 500, 1))
                 ->setConvertForRealField(true, 1, 5)
                 ->setShowValue(false)
                 ->setTickInterval(1)
                 // ->setTickPosition(QSlider::NoTicks)
                 // ->setTickPosition(QSlider::TicksAbove)
                 // ->setTickPosition(QSlider::TicksBelow)
                 ->setTickPosition(QSlider::TicksBothSides)
                 // ->setTickLabelPosition(QSlider::NoTicks)
                 // ->setTickLabelPosition(QSlider::TicksAbove)
                 // ->setTickLabelPosition(QSlider::TicksBelow)
                 ->setTickLabelPosition(QSlider::TicksBothSides)
                 ->setTickLabels({
                     {100, tr("one: low")},
                     {300, tr("three: medium")},
                     {500, tr("five: maximum!")},
                 })
                 ->setShowValue(true),
             new QuHeading(tr("Thermometer:")),
             (new QuThermometer(fr_thermometer, thermometer_items))
                 ->setRescale(true, 0.4),
             new QuHeading(tr("Likert-style (discrete) slider, in grid (70% "
                              "of window width)")),
             rose_q,
             likert_slider_grid,
             new QuHeading(tr("Visual analogue scale-style slider "
                              "(approximating continuous)")),
             new QuText(vas_description),
             vas_slider,
             new QuHeading(
                 tr("Visual analogue scale-style slider (vertical version)")
             ),
             new QuText(vas_description),
             vas_slider2,
#endif
         })
            ->setTitle(tr("Sliders and thermometers"))
            ->setType(QuPage::PageType::ClinicianWithPatient)
    );

    // ------------------------------------------------------------------------
    // Editable variables inc. datetime
    // ------------------------------------------------------------------------

    FieldRefPtr fr_date_time = fieldRef(QStringLiteral("date_time"));
    FieldRefPtr fr_date_only = fieldRef(QStringLiteral("date_only"));
    FieldRefPtr fr_time_only = fieldRef(QStringLiteral("time_only"));
    FieldRefPtr fr_typedvar_text = fieldRef(QStringLiteral("typedvar_text"));
    FieldRefPtr fr_typedvar_int = fieldRef(QStringLiteral("typedvar_int"));
    FieldRefPtr fr_typedvar_text_multiline
        = fieldRef(QStringLiteral("typedvar_text_multiline"));
    QuPagePtr page_vars(
        (new QuPage{
             new QuText(
                 tr("Pages for clinicians have a different background colour.")
             ),
             new QuHeading(tr("Date/time:")),
             new QuDateTime(fr_date_time),
             new QuHeading(tr("Date/time (with ‘now’ and ‘nullify’ buttons):")
             ),
             (new QuDateTime(fr_date_time))
                 ->setOfferNowButton(true)
                 ->setOfferNullButton(true),
             new QuHeading(tr("Date/time (custom format):")),
             (new QuDateTime(fr_date_time))
                 ->setMode(QuDateTime::CustomDateTime)
                 ->setCustomFormat(QStringLiteral("yyyy MM dd HH:mm:ss:zzz")),
             new QuHeading(tr("Date:")),
             (new QuDateTime(fr_date_only))
                 ->setMode(QuDateTime::DefaultDate)
                 ->setOfferNowButton(true),
             new QuHeading(tr("Date (custom format):")),
             (new QuDateTime(fr_date_only))
                 ->setMode(QuDateTime::CustomDate)
                 ->setCustomFormat(QStringLiteral("yyyy MM dd"))
                 ->setOfferNowButton(true),
             new QuHeading(tr("Time:")),
             (new QuDateTime(fr_time_only))
                 ->setMode(QuDateTime::DefaultTime)
                 ->setOfferNowButton(true)
                 ->setOfferNullButton(true),
             new QuHeading(tr("Time (custom format):")),
             (new QuDateTime(fr_time_only))
                 ->setMode(QuDateTime::CustomTime)
                 ->setCustomFormat(QStringLiteral("HH:mm:ss"))
                 ->setOfferNowButton(true),
             new QuHeading(tr("Integer spinbox (range 5–10):")),
             new QuSpinBoxInteger(
                 fieldRef(QStringLiteral("spinbox_int")), 5, 10
             ),
             new QuHeading(tr("Double spinbox (range 7.1–7.9):")),
             new QuSpinBoxDouble(
                 fieldRef(QStringLiteral("spinbox_real")), 7.1, 7.9
             ),
             new QuHeading(tr("Text editor (plain text):")),
             new QuTextEdit(fr_typedvar_text_multiline, false),
             new QuHeading(tr("Text editor (clone of previous):")),
             new QuTextEdit(fr_typedvar_text_multiline, false),
             new QuHeading(tr("Text editor (rich text):")),
             (new QuTextEdit(
                  fieldRef(QStringLiteral("typedvar_text_rich")), true
              ))
                 ->setHint(tr("This one has a hint (placeholder text)")),
             new QuHeading(tr("Line editor (plain):")),
             (new QuLineEdit(fr_typedvar_text))
                 ->setHint(tr("hint: plain text")),
             new QuHeading(tr("Line editor (integer, range 13–19):")),
             new QuLineEditInteger(fr_typedvar_int, 13, 19),
             new QuHeading(
                 tr("Line editor (double, range -0.05 to -0.09, 2dp):")
             ),
             new QuLineEditDouble(
                 fieldRef(QStringLiteral("typedvar_real")), -0.05, -0.09, 2
             ),
             new QuHeading(tr("Variables in a grid:")),
             questionnairefunc::defaultGridRawPointer(
                 {
                     {tr("label 1 (text)"), new QuLineEdit(fr_typedvar_text)},
                     {tr("label 2 (int 13-19)"),
                      new QuLineEditInteger(fr_typedvar_int, 13, 19)},
                     {tr("label 3"),
                      new QuHeading("Just a heading: " + lipsum2)},
                     {tr("label 4"), new QuDateTime(fr_date_time)},
                     {tr("label 5 (multiline text)"),
                      new QuTextEdit(fr_typedvar_text)},
                 },
                 uiconst::DEFAULT_COLSPAN_Q,
                 uiconst::DEFAULT_COLSPAN_A
             ),
         })
            ->setTitle(tr("Editable variable including dates/times"))
            ->setType(QuPage::PageType::Clinician)
    );

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
    FieldRefPtr fr_dx_code = fieldRef(QStringLiteral("diagnosticcode_code"));
    FieldRefPtr fr_dx_desc
        = fieldRef(QStringLiteral("diagnosticcode_description"));
    FieldRefPtr fr_dx_code2 = fieldRef(QStringLiteral("diagnosticcode2_code"));
    FieldRefPtr fr_dx_desc2
        = fieldRef(QStringLiteral("diagnosticcode2_description"));
    QuPagePtr page_diag(
        (new QuPage{
             new QuHeading(tr("Diagnostic code, ICD-10:")),
             new QuDiagnosticCode(icd10, fr_dx_code, fr_dx_desc),
             new QuHeading(tr("Diagnostic code, clone of the preceding:")),
             new QuDiagnosticCode(icd10, fr_dx_code, fr_dx_desc),
             new QuHeading(tr("Diagnostic code, ICD-9-CM:")),
             new QuDiagnosticCode(icd9cm, fr_dx_code2, fr_dx_desc2),
         })
            ->setTitle(tr("Diagnostic codes"))
    );

    // ------------------------------------------------------------------------
    // Canvas
    // ------------------------------------------------------------------------

    BlobFieldRefPtr fr_canvas_blobid
        = blobFieldRef(QStringLiteral("canvas_blobid"), true);
    BlobFieldRefPtr fr_canvas2_blobid
        = blobFieldRef(QStringLiteral("canvas2_blobid"), true);
    QuPagePtr page_canvas_1(
        (new QuPage{
             (new QuText(tr("Page style: ClinicianWithPatient")))
                 ->setItalic(true),
             (new QuText(tr("WATCH OUT: scrolling enabled for this page; may "
                            "conflict with canvas; see next page too")))
                 ->setWarning(true),
             new QuHeading(tr("Canvas, blank start:")),
             new QuCanvas(fr_canvas2_blobid),
             new QuHeading(tr("Canvas, using files:")),
             new QuCanvas(
                 fr_canvas_blobid,
                 uifunc::resourceFilename(QStringLiteral("ace3/rhinoceros.png")
                 )
             ),
             new QuHeading(tr("Canvas, clone of the first one:")),
             new QuCanvas(fr_canvas2_blobid),
         })
            ->setTitle(tr("Canvas (allowing scrolling)"))
            ->setType(QuPage::PageType::ClinicianWithPatient)
    );

    QuPagePtr page_canvas_2(
        (new QuPage{
             new QuHeading(tr("As before, but with scrolling disabled:")),
             new QuCanvas(
                 fr_canvas_blobid,
                 uifunc::resourceFilename(QStringLiteral("ace3/rhinoceros.png")
                 )
             ),
         })
            ->setTitle(tr("Canvas (disabling scrolling)"))
            ->allowScroll(false)
            ->setType(QuPage::PageType::ClinicianWithPatient)
    );

    // ------------------------------------------------------------------------
    // Buttons
    // ------------------------------------------------------------------------

    // Safe object lifespan signal: can use std::bind
    QuPagePtr page_buttons(
        (new QuPage{
             new QuButton(
                 tr("Say hello"),
                 std::bind(&DemoQuestionnaire::callbackHello, this)
             ),
             (new QuButton(
                  tr("Say hello [disabled]"),
                  std::bind(&DemoQuestionnaire::callbackHello, this)
              ))
                 ->setActive(false),
             new QuButton(
                 tr("Button with args ('foo')"),
                 std::bind(&DemoQuestionnaire::callbackArg, this, "foo")
             ),
             new QuButton(
                 tr("Button with args ('bar')"),
                 std::bind(&DemoQuestionnaire::callbackArg, this, "bar")
             ),
             new QuButton(
                 uiconst::CBS_ADD,
                 true,
                 true,
                 std::bind(&DemoQuestionnaire::callbackHello, this)
             ),
         })
            ->setTitle(tr("Buttons"))
    );

    // ------------------------------------------------------------------------
    // Photo (for a mandatory photo: last page in case we have no camera)
    // ... make it non-mandatory...
    // ------------------------------------------------------------------------

    QuPagePtr page_photo(
        (new QuPage{
             new QuHeading(tr("Photo:")),
             new QuPhoto(blobFieldRef(QStringLiteral("photo_blobid"), false)),
         })
            ->setTitle(tr("Photo"))
    );

    // ------------------------------------------------------------------------
    // Layout test: cf. WidgetTestMenu::testQuestionnaire()
    // ------------------------------------------------------------------------

    QuPagePtr page_minimal_layout(
        (new QuPage{
             new QuText(TextConst::LOREM_IPSUM_1),
         })
            ->setTitle(tr("Reasonably long title with several words"))
    );

    // ------------------------------------------------------------------------
    // Questionnaire
    // ------------------------------------------------------------------------

    auto questionnaire = new Questionnaire(
        m_app,
        {
            page_text,
#ifdef DEBUG_BIG_HEADER_ONLY_PAGE
            page_text_header_only,
#endif
            page_image,
            page_headings_layout,
            page_audio_countdown,
            page_boolean,
            page_mcq,
            page_mcq_variants,
            page_multiple_response,
            page_pickers,
            page_sliders,
            page_vars,
            page_diag,
            page_canvas_1,
            page_canvas_2,
            page_buttons,
            page_photo,
            page_minimal_layout,
        }
    );
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}

// ============================================================================
// Extra
// ============================================================================

void DemoQuestionnaire::callbackHello()
{
    uifunc::alert(tr("Hello!"));
}

void DemoQuestionnaire::callbackArg(const QString& arg)
{
    uifunc::alert(tr("Function argument was:") + " " + arg);
}

QuBoolean* DemoQuestionnaire::aceBoolean(
    const QString& stringname, const QString& fieldname
)
{
    return (new QuBoolean(
                m_app.xstring(QStringLiteral("ace3"), stringname),
                fieldRef(fieldname, false)
            ))
        ->setBigIndicator(false);
}
