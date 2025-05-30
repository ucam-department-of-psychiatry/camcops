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


/*

A note on task inheritance:

- MiniAce isn't a proper subclass of Ace3, because it has fewer fields.
- A common non-creatable parent is perfectly proper, though. That would likely
  be most sensible.

*/

#define NOSCROLL_IMAGE_PAGES  // Should be defined. Better UI with it.

#include "miniace.h"

#include <QDebug>

#include "common/textconst.h"
#include "common/uiconst.h"
#include "lib/datetime.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/qucountdown.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/quflowcontainer.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/quphoto.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/quverticalcontainer.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using mathfunc::allNull;
using mathfunc::eq;
using mathfunc::noneNull;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;
using stringfunc::strnum;
using stringfunc::strseq;

const QString MiniAce::MINIACE_TABLENAME(QStringLiteral("miniace"));

// Field names, field prefixes, and field counts
const int N_ATTN_TIME_MINIACE = 4;

// Subtotals. No magic numbers...
const int TOTAL_ATTN_MINIACE = 4;
const int TOTAL_MEM_MINIACE = 14;
const int TOTAL_FLUENCY_MINIACE = 7;
const int TOTAL_VSP_MINIACE = 5;

// xstrings
const QString X_EDITION_MINIACE(QStringLiteral("edition_miniace"));

void initializeMiniAce(TaskFactory& factory)
{
    static TaskRegistrar<MiniAce> registered(factory);
}

MiniAce::MiniAce(
    CamcopsApp& app, DatabaseManager& db, const int load_pk, QObject* parent
) :
    AceFamily(app, db, MINIACE_TABLENAME, parent)
{
    addField(
        FN_TASK_EDITION,
        QMetaType::fromType<QString>(),
        false,
        false,
        false,
        xstring(X_EDITION_MINIACE)
    );
    addField(
        FN_TASK_ADDRESS_VERSION,
        QMetaType::fromType<QString>(),
        false,
        false,
        false,
        TASK_DEFAULT_VERSION
    );
    addField(
        FN_REMOTE_ADMINISTRATION,
        QMetaType::fromType<bool>(),
        false,
        false,
        false,
        false
    );

    addField(FN_AGE_FT_EDUCATION, QMetaType::fromType<int>());
    addField(FN_OCCUPATION, QMetaType::fromType<QString>());
    addField(FN_HANDEDNESS, QMetaType::fromType<QString>());

    addFields(
        strseq(FP_ATTN_TIME, 1, N_ATTN_TIME_MINIACE),
        QMetaType::fromType<int>()
    );

    addFields(
        strseq(FP_MEM_REPEAT_ADDR_TRIAL1, 1, N_MEM_REPEAT_RECALL_ADDR),
        QMetaType::fromType<int>()
    );
    addFields(
        strseq(FP_MEM_REPEAT_ADDR_TRIAL2, 1, N_MEM_REPEAT_RECALL_ADDR),
        QMetaType::fromType<int>()
    );
    addFields(
        strseq(FP_MEM_REPEAT_ADDR_TRIAL3, 1, N_MEM_REPEAT_RECALL_ADDR),
        QMetaType::fromType<int>()
    );

    addField(FN_FLUENCY_ANIMALS_SCORE, QMetaType::fromType<int>());

    addField(FN_VSP_DRAW_CLOCK, QMetaType::fromType<int>());

    addFields(
        strseq(FP_MEM_RECALL_ADDRESS, 1, N_MEM_REPEAT_RECALL_ADDR),
        QMetaType::fromType<int>()
    );

    addField(FN_PICTURE1_BLOBID, QMetaType::fromType<int>());
    // ... FK to BLOB table
    addField(FN_PICTURE2_BLOBID, QMetaType::fromType<int>());
    // ... FK to BLOB table
    addField(FN_COMMENTS, QMetaType::fromType<QString>());

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString MiniAce::shortname() const
{
    return QStringLiteral("Mini-ACE");
}

QString MiniAce::longname() const
{
    return tr("Mini-Addenbrooke’s Cognitive Examination");
}

QString MiniAce::description() const
{
    return tr(
        "30-point clinician-administered assessment of attention/"
        "orientation, memory, fluency, and visuospatial domains."
    );
}

// ============================================================================
// Instance info
// ============================================================================

bool MiniAce::isComplete() const
{
    return noneNull(values(strseq(FP_ATTN_TIME, 1, N_ATTN_TIME_MINIACE)))
        && noneNull(values(
            strseq(FP_MEM_REPEAT_ADDR_TRIAL3, 1, N_MEM_REPEAT_RECALL_ADDR)
        ))
        && !valueIsNull(FN_FLUENCY_ANIMALS_SCORE)
        && !valueIsNull(FN_VSP_DRAW_CLOCK)
        && noneNull(values(
            strseq(FP_MEM_RECALL_ADDRESS, 1, N_MEM_REPEAT_RECALL_ADDR)
        ));
}

QStringList MiniAce::summary() const
{
    QStringList lines;
    lines.append(
        xstring(X_MINI_ACE_SCORE)
        + scorePercent(miniAceScore(), TOTAL_MINI_ACE)
    );
    lines.append(
        xstring(QStringLiteral("cat_attn"))
        + scorePercent(getAttnScore(), TOTAL_ATTN_MINIACE)
    );
    lines.append(
        xstring(QStringLiteral("cat_mem"))
        + scorePercent(getMemScore(), TOTAL_MEM_MINIACE)
    );
    lines.append(
        xstring(QStringLiteral("cat_fluency"))
        + scorePercent(getFluencyScore(), TOTAL_FLUENCY_MINIACE)
    );
    lines.append(
        xstring(QStringLiteral("cat_vsp"))
        + scorePercent(getVisuospatialScore(), TOTAL_VSP_MINIACE)
    );
    return lines;
}

OpenableWidget* MiniAce::editor(const bool read_only)
{
    int pagenum = 1;
    auto makeTitle = [this, &pagenum](const QString& title) -> QString {
        return xstring(QStringLiteral("title_prefix_miniace"))
            + QString(QStringLiteral(" %1")).arg(pagenum++) + ": " + title;
    };

    // ------------------------------------------------------------------------
    // Preamble; age-leaving-full-time-education; handedness
    // ------------------------------------------------------------------------

    NameValueOptions options_task_version;
    const QStringList versions = addressVersionsAvailable();
    for (const auto& v : versions) {
        options_task_version.append(NameValuePair(v, v));
    }
    const NameValueOptions options_handedness{
        {xstring(QStringLiteral("left_handed")), "L"},
        {xstring(QStringLiteral("right_handed")), "R"},
    };
    FieldRefPtr fr_task_addr_version = fieldRef(FN_TASK_ADDRESS_VERSION);
    QuPagePtr page_preamble(
        (new QuPage{
             heading(X_EDITION_MINIACE),
             getClinicianQuestionnaireBlockRawPointer(),
             instruction(QStringLiteral("choose_task_version")),
             questionnairefunc::defaultGridRawPointer(
                 {
                     {"",
                      (new QuMcq(fr_task_addr_version, options_task_version))
                          ->setHorizontal(true)
                          ->addTag(TAG_EL_CHOOSE_TASK_VERSION)},
                     {"",
                      (new QuText(fr_task_addr_version))
                          ->addTag(TAG_EL_SHOW_TASK_VERSION)
                          ->setVisible(false)},
                     {"",
                      boolean(
                          QStringLiteral("q_remote"), FN_REMOTE_ADMINISTRATION
                      )},
                 },
                 uiconst::DEFAULT_COLSPAN_Q,
                 uiconst::DEFAULT_COLSPAN_A
             ),
             // remInstruct(QStringLiteral("instruction_remote_read_first")),
             // Mini-ACE doesn't have an official remote version and therefore
             // remote instructions. But it is very simple.
             stdInstruct(QStringLiteral("instruction_need_paper_miniace")),
             remInstruct(QStringLiteral("instruction_need_paper_remote_miniace"
             )),
             remInstruct(
                 QStringLiteral("instruction_remote_camera_to_participant")
             ),
             instruction(QStringLiteral("preamble_instruction")),
             questionnairefunc::defaultGridRawPointer(
                 {
                     {xstring(QStringLiteral("q_age_leaving_fte")),
                      new QuLineEditInteger(
                          fieldRef(FN_AGE_FT_EDUCATION), MIN_AGE, MAX_AGE_Y
                      )},
                     {xstring(QStringLiteral("q_occupation")),
                      new QuLineEdit(fieldRef(FN_OCCUPATION))},
                     {xstring(QStringLiteral("q_handedness")),
                      (new QuMcq(fieldRef(FN_HANDEDNESS), options_handedness))
                          ->setHorizontal(true)},
                 },
                 uiconst::DEFAULT_COLSPAN_Q,
                 uiconst::DEFAULT_COLSPAN_A
             ),
         })
            ->setTitle(makeTitle(tr("Preamble")))
            ->setType(QuPage::PageType::Clinician)
            ->addTag(TAG_PG_PREAMBLE)
    );

    // ------------------------------------------------------------------------
    // Attention/orientation
    // ------------------------------------------------------------------------

    const QDateTime now = datetime::now();
    const QString correct_date
        = "     " + now.toString(QStringLiteral("dddd d MMMM yyyy"));
    // ... e.g. "Monday 2 January 2016";

    QuPagePtr page_attn(
        (new QuPage{
             heading(QStringLiteral("cat_attn")),

             // Orientation
             instruction(QStringLiteral("attn_q_time")),
             new QuFlowContainer{
                 boolean(
                     QStringLiteral("attn_time1"), strnum(FP_ATTN_TIME, 1)
                 ),
                 boolean(
                     QStringLiteral("attn_time2"), strnum(FP_ATTN_TIME, 2)
                 ),
                 boolean(
                     QStringLiteral("attn_time3"), strnum(FP_ATTN_TIME, 3)
                 ),
                 boolean(
                     QStringLiteral("attn_time4"), strnum(FP_ATTN_TIME, 4)
                 ),
             },
             explanation(QStringLiteral("instruction_time_miniace")),
             (new QuText(correct_date))->setItalic(),

         })
            ->setTitle(makeTitle(tr("Attention")))
            ->setType(QuPage::PageType::Clinician)
    );

    // ------------------------------------------------------------------------
    // Learning the address (comes before fluency in the mini-ACE)
    // ------------------------------------------------------------------------

    // Inelegance acknowledged! Address layouts are cosmetic.
    auto addrReg = [this](
                       int trial, int component, bool mandatory = false
                   ) -> QuElement* {
        return (new QuBoolean(
                    targetAddressComponent(component),
                    fieldRef(
                        FP_MEM_REPEAT_ADDR_GENERIC.arg(trial).arg(component),
                        mandatory
                    )
                ))
            ->addTag(tagAddressRegistration(trial, component));
    };
    QuPagePtr page_repeat_addr_famous(
        (new QuPage{
             heading(QStringLiteral("cat_mem")),
             instruction(QStringLiteral("memory_q_address")),
             explanation(QStringLiteral("memory_instruction_address_1")),
             explanation(QStringLiteral("memory_instruction_address_2")),

             // Address 1
             new QuVerticalContainer{
                 instructionRaw(xstring(QStringLiteral("trial")) + " 1"),
                 new QuFlowContainer{addrReg(1, 1), addrReg(1, 2)},
                 new QuFlowContainer{
                     addrReg(1, 3), addrReg(1, 4), addrReg(1, 5)},
                 addrReg(1, 6),
                 addrReg(1, 7),
             },

             // Address 2
             new QuVerticalContainer{
                 instructionRaw(xstring(QStringLiteral("trial")) + " 2"),
                 new QuFlowContainer{addrReg(2, 1), addrReg(2, 2)},
                 new QuFlowContainer{
                     addrReg(2, 3), addrReg(2, 4), addrReg(2, 5)},
                 addrReg(2, 6),
                 addrReg(2, 7),
             },

             // Address 3
             new QuVerticalContainer{
                 instructionRaw(xstring(QStringLiteral("trial")) + " 3"),
                 new QuFlowContainer{
                     addrReg(3, 1, true),
                     addrReg(3, 2, true),
                 },
                 new QuFlowContainer{
                     addrReg(3, 3, true),
                     addrReg(3, 4, true),
                     addrReg(3, 5, true),
                 },
                 addrReg(3, 6, true),
                 addrReg(3, 7, true),
             },
         })
            ->setTitle(makeTitle(tr("Memory")))
            ->addTag(TAG_PG_ADDRESS_LEARNING_FAMOUS)
            ->setType(QuPage::PageType::Clinician)
    );

    // ------------------------------------------------------------------------
    // Fluency
    // ------------------------------------------------------------------------

    const NameValueOptions options_fluency_animals{
        {"0–4", 0},
        {"5–6", 1},
        {"7–8", 2},
        {"9–10", 3},
        {"11–13", 4},
        {"14–16", 5},
        {"17–21", 6},
        {"≥22", 7}};
    QuPagePtr page_fluency(
        (new QuPage{
             heading(QStringLiteral("cat_fluency")),

             // Animals
             subheading(QStringLiteral("fluency_subheading_animals")),
             instruction(QStringLiteral("fluency_q_animals")),
             new QuCountdown(FLUENCY_TIME_SEC),
             explanation(QStringLiteral("fluency_instruction_animals")),
             text(QStringLiteral("fluency_prompt_animals_cor")),
             (new QuMcq(
                  fieldRef(FN_FLUENCY_ANIMALS_SCORE), options_fluency_animals
              ))
                 ->setHorizontal(true),
         })
            ->setTitle(makeTitle(tr("Fluency")))
            ->setType(QuPage::PageType::Clinician)
    );

    // ------------------------------------------------------------------------
    // Clock
    // ------------------------------------------------------------------------

    const NameValueOptions options_clock = NameValueOptions::makeNumbers(0, 5);
    QuPagePtr page_clock(
        (new QuPage{
             stdInstruct(QStringLiteral("vsp_q_clock")),
             remInstruct(QStringLiteral("vsp_q_clock_remote")),
             explanation(QStringLiteral("vsp_instruction_clock")),
             text(QStringLiteral("vsp_score_clock")),
             (new QuMcq(fieldRef(FN_VSP_DRAW_CLOCK), options_clock))
                 ->setHorizontal(true),
         })
            ->setTitle(makeTitle(tr("Clock")))
            ->setType(QuPage::PageType::Clinician)
    );

    // ------------------------------------------------------------------------
    // Back to clinician
    // ------------------------------------------------------------------------

    QuPagePtr page_back_to_clinician(
        (new QuPage{
             textRaw(tr("Please make sure the subject can’t see the screen "
                        "before you proceed. (Memory prompts coming up.)")),
         })
            ->setTitle(makeTitle(tr("[reminder to clinician]")))
            ->setType(QuPage::PageType::Clinician)
    );

    // ------------------------------------------------------------------------
    // Address recall: free
    // ------------------------------------------------------------------------

    auto addrFree = [this](int component) -> QuElement* {
        return (new QuBoolean(
                    targetAddressComponent(component),
                    fieldRef(strnum(FP_MEM_RECALL_ADDRESS, component), true)
                ))
            ->addTag(tagAddressFreeRecall(component));
    };
    QuPagePtr page_recall_address_free(
        (new QuPage{
             heading(QStringLiteral("cat_mem")),
             instruction(QStringLiteral("mem_q_recall_address")),
             new QuVerticalContainer{
                 new QuFlowContainer{addrFree(1), addrFree(2)},
                 new QuFlowContainer{addrFree(3), addrFree(4), addrFree(5)},
                 addrFree(6),
                 addrFree(7),
             },
         })
            ->setTitle(makeTitle(tr("Free recall")))
            ->addTag(TAG_PG_MEM_FREE_RECALL)
            ->setType(QuPage::PageType::Clinician)
    );

    // ------------------------------------------------------------------------
    // Comments
    // ------------------------------------------------------------------------

    QuPagePtr page_comments(
        (new QuPage{
             instructionRaw(TextConst::examinerCommentsPrompt()),
             (new QuLineEdit(fieldRef(FN_COMMENTS, false)))
                 ->setHint(TextConst::examinerComments()),
         })
            ->setTitle(makeTitle(tr("Comments")))
            ->setType(QuPage::PageType::Clinician)
    );

    // ------------------------------------------------------------------------
    // Photo 1
    // ------------------------------------------------------------------------

    QuPagePtr page_photo_1(
        (new QuPage{
             instruction(QStringLiteral("picture1_q")),
             explanation(QStringLiteral("picture_instruction1")),
             explanation(QStringLiteral("picture_instruction2_miniace")),
             new QuPhoto(blobFieldRef(FN_PICTURE1_BLOBID, false)),
         })
            ->setTitle(makeTitle(tr("Photo 1")))
            ->setType(QuPage::PageType::Clinician)
    );

    // ------------------------------------------------------------------------
    // Photo 2
    // ------------------------------------------------------------------------

    QuPagePtr page_photo_2(
        (new QuPage{
             instruction(QStringLiteral("picture2_q")),
             explanation(QStringLiteral("picture_instruction1")),
             explanation(QStringLiteral("picture_instruction2_miniace")),
             new QuPhoto(blobFieldRef(FN_PICTURE2_BLOBID, false)),
         })
            ->setTitle(makeTitle(tr("Photo 2")))
            ->setType(QuPage::PageType::Clinician)
    );

    // ------------------------------------------------------------------------
    // Questionnaire
    // ------------------------------------------------------------------------

    m_questionnaire = new Questionnaire(
        m_app,
        {
            page_preamble,
            page_attn,
            page_repeat_addr_famous,
            page_fluency,
            page_clock,
            page_back_to_clinician,
            page_recall_address_free,
            page_comments,
            page_photo_1,
            page_photo_2,
        }
    );
    m_questionnaire->setReadOnly(read_only);

    // ------------------------------------------------------------------------
    // Signals and initial dynamic state
    // ------------------------------------------------------------------------

    // When the user changes the task address version (e.g. A/B/C).
    FieldRefPtr fr_task_version = fieldRef(FN_TASK_ADDRESS_VERSION);
    connect(
        fr_task_version.data(),
        &FieldRef::valueChanged,
        this,
        &MiniAce::updateTaskVersionAddresses
    );
    updateTaskVersionAddresses();

    // When the user changes the remote administration status.
    FieldRefPtr fr_remote = fieldRef(FN_REMOTE_ADMINISTRATION);
    connect(
        fr_remote.data(),
        &FieldRef::valueChanged,
        this,
        &MiniAce::showStandardOrRemoteInstructions
    );
    showStandardOrRemoteInstructions();

    // When the user writes data relating to a specific address, locking in
    // the address version selection. See isChangingAddressVersionOk().
    for (int i = 1; i <= N_MEM_REPEAT_RECALL_ADDR; ++i) {
        connect(
            fieldRef(strnum(FP_MEM_REPEAT_ADDR_TRIAL1, i)).data(),
            &FieldRef::valueChanged,
            this,
            &MiniAce::updateTaskVersionEditability
        );
        connect(
            fieldRef(strnum(FP_MEM_REPEAT_ADDR_TRIAL2, i)).data(),
            &FieldRef::valueChanged,
            this,
            &MiniAce::updateTaskVersionEditability
        );
        connect(
            fieldRef(strnum(FP_MEM_REPEAT_ADDR_TRIAL3, i)).data(),
            &FieldRef::valueChanged,
            this,
            &MiniAce::updateTaskVersionEditability
        );
    }
    for (int i = 1; i <= N_MEM_REPEAT_RECALL_ADDR; ++i) {
        connect(
            fieldRef(strnum(FP_MEM_RECALL_ADDRESS, i)).data(),
            &FieldRef::valueChanged,
            this,
            &MiniAce::updateTaskVersionEditability
        );
    }
    updateTaskVersionEditability();

    // ------------------------------------------------------------------------
    // Done
    // ------------------------------------------------------------------------

    return m_questionnaire;
}

// ============================================================================
// Task-specific calculations
// ============================================================================

int MiniAce::getAttnScore() const
{
    return sumInt(values(strseq(FP_ATTN_TIME, 1, N_ATTN_TIME_MINIACE)));
    // 4 points
}

int MiniAce::getFluencyScore() const
{
    return valueInt(FN_FLUENCY_ANIMALS_SCORE);
    // 7 points
}

int MiniAce::getMemScore() const
{
    return sumInt(values(
               strseq(FP_MEM_REPEAT_ADDR_TRIAL3, 1, N_MEM_REPEAT_RECALL_ADDR)
           ))
        + sumInt(values(
            strseq(FP_MEM_RECALL_ADDRESS, 1, N_MEM_REPEAT_RECALL_ADDR)
        ));
    // 14 points
}

int MiniAce::getVisuospatialScore() const
{
    return valueInt(FN_VSP_DRAW_CLOCK);
    // 5 points
}

int MiniAce::miniAceScore() const
{
    return getAttnScore() + getFluencyScore() + getMemScore()
        + getVisuospatialScore();
    // 30 points
}

// ============================================================================
// Task address version support functions
// ============================================================================

QString MiniAce::taskAddressVersion() const
{
    // Could be consolidated into AceFamily, but we follow the rule that access
    // to class-specific data is not put into the parent.
    const QString selected = valueString(FN_TASK_ADDRESS_VERSION);
    if (addressVersionsAvailable().contains(selected)) {
        return selected;
    }
    return TASK_DEFAULT_VERSION;
}

bool MiniAce::isChangingAddressVersionOk() const
{
    return allNull(values(
               strseq(FP_MEM_REPEAT_ADDR_TRIAL1, 1, N_MEM_REPEAT_RECALL_ADDR)
           ))
        && allNull(values(
            strseq(FP_MEM_REPEAT_ADDR_TRIAL2, 1, N_MEM_REPEAT_RECALL_ADDR)
        ))
        && allNull(values(
            strseq(FP_MEM_REPEAT_ADDR_TRIAL3, 1, N_MEM_REPEAT_RECALL_ADDR)
        ))
        && allNull(values(
            strseq(FP_MEM_RECALL_ADDRESS, 1, N_MEM_REPEAT_RECALL_ADDR)
        ));
}

// ============================================================================
// Signal handlers
// ============================================================================

void MiniAce::updateTaskVersionAddresses()
{
    // Set address components.
    for (int component = 1; component <= N_MEM_REPEAT_RECALL_ADDR;
         ++component) {

        // 1. Repetition.
        const QString target_text = targetAddressComponent(component);
        for (int trial = 1; trial <= ADDR_LEARN_N_TRIALS; ++trial) {
            auto repet = qobject_cast<QuBoolean*>(
                m_questionnaire->getFirstElementByTag(
                    tagAddressRegistration(trial, component),
                    false,
                    TAG_PG_ADDRESS_LEARNING_FAMOUS
                )
            );
            if (!repet) {
                continue;
            }
            repet->setText(target_text);
        }

        // 2. Free recall.
        auto free_recall
            = qobject_cast<QuBoolean*>(m_questionnaire->getFirstElementByTag(
                tagAddressFreeRecall(component), false, TAG_PG_MEM_FREE_RECALL
            ));
        if (!free_recall) {
            continue;
        }
        free_recall->setText(target_text);
    }
}

void MiniAce::showStandardOrRemoteInstructions()
{
    const bool remote = valueBool(FN_REMOTE_ADMINISTRATION);
    const bool standard = !remote;
    const QVector<QuElement*> standard_elements
        = m_questionnaire->getElementsByTag(TAG_STANDARD, false);
    for (auto e : standard_elements) {
        e->setVisible(standard);
    }
    const QVector<QuElement*> remote_elements
        = m_questionnaire->getElementsByTag(TAG_REMOTE, false);
    for (auto e : remote_elements) {
        e->setVisible(remote);
    }
}

void MiniAce::updateTaskVersionEditability()
{
    const bool editable = isChangingAddressVersionOk();
    m_questionnaire->setVisibleByTag(
        TAG_EL_CHOOSE_TASK_VERSION, editable, false, TAG_PG_PREAMBLE
    );
    m_questionnaire->setVisibleByTag(
        TAG_EL_SHOW_TASK_VERSION, !editable, false, TAG_PG_PREAMBLE
    );
}
