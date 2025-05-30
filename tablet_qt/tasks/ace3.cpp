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

A note on the address alternatives (2022-12-01):

- There are up to three versions of the ACE-III in a given language, versions
  A/B/C. They differ in their address for memory testing. The purpose is so
  that you can repeat without a practice effect for this aspect.
- The target address is presented as 7 components (e.g. Harry, Barnes, 73,
  Orchard, Close, Kingsbridge, Devon).
- The three memory phases are repetition/registration, free recall, and
  recognition (three cues/prompts are offered; one is exactly the right
  answer). "Recognition" is the preferred term (and matches the scoring guide);
  better than "cued recall" (normally that refers to an incomplete cue) or
  "prompted recall".
- The recognition version is presented as five lines, each with three
  alternatives (e.g. first line is Jerry Barnes / Harry Barnes / Harry
  Bradford).

For the English ACE-III, we could store 7 components and build up the
recognition versions by concatenation (e.g. "Harry" + " " + "Barnes"). However,
the recognition versons can differ a bit across languages (e.g. French "24 rue
du Bois" provides the alternatives "Rue du Bois", "Rue du Prince", "Place du
Marché"). There might be other differences (e.g. might word order change?).
Certainly the number/street order varies, e.g. Spanish "Calle Castillo 73".

So we'll store the target as 7 components and then 5x3 for the recognition.

Not all languages support A/B/C at present (e.g. Spanish), in which case the
string versions should be made identical.

Note also that the target/distractor order in the recognition is NOT
consistent across languages or even versions, e.g.

    English A/French A: correct columns 2, 2, 3, 2, 1
    English C:          correct columns 2, 3, 1, 1, 2
    Spanish:            correct columns 2, 3, 2, 2, 1

We could therefore store as rows/columns with an indication of which is
correct, or target/distractor 1/distractor 2 with an indication of which to put
where. The first is going to be simpler for administrators.

*/

/*

A note on the clazy-range-loop warning:

- This warning: https://www.kdab.com/blog-qasconst-and-stdas_const/
- Const vectors of non-const pointers: https://yosefk.com/c++fqa/const.html

*/

#define NOSCROLL_IMAGE_PAGES  // Should be defined. Better UI with it.

#include "ace3.h"

#include <QDebug>

#include "common/textconst.h"
#include "common/uiconst.h"
#include "lib/convert.h"
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
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quimage.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/quphoto.h"
#include "questionnairelib/quspacer.h"
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

const QString IMAGE_SPOON(QStringLiteral("ace3/spoon.png"));
const QString IMAGE_BOOK(QStringLiteral("ace3/book.png"));
const QString IMAGE_KANGAROO(QStringLiteral("ace3/kangaroo.png"));
const QString IMAGE_PENGUIN(QStringLiteral("ace3/penguin.png"));
const QString IMAGE_ANCHOR(QStringLiteral("ace3/anchor.png"));
const QString IMAGE_CAMEL(QStringLiteral("ace3/camel.png"));
const QString IMAGE_HARP(QStringLiteral("ace3/harp.png"));
const QString IMAGE_RHINOCEROS(QStringLiteral("ace3/rhinoceros.png"));
const QString IMAGE_BARREL(QStringLiteral("ace3/barrel.png"));
const QString IMAGE_CROWN(QStringLiteral("ace3/crown.png"));
const QString IMAGE_CROCODILE(QStringLiteral("ace3/crocodile.png"));
const QString IMAGE_ACCORDION(QStringLiteral("ace3/accordion.png"));
const QString IMAGE_INFINITY(QStringLiteral("ace3/infinity.png"));
const QString IMAGE_CUBE(QStringLiteral("ace3/cube.png"));
const QString IMAGE_DOTS8(QStringLiteral("ace3/dots8.png"));
const QString IMAGE_DOTS10(QStringLiteral("ace3/dots10.png"));
const QString IMAGE_DOTS7(QStringLiteral("ace3/dots7.png"));
const QString IMAGE_DOTS9(QStringLiteral("ace3/dots9.png"));
const QString IMAGE_K(QStringLiteral("ace3/k.png"));
const QString IMAGE_M(QStringLiteral("ace3/m.png"));
const QString IMAGE_A(QStringLiteral("ace3/a.png"));
const QString IMAGE_T(QStringLiteral("ace3/t.png"));

const QString TAG_PG_LANG_COMMANDS_SENTENCES(
    QStringLiteral("pg_lang_commands_sentences")
);
const QString TAG_PG_MEM_RECOGNITION(QStringLiteral("pg_mem_recog"));
const QString
    TAG_EL_LANG_OPTIONAL_COMMAND(QStringLiteral("lang_optional_command"));
const QString TAG_EL_LANG_NOT_SHOWN(QStringLiteral("lang_not_shown"));
const QString TAG_RECOG_REQUIRED(QStringLiteral("recog_required"));
const QString TAG_RECOG_SUPERFLUOUS(QStringLiteral("recog_superfluous"));

// Field names, field prefixes, and field counts
const int N_ATTN_TIME_ACE = 5;
const QString FP_ATTN_PLACE(QStringLiteral("attn_place"));
const int N_ATTN_PLACE = 5;
const QString FP_ATTN_REPEAT_WORD(QStringLiteral("attn_repeat_word"));
const int N_ATTN_REPEAT_WORD = 3;
const QString FN_ATTN_NUM_REGISTRATION_TRIALS(
    QStringLiteral("attn_num_registration_trials")
);
const QString FP_ATTN_SERIAL7(QStringLiteral("attn_serial7_subtraction"));
const int N_ATTN_SERIAL7 = 5;

const QString FP_MEM_RECALL_WORD(QStringLiteral("mem_recall_word"));
const int N_MEM_RECALL_WORD = 3;
const QString FN_FLUENCY_LETTERS_SCORE(QStringLiteral("fluency_letters_score")
);
const QString FN_FLUENCY_ANIMALS_SCORE(QStringLiteral("fluency_animals_score")
);
const QString FP_MEM_FAMOUS(QStringLiteral("mem_famous"));
const int N_MEM_FAMOUS = 4;
const QString
    FP_MEM_RECOGNIZE_ADDRESS_SCORE(QStringLiteral("mem_recognize_address"));
// ... SCORE; matches versions before 2.0.0
const QString FP_MEM_RECOGNIZE_ADDRESS_CHOICE(
    QStringLiteral("mem_recognize_address_choice")
);
// ... CHOICE; v2.0.0 onwards
// ... storing raw choices is new in v2.0.0, but the score field is preserved
//     for backwards compatibility
const int N_MEM_RECOGNIZE_ADDRESS = 5;
const int N_ADDRESS_RECOG_OPTIONS = 3;
const QVector<int> DEFAULT_ADDRESS_RECOG_CORRECT_COLS_ENGLISH_A{2, 2, 3, 2, 1};
// Choices for address recall phase:
const QChar CHOICE_A = 'A';
const QChar CHOICE_B = 'B';
const QChar CHOICE_C = 'C';

const QString FN_LANG_FOLLOW_CMD_PRACTICE(
    QStringLiteral("lang_follow_command_practice")
);
const QString FP_LANG_FOLLOW_CMD(QStringLiteral("lang_follow_command"));
const int N_LANG_FOLLOW_CMD = 3;
const QString FP_LANG_WRITE_SENTENCES_POINT(
    QStringLiteral("lang_write_sentences_point")
);
const int N_LANG_WRITE_SENTENCES_POINT = 2;
const QString FP_LANG_REPEAT_WORD(QStringLiteral("lang_repeat_word"));
const int N_LANG_REPEAT_WORD = 4;
const QString FP_LANG_REPEAT_SENTENCE(QStringLiteral("lang_repeat_sentence"));
const int N_LANG_REPEAT_SENTENCE = 2;
const QString FP_LANG_NAME_PICTURE(QStringLiteral("lang_name_picture"));
const int N_LANG_NAME_PICTURE = 12;
const QString FP_LANG_IDENTIFY_CONCEPT(QStringLiteral("lang_identify_concept")
);
const int N_LANG_IDENTIFY_CONCEPT = 4;
const QString FN_LANG_READ_WORDS_ALOUD(QStringLiteral("lang_read_words_aloud")
);

const QString FN_VSP_COPY_INFINITY(QStringLiteral("vsp_copy_infinity"));
const QString FN_VSP_COPY_CUBE(QStringLiteral("vsp_copy_cube"));
const QString FP_VSP_COUNT_DOTS(QStringLiteral("vsp_count_dots"));
const int N_VSP_COUNT_DOTS = 4;
const QString FP_VSP_IDENTIFY_LETTER(QStringLiteral("vsp_identify_letter"));
const int N_VSP_IDENTIFY_LETTER = 4;

// Subtotals. No magic numbers...
const int TOTAL_ATTN = 18;
const int TOTAL_MEM = 26;
const int TOTAL_FLUENCY = 14;
const int TOTAL_LANG = 26;
const int TOTAL_VSP = 16;
const int TOTAL_OVERALL = 100;

// xstrings
const QString X_EDITION(QStringLiteral("edition"));

// ============================================================================
// Ace3
// ============================================================================

void initializeAce3(TaskFactory& factory)
{
    static TaskRegistrar<Ace3> registered(factory);
}

Ace3::Ace3(
    CamcopsApp& app, DatabaseManager& db, const int load_pk, QObject* parent
) :
    AceFamily(app, db, ACE3_TABLENAME, parent)
{
    addField(
        FN_TASK_EDITION,
        QMetaType::fromType<QString>(),
        false,
        false,
        false,
        xstring(X_EDITION)
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
        strseq(FP_ATTN_TIME, 1, N_ATTN_TIME_ACE), QMetaType::fromType<int>()
    );
    addFields(
        strseq(FP_ATTN_PLACE, 1, N_ATTN_PLACE), QMetaType::fromType<int>()
    );
    addFields(
        strseq(FP_ATTN_REPEAT_WORD, 1, N_ATTN_REPEAT_WORD),
        QMetaType::fromType<int>()
    );
    addField(FN_ATTN_NUM_REGISTRATION_TRIALS, QMetaType::fromType<int>());
    addFields(
        strseq(FP_ATTN_SERIAL7, 1, N_ATTN_SERIAL7), QMetaType::fromType<int>()
    );

    addFields(
        strseq(FP_MEM_RECALL_WORD, 1, N_MEM_RECALL_WORD),
        QMetaType::fromType<int>()
    );

    addField(FN_FLUENCY_LETTERS_SCORE, QMetaType::fromType<int>());
    addField(FN_FLUENCY_ANIMALS_SCORE, QMetaType::fromType<int>());

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
    addFields(
        strseq(FP_MEM_FAMOUS, 1, N_MEM_FAMOUS), QMetaType::fromType<int>()
    );

    addField(FN_LANG_FOLLOW_CMD_PRACTICE, QMetaType::fromType<int>());
    addFields(
        strseq(FP_LANG_FOLLOW_CMD, 1, N_LANG_FOLLOW_CMD),
        QMetaType::fromType<int>()
    );
    addFields(
        strseq(FP_LANG_WRITE_SENTENCES_POINT, 1, N_LANG_WRITE_SENTENCES_POINT),
        QMetaType::fromType<int>()
    );
    addFields(
        strseq(FP_LANG_REPEAT_WORD, 1, N_LANG_REPEAT_WORD),
        QMetaType::fromType<int>()
    );
    addFields(
        strseq(FP_LANG_REPEAT_SENTENCE, 1, N_LANG_REPEAT_SENTENCE),
        QMetaType::fromType<int>()
    );
    addFields(
        strseq(FP_LANG_NAME_PICTURE, 1, N_LANG_NAME_PICTURE),
        QMetaType::fromType<int>()
    );
    addFields(
        strseq(FP_LANG_IDENTIFY_CONCEPT, 1, N_LANG_IDENTIFY_CONCEPT),
        QMetaType::fromType<int>()
    );
    addField(FN_LANG_READ_WORDS_ALOUD, QMetaType::fromType<int>());

    addField(FN_VSP_COPY_INFINITY, QMetaType::fromType<int>());
    addField(FN_VSP_COPY_CUBE, QMetaType::fromType<int>());
    addField(FN_VSP_DRAW_CLOCK, QMetaType::fromType<int>());
    addFields(
        strseq(FP_VSP_COUNT_DOTS, 1, N_VSP_COUNT_DOTS),
        QMetaType::fromType<int>()
    );
    addFields(
        strseq(FP_VSP_IDENTIFY_LETTER, 1, N_VSP_IDENTIFY_LETTER),
        QMetaType::fromType<int>()
    );

    addFields(
        strseq(FP_MEM_RECALL_ADDRESS, 1, N_MEM_REPEAT_RECALL_ADDR),
        QMetaType::fromType<int>()
    );
    addFields(
        strseq(FP_MEM_RECOGNIZE_ADDRESS_SCORE, 1, N_MEM_RECOGNIZE_ADDRESS),
        QMetaType::fromType<int>()
    );
    addFields(
        strseq(FP_MEM_RECOGNIZE_ADDRESS_CHOICE, 1, N_MEM_RECOGNIZE_ADDRESS),
        QMetaType::fromType<QChar>()
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

QString Ace3::shortname() const
{
    return QStringLiteral("ACE-III");
}

QString Ace3::longname() const
{
    return tr("Addenbrooke’s Cognitive Examination, revision 3");
}

QString Ace3::description() const
{
    return tr(
        "100-point clinician-administered assessment of attention/"
        "orientation, memory, fluency, language, and visuospatial "
        "domains."
    );
}

bool Ace3::isTaskProperlyCreatable(QString& why_not_creatable) const
{
    if (!AceFamily::isTaskProperlyCreatable(why_not_creatable)) {
        return false;
    }
    if (!isAddressRecogCorrectColumnInfoValid()) {
        why_not_creatable = tr(
            "Server strings are not providing valid information about which "
            "address components are correct. Try re-fetching server info."
        );
        return false;
    }
    return true;
}

// ============================================================================
// Instance info
// ============================================================================

bool Ace3::isComplete() const
{
    return noneNull(values(strseq(FP_ATTN_TIME, 1, N_ATTN_TIME_ACE)))
        && noneNull(values(strseq(FP_ATTN_PLACE, 1, N_ATTN_PLACE)))
        && noneNull(values(strseq(FP_ATTN_REPEAT_WORD, 1, N_ATTN_REPEAT_WORD)))
        && noneNull(values(strseq(FP_ATTN_SERIAL7, 1, N_ATTN_SERIAL7)))
        && noneNull(values(strseq(FP_MEM_RECALL_WORD, 1, N_MEM_RECALL_WORD)))
        && !valueIsNull(FN_FLUENCY_LETTERS_SCORE)
        && !valueIsNull(FN_FLUENCY_ANIMALS_SCORE)
        && noneNull(values(
            strseq(FP_MEM_REPEAT_ADDR_TRIAL3, 1, N_MEM_REPEAT_RECALL_ADDR)
        ))
        && noneNull(values(strseq(FP_MEM_FAMOUS, 1, N_MEM_FAMOUS)))
        && !valueIsNull(FN_LANG_FOLLOW_CMD_PRACTICE)
        && (eq(value(FN_LANG_FOLLOW_CMD_PRACTICE), 0)
            || noneNull(values(strseq(FP_LANG_FOLLOW_CMD, 1, N_LANG_FOLLOW_CMD)
            )))
        &&
        // ... failed practice, or completed all three actual tests
        noneNull(values(strseq(
            FP_LANG_WRITE_SENTENCES_POINT, 1, N_LANG_WRITE_SENTENCES_POINT
        )))
        && noneNull(values(strseq(FP_LANG_REPEAT_WORD, 1, N_LANG_REPEAT_WORD)))
        && noneNull(values(
            strseq(FP_LANG_REPEAT_SENTENCE, 1, N_LANG_REPEAT_SENTENCE)
        ))
        && noneNull(values(strseq(FP_LANG_NAME_PICTURE, 1, N_LANG_NAME_PICTURE)
        ))
        && noneNull(values(
            strseq(FP_LANG_IDENTIFY_CONCEPT, 1, N_LANG_IDENTIFY_CONCEPT)
        ))
        && !valueIsNull(FN_LANG_READ_WORDS_ALOUD)
        && !valueIsNull(FN_VSP_COPY_INFINITY) && !valueIsNull(FN_VSP_COPY_CUBE)
        && !valueIsNull(FN_VSP_DRAW_CLOCK)
        && noneNull(values(strseq(FP_VSP_COUNT_DOTS, 1, N_VSP_COUNT_DOTS)))
        && noneNull(
               values(strseq(FP_VSP_IDENTIFY_LETTER, 1, N_VSP_IDENTIFY_LETTER))
        )
        && noneNull(values(
            strseq(FP_MEM_RECALL_ADDRESS, 1, N_MEM_REPEAT_RECALL_ADDR)
        ))
        && isRecognitionComplete();
}

QStringList Ace3::summary() const
{
    const int a = getAttnScore();
    const int m = getMemScore();
    const int f = getFluencyScore();
    const int l = getLangScore();
    const int v = getVisuospatialScore();
    const int t = a + m + f + l + v;
    const int mini = miniAceScore();
    QStringList lines;
    lines.append(totalScorePhrase(t, TOTAL_OVERALL));
    lines.append(
        xstring(QStringLiteral("cat_attn")) + scorePercent(a, TOTAL_ATTN)
    );
    lines.append(
        xstring(QStringLiteral("cat_mem")) + scorePercent(m, TOTAL_MEM)
    );
    lines.append(
        xstring(QStringLiteral("cat_fluency")) + scorePercent(f, TOTAL_FLUENCY)
    );
    lines.append(
        xstring(QStringLiteral("cat_lang")) + scorePercent(l, TOTAL_LANG)
    );
    lines.append(
        xstring(QStringLiteral("cat_vsp")) + scorePercent(v, TOTAL_VSP)
    );
    lines.append(
        xstring(X_MINI_ACE_SCORE) + scorePercent(mini, TOTAL_MINI_ACE)
    );
    return lines;
}

OpenableWidget* Ace3::editor(const bool read_only)
{
    int pagenum = 1;
    auto makeTitle = [this, &pagenum](const QString& title) -> QString {
        return xstring(QStringLiteral("title_prefix"))
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
             heading(X_EDITION),
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
             remInstruct(QStringLiteral("instruction_remote_read_first")),
             stdInstruct(QStringLiteral("instruction_need_paper")),
             remInstruct(QStringLiteral("instruction_need_paper_remote")),
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
    // Attention/orientation/three word recall
    // ------------------------------------------------------------------------

    const QDateTime now = datetime::now();
    QString season;
    switch (datetime::now().date().month()) {
            // 1 = Jan, 12 = Dec
        case 12:
        case 1:
        case 2:
            season = xstring(QStringLiteral("season_winter"));
            break;
        case 3:
        case 4:
        case 5:
            season = xstring(QStringLiteral("season_spring"));
            break;
        case 6:
        case 7:
        case 8:
            season = xstring(QStringLiteral("season_summer"));
            break;
        case 9:
        case 10:
        case 11:
            season = xstring(QStringLiteral("season_autumn"));
            break;
        default:
            season = QStringLiteral("?(season_bug)");
            break;
    }
    const QString correct_date = "     "
        + now.toString(QStringLiteral("dddd d MMMM yyyy")) + "; " + season;
    // ... e.g. "Monday 2 January 2016; winter";
    // https://doc.qt.io/qt-6.5/qdate.html#toString

    const NameValueOptions options_registration{
        {"1", 1},
        {"2", 2},
        {"3", 3},
        {"4", 4},
        {">4", 0},
    };
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
                 boolean(
                     QStringLiteral("attn_time5"), strnum(FP_ATTN_TIME, 5)
                 ),
             },
             explanation(QStringLiteral("instruction_time")),
             (new QuText(correct_date))->setItalic(),
             instruction(QStringLiteral("attn_q_place")),
             new QuFlowContainer{
                 boolean(
                     QStringLiteral("attn_place1"), strnum(FP_ATTN_PLACE, 1)
                 ),
                 boolean(
                     QStringLiteral("attn_place2"), strnum(FP_ATTN_PLACE, 2)
                 ),
                 boolean(
                     QStringLiteral("attn_place3"), strnum(FP_ATTN_PLACE, 3)
                 ),
                 boolean(
                     QStringLiteral("attn_place4"), strnum(FP_ATTN_PLACE, 4)
                 ),
                 boolean(
                     QStringLiteral("attn_place5"), strnum(FP_ATTN_PLACE, 5)
                 ),
             },
             explanation(QStringLiteral("instruction_place")),

             // Lemon, key, ball (registration)
             heading(QStringLiteral("cat_attn")),
             instruction(QStringLiteral("attn_q_words")),
             explanation(QStringLiteral("attn_instruction_words")),
             new QuFlowContainer{
                 boolean(
                     QStringLiteral("mem_word1"),
                     strnum(FP_ATTN_REPEAT_WORD, 1)
                 ),
                 boolean(
                     QStringLiteral("mem_word2"),
                     strnum(FP_ATTN_REPEAT_WORD, 2)
                 ),
                 boolean(
                     QStringLiteral("mem_word3"),
                     strnum(FP_ATTN_REPEAT_WORD, 3)
                 ),
             },
             new QuFlowContainer{
                 text(QStringLiteral("attn_q_register_n_trials")),
                 (new QuMcq(
                      fieldRef(FN_ATTN_NUM_REGISTRATION_TRIALS, false),
                      options_registration
                  ))
                     ->setHorizontal(true),
                 // ... not mandatory
             },

             // Serial 7s
             heading(QStringLiteral("cat_attn")),
             instruction(QStringLiteral("attn_q_serial_sevens")),
             explanation(QStringLiteral("attn_instruction_sevens")),
             new QuFlowContainer{
                 boolean(
                     QStringLiteral("attn_subtraction1"),
                     strnum(FP_ATTN_SERIAL7, 1)
                 ),
                 boolean(
                     QStringLiteral("attn_subtraction2"),
                     strnum(FP_ATTN_SERIAL7, 2)
                 ),
                 boolean(
                     QStringLiteral("attn_subtraction3"),
                     strnum(FP_ATTN_SERIAL7, 3)
                 ),
                 boolean(
                     QStringLiteral("attn_subtraction4"),
                     strnum(FP_ATTN_SERIAL7, 4)
                 ),
                 boolean(
                     QStringLiteral("attn_subtraction5"),
                     strnum(FP_ATTN_SERIAL7, 5)
                 ),
             },

             // Lemon, key, ball (recall)
             heading(QStringLiteral("cat_mem")),
             instruction(QStringLiteral("mem_q_recall_words")),
             explanation(QStringLiteral("mem_instruction_recall")),
             new QuFlowContainer{
                 boolean(
                     QStringLiteral("mem_word1"), strnum(FP_MEM_RECALL_WORD, 1)
                 ),
                 boolean(
                     QStringLiteral("mem_word2"), strnum(FP_MEM_RECALL_WORD, 2)
                 ),
                 boolean(
                     QStringLiteral("mem_word3"), strnum(FP_MEM_RECALL_WORD, 3)
                 ),
             },
         })
            ->setTitle(makeTitle(tr("Attention")))
            ->setType(QuPage::PageType::Clinician)
    );

    // ------------------------------------------------------------------------
    // Fluency
    // ------------------------------------------------------------------------

    const NameValueOptions options_fluency_letters{
        {"0–1", 0},
        {"2–3", 1},
        {"4–5", 2},
        {"6–7", 3},
        {"8–10", 4},
        {"11–13", 5},
        {"14–17", 6},
        {"≥18", 7}

    };
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

             // Letters
             subheading(QStringLiteral("fluency_subhead_letters")),
             instruction(QStringLiteral("fluency_q_letters")),
             new QuCountdown(FLUENCY_TIME_SEC),
             explanation(QStringLiteral("fluency_instruction_letters")),
             text(QStringLiteral("fluency_prompt_letters_cor")),
             (new QuMcq(
                  fieldRef(FN_FLUENCY_LETTERS_SCORE), options_fluency_letters
              ))
                 ->setHorizontal(true),
             new QuSpacer(),

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
    // Learning the address; famous people
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

             // Famous people
             heading(QStringLiteral("cat_mem")),
             boolean(
                 QStringLiteral("famous_1"),
                 strnum(FP_MEM_FAMOUS, 1),
                 true,
                 true
             ),
             boolean(
                 QStringLiteral("famous_2"),
                 strnum(FP_MEM_FAMOUS, 2),
                 true,
                 true
             ),
             boolean(
                 QStringLiteral("famous_3"),
                 strnum(FP_MEM_FAMOUS, 3),
                 true,
                 true
             ),
             boolean(
                 QStringLiteral("famous_4"),
                 strnum(FP_MEM_FAMOUS, 4),
                 true,
                 true
             ),
             explanation(QStringLiteral("instruction_famous")),
         })
            ->setTitle(makeTitle(tr("Address learning; famous people")))
            ->addTag(TAG_PG_ADDRESS_LEARNING_FAMOUS)
            ->setType(QuPage::PageType::Clinician)
    );

    // ------------------------------------------------------------------------
    // Commands; writing sentences
    // ------------------------------------------------------------------------

    QuPagePtr page_commands_sentences(
        (new QuPage{
             heading(QStringLiteral("cat_lang")),
             stdInstruct(QStringLiteral("lang_q_command_1")),
             remInstruct(QStringLiteral("lang_q_command_1_remote")),
             boolean(
                 QStringLiteral("lang_command_practice"),
                 FN_LANG_FOLLOW_CMD_PRACTICE,
                 true,
                 true
             ),
             stdExplan(QStringLiteral("lang_q_command_2")),
             remExplan(QStringLiteral("lang_q_command_2_remote")),
             boolean(
                 QStringLiteral("lang_command1"),
                 strnum(FP_LANG_FOLLOW_CMD, 1),
                 true,
                 true
             )
                 ->addTag(TAG_EL_LANG_OPTIONAL_COMMAND),
             boolean(
                 QStringLiteral("lang_command2"),
                 strnum(FP_LANG_FOLLOW_CMD, 2),
                 true,
                 true
             )
                 ->addTag(TAG_EL_LANG_OPTIONAL_COMMAND),
             boolean(
                 QStringLiteral("lang_command3"),
                 strnum(FP_LANG_FOLLOW_CMD, 3),
                 true,
                 true
             )
                 ->addTag(TAG_EL_LANG_OPTIONAL_COMMAND),
             warning(
                 tr("Other commands not shown; subject failed practice trial.")
             )
                 ->addTag(TAG_EL_LANG_NOT_SHOWN),
             heading(QStringLiteral("cat_lang")),
             remInstruct(QStringLiteral("lang_instruction_remote_keep_paper")),
             // ... explicitly before the sentence section in the original
             remInstruct(
                 QStringLiteral("lang_instruction_remote_camera_to_paper")
             ),
             instruction(QStringLiteral("lang_q_sentences")),
             boolean(
                 QStringLiteral("lang_sentences_point1"),
                 strnum(FP_LANG_WRITE_SENTENCES_POINT, 1)
             ),
             boolean(
                 QStringLiteral("lang_sentences_point2"),
                 strnum(FP_LANG_WRITE_SENTENCES_POINT, 2)
             ),
             remInstruct(QStringLiteral("lang_instruction_remote_remove_paper")
             ),
         })
            ->setTitle(makeTitle(tr("Commands; writing sentences")))
            ->addTag(TAG_PG_LANG_COMMANDS_SENTENCES)
            ->setType(QuPage::PageType::Clinician)
    );

    // ------------------------------------------------------------------------
    // Repetition; preparing clinician for pictures
    // ------------------------------------------------------------------------

    QuPagePtr page_repetition(
        (new QuPage{
             // Repeating words
             heading(QStringLiteral("cat_lang")),
             instruction(QStringLiteral("lang_q_repeat")),
             boolean(
                 QStringLiteral("lang_repeat_word1"),
                 strnum(FP_LANG_REPEAT_WORD, 1)
             ),
             boolean(
                 QStringLiteral("lang_repeat_word2"),
                 strnum(FP_LANG_REPEAT_WORD, 2)
             ),
             boolean(
                 QStringLiteral("lang_repeat_word3"),
                 strnum(FP_LANG_REPEAT_WORD, 3)
             ),
             boolean(
                 QStringLiteral("lang_repeat_word4"),
                 strnum(FP_LANG_REPEAT_WORD, 4)
             ),
             explanation(QStringLiteral("lang_instruction_repeat")),
             // Repeating sentences
             heading(QStringLiteral("cat_lang")),
             instruction(QStringLiteral("lang_q_repeat")),
             boolean(
                 QStringLiteral("lang_sentence1"),
                 strnum(FP_LANG_REPEAT_SENTENCE, 1)
             ),
             boolean(
                 QStringLiteral("lang_sentence2"),
                 strnum(FP_LANG_REPEAT_SENTENCE, 2)
             ),
             explanation(QStringLiteral("lang_instruction_sentences_1")),
             explanation(QStringLiteral("lang_instruction_sentences_2")),
             new QuSpacer(),
             // Preparation for clinician for pictures
             instruction(QStringLiteral("advance_warning_1")),
             explanation(QStringLiteral("advance_warning_2")),
             explanation(QStringLiteral("advance_warning_3")),
             explanation(QStringLiteral("advance_warning_4")),
             explanation(QStringLiteral("advance_warning_5")),
             explanation(QStringLiteral("advance_warning_6")),
             explanation(QStringLiteral("advance_warning_7")),
             explanation(QStringLiteral("advance_warning_8")),
         })
            ->setTitle(makeTitle(tr("Repetition")))
            ->setType(QuPage::PageType::Clinician)
    );

    // ------------------------------------------------------------------------
    // Naming pictures
    // ------------------------------------------------------------------------

    QuPagePtr page_name_pictures(
        (new QuPage{
             // Naming pictures
             heading(QStringLiteral("cat_lang")),
             remInstruct(QStringLiteral("lang_instruction_remote_share_screen")
             ),
             stdInstruct(QStringLiteral("lang_q_identify_pic")),
             remInstruct(QStringLiteral("lang_q_identify_pic_remote")),
             new QuGridContainer(
                 3,
                 {
                     boolimg(IMAGE_SPOON, strnum(FP_LANG_NAME_PICTURE, 1)),
                     boolimg(IMAGE_BOOK, strnum(FP_LANG_NAME_PICTURE, 2)),
                     boolimg(IMAGE_KANGAROO, strnum(FP_LANG_NAME_PICTURE, 3)),
                     boolimg(IMAGE_PENGUIN, strnum(FP_LANG_NAME_PICTURE, 4)),
                     boolimg(IMAGE_ANCHOR, strnum(FP_LANG_NAME_PICTURE, 5)),
                     boolimg(IMAGE_CAMEL, strnum(FP_LANG_NAME_PICTURE, 6)),
                     boolimg(IMAGE_HARP, strnum(FP_LANG_NAME_PICTURE, 7)),
                     boolimg(
                         IMAGE_RHINOCEROS, strnum(FP_LANG_NAME_PICTURE, 8)
                     ),
                     boolimg(IMAGE_BARREL, strnum(FP_LANG_NAME_PICTURE, 9)),
                     boolimg(IMAGE_CROWN, strnum(FP_LANG_NAME_PICTURE, 10)),
                     boolimg(
                         IMAGE_CROCODILE, strnum(FP_LANG_NAME_PICTURE, 11)
                     ),
                     boolimg(
                         IMAGE_ACCORDION, strnum(FP_LANG_NAME_PICTURE, 12)
                     ),
                 }
             ),
             // Choosing pictures by concept
             // ... standard version:
             stdInstruct(QStringLiteral("lang_q_identify_concept")),
             boolean(
                 QStringLiteral("lang_concept1"),
                 strnum(FP_LANG_IDENTIFY_CONCEPT, 1)
             )
                 ->addTag(TAG_STANDARD),
             boolean(
                 QStringLiteral("lang_concept2"),
                 strnum(FP_LANG_IDENTIFY_CONCEPT, 2)
             )
                 ->addTag(TAG_STANDARD),
             boolean(
                 QStringLiteral("lang_concept3"),
                 strnum(FP_LANG_IDENTIFY_CONCEPT, 3)
             )
                 ->addTag(TAG_STANDARD),
             boolean(
                 QStringLiteral("lang_concept4"),
                 strnum(FP_LANG_IDENTIFY_CONCEPT, 4)
             )
                 ->addTag(TAG_STANDARD),
             // ... remote version (same fields):
             remInstruct(QStringLiteral("lang_q_identify_concept_remote")),
             boolean(
                 QStringLiteral("lang_concept1_remote"),
                 strnum(FP_LANG_IDENTIFY_CONCEPT, 1)
             )
                 ->addTag(TAG_REMOTE),
             boolean(
                 QStringLiteral("lang_concept2_remote"),
                 strnum(FP_LANG_IDENTIFY_CONCEPT, 2)
             )
                 ->addTag(TAG_REMOTE),
             boolean(
                 QStringLiteral("lang_concept3_remote"),
                 strnum(FP_LANG_IDENTIFY_CONCEPT, 3)
             )
                 ->addTag(TAG_REMOTE),
             boolean(
                 QStringLiteral("lang_concept4_remote"),
                 strnum(FP_LANG_IDENTIFY_CONCEPT, 4)
             )
                 ->addTag(TAG_REMOTE),
             explanation(QStringLiteral("lang_instruction_identify_concept")),
         })
            ->setTitle(makeTitle(tr("Naming pictures")))
#ifdef NOSCROLL_IMAGE_PAGES
            ->allowScroll(false, true)  // no scrolling; zoomable
#endif
            ->setType(QuPage::PageType::ClinicianWithPatient)
    );

    // ------------------------------------------------------------------------
    // Reading irregular words
    // ------------------------------------------------------------------------

    QuPagePtr page_read_words_aloud(
        (new QuPage{
             // Reading irregular words aloud
             heading(QStringLiteral("cat_lang")),
             stdInstruct(QStringLiteral("lang_q_read_aloud")),
             remInstruct(QStringLiteral("lang_q_read_aloud_remote")),
             new QuSpacer(),
             subheading(QStringLiteral("lang_read_aloud_words")),  // the words
             new QuSpacer(),
             boolean(
                 QStringLiteral("lang_read_aloud_all_correct"),
                 FN_LANG_READ_WORDS_ALOUD
             ),
             stdExplan(QStringLiteral("lang_instruction_read_aloud")),
         })
            ->setTitle(makeTitle(tr("Reading irregular words")))
            ->setType(QuPage::PageType::ClinicianWithPatient)
    );

    // ------------------------------------------------------------------------
    // Infinity
    // ------------------------------------------------------------------------

    QuPagePtr page_infinity(
        (new QuPage{
             heading(QStringLiteral("cat_vsp")),
             stdInstruct(QStringLiteral("vsp_q_infinity")),
             remInstruct(QStringLiteral("vsp_q_infinity_remote")),
             new QuImage(uifunc::resourceFilename(IMAGE_INFINITY)),
             boolean(
                 QStringLiteral("vsp_infinity_correct"), FN_VSP_COPY_INFINITY
             ),
         })
            ->setTitle(makeTitle(tr("Infinity")))
            ->setType(QuPage::PageType::ClinicianWithPatient)
    );

    // ------------------------------------------------------------------------
    // Cube
    // ------------------------------------------------------------------------

    const NameValueOptions options_cube = NameValueOptions::makeNumbers(0, 2);
    QuPagePtr page_cube(
        (new QuPage{
             stdInstruct(QStringLiteral("vsp_q_cube")),
             remInstruct(QStringLiteral("vsp_q_cube_remote")),
             new QuImage(uifunc::resourceFilename(IMAGE_CUBE)),
             text(QStringLiteral("vsp_score_cube")),
             (new QuMcq(fieldRef(FN_VSP_COPY_CUBE), options_cube))
                 ->setHorizontal(true),
         })
            ->setTitle(makeTitle(tr("Cube")))
            ->setType(QuPage::PageType::ClinicianWithPatient)
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
    // Dots
    // ------------------------------------------------------------------------

    QuPagePtr page_dots(
        (new QuPage{
             heading(QStringLiteral("cat_vsp")),
             stdInstruct(QStringLiteral("vsp_q_dots")),
             remInstruct(QStringLiteral("vsp_q_dots_remote")),
             new QuGridContainer(
                 2,
                 {
                     boolimg(IMAGE_DOTS8, strnum(FP_VSP_COUNT_DOTS, 1)),
                     boolimg(IMAGE_DOTS10, strnum(FP_VSP_COUNT_DOTS, 2)),
                     boolimg(IMAGE_DOTS7, strnum(FP_VSP_COUNT_DOTS, 3)),
                     boolimg(IMAGE_DOTS9, strnum(FP_VSP_COUNT_DOTS, 4)),
                 }
             ),
         })
            ->setTitle(makeTitle(tr("Dot counting")))
#ifdef NOSCROLL_IMAGE_PAGES
            ->allowScroll(false, true)  // no scrolling; zoomable
#endif
            ->setType(QuPage::PageType::ClinicianWithPatient)
    );

    // ------------------------------------------------------------------------
    // Letters
    // ------------------------------------------------------------------------

    QuPagePtr page_letters(
        (new QuPage{
             heading(QStringLiteral("cat_vsp")),
             stdInstruct(QStringLiteral("vsp_q_letters")),
             remInstruct(QStringLiteral("vsp_q_letters_remote")),
             new QuGridContainer(
                 2,
                 {
                     boolimg(IMAGE_K, strnum(FP_VSP_IDENTIFY_LETTER, 1)),
                     boolimg(IMAGE_M, strnum(FP_VSP_IDENTIFY_LETTER, 2)),
                     boolimg(IMAGE_A, strnum(FP_VSP_IDENTIFY_LETTER, 3)),
                     boolimg(IMAGE_T, strnum(FP_VSP_IDENTIFY_LETTER, 4)),
                 }
             ),
         })
            ->setTitle(makeTitle(tr("Noisy letters")))
#ifdef NOSCROLL_IMAGE_PAGES
            ->allowScroll(false, true)  // no scrolling; zoomable
#endif
            ->setType(QuPage::PageType::ClinicianWithPatient)
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
    // Address recall: recognition
    // ------------------------------------------------------------------------

    const QStringList address_component_titles{
        tr("Name:"),
        tr("Number:"),
        tr("Street:"),
        tr("Town:"),
        tr("County:"),
    };
    QVector<QuElement*> recog_elements;
    recog_elements.reserve(4);
    recog_elements.append(instruction(QStringLiteral("no_need_for_extra_recall"
                                      ))
                              ->addTag(TAG_RECOG_SUPERFLUOUS));
    recog_elements.append(instruction(QStringLiteral("mem_q_recognize_address")
    )
                              ->addTag(TAG_RECOG_REQUIRED));
    for (int line = 1; line <= N_MEM_RECOGNIZE_ADDRESS; ++line) {
        const NameValueOptions options_recog = getAddressRecogOptions(line);
        FieldRefPtr fr_recog
            = fieldRef(strnum(FP_MEM_RECOGNIZE_ADDRESS_CHOICE, line));
        connect(
            fr_recog.data(),
            &FieldRef::valueChanged,
            this,
            &Ace3::updateAddressRecognition
        );
        const QString tag = tagAddressRecog(line);
        // The mini-prompt, like "Name:":
        const int line_idx = line - 1;
        recog_elements.append(
            textRaw(address_component_titles[line_idx])->addTag(tag)
        );
        // The MCQ element:
        recog_elements.append((new QuMcq(fr_recog, options_recog))
                                  ->setHorizontal(true)
                                  ->addTag(tag));
    }
    QuPagePtr page_recog_address((new QuPage(recog_elements))
                                     ->setTitle(makeTitle(tr("Recognition")))
                                     ->addTag(TAG_PG_MEM_RECOGNITION)
                                     ->setType(QuPage::PageType::Clinician));

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
             explanation(QStringLiteral("picture_instruction2")),
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
             explanation(QStringLiteral("picture_instruction2")),
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
            page_fluency,
            page_repeat_addr_famous,
            page_commands_sentences,
            page_repetition,
            page_name_pictures,
            page_read_words_aloud,
            page_infinity,
            page_cube,
            page_clock,
            page_dots,
            page_letters,
            page_back_to_clinician,
            page_recall_address_free,
            page_recog_address,
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
        &Ace3::updateTaskVersionAddresses
    );
    updateTaskVersionAddresses();

    // When the user changes the remote administration status.
    FieldRefPtr fr_remote = fieldRef(FN_REMOTE_ADMINISTRATION);
    connect(
        fr_remote.data(),
        &FieldRef::valueChanged,
        this,
        &Ace3::showStandardOrRemoteInstructions
    );
    showStandardOrRemoteInstructions();

    // When the user writes data relating to a specific address, locking in
    // the address version selection. See isChangingAddressVersionOk().
    for (int i = 1; i <= N_MEM_REPEAT_RECALL_ADDR; ++i) {
        connect(
            fieldRef(strnum(FP_MEM_REPEAT_ADDR_TRIAL1, i)).data(),
            &FieldRef::valueChanged,
            this,
            &Ace3::updateTaskVersionEditability
        );
        connect(
            fieldRef(strnum(FP_MEM_REPEAT_ADDR_TRIAL2, i)).data(),
            &FieldRef::valueChanged,
            this,
            &Ace3::updateTaskVersionEditability
        );
        connect(
            fieldRef(strnum(FP_MEM_REPEAT_ADDR_TRIAL3, i)).data(),
            &FieldRef::valueChanged,
            this,
            &Ace3::updateTaskVersionEditability
        );
    }
    for (int i = 1; i <= N_MEM_REPEAT_RECALL_ADDR; ++i) {
        connect(
            fieldRef(strnum(FP_MEM_RECALL_ADDRESS, i)).data(),
            &FieldRef::valueChanged,
            this,
            &Ace3::updateTaskVersionEditability
        );
    }
    for (int i = 1; i <= N_MEM_RECOGNIZE_ADDRESS; ++i) {
        connect(
            fieldRef(strnum(FP_MEM_RECOGNIZE_ADDRESS_CHOICE, i)).data(),
            &FieldRef::valueChanged,
            this,
            &Ace3::updateTaskVersionEditability
        );
    }
    updateTaskVersionEditability();

    // When the user enters data for the practice command to follow,
    // determining whether we need to bother with other commands.
    FieldRefPtr fr_lang_practice = fieldRef(FN_LANG_FOLLOW_CMD_PRACTICE);
    connect(
        fr_lang_practice.data(),
        &FieldRef::valueChanged,
        this,
        &Ace3::langPracticeChanged
    );
    langPracticeChanged(fr_lang_practice.data());

    // When the user enters data for some aspect of address recall, determining
    // whether we need to bother with recognition for that part of the address.
    for (int i = 1; i <= N_MEM_REPEAT_RECALL_ADDR; ++i) {
        FieldRefPtr fr = fieldRef(strnum(FP_MEM_RECALL_ADDRESS, i));
        connect(
            fr.data(),
            &FieldRef::valueChanged,
            this,
            &Ace3::updateAddressRecognition
        );
    }
    updateAddressRecognition();

    // ------------------------------------------------------------------------
    // Done
    // ------------------------------------------------------------------------

    return m_questionnaire;
}

// ============================================================================
// Task-specific calculations
// ============================================================================

int Ace3::getAttnScore() const
{
    return sumInt(values(
        strseq(FP_ATTN_TIME, 1, N_ATTN_TIME_ACE)
        + strseq(FP_ATTN_PLACE, 1, N_ATTN_PLACE)
        + strseq(FP_ATTN_REPEAT_WORD, 1, N_ATTN_REPEAT_WORD)
        + strseq(FP_ATTN_SERIAL7, 1, N_ATTN_SERIAL7)
    ));
}

int Ace3::getMemScore() const
{
    return sumInt(values(
               strseq(FP_MEM_RECALL_WORD, 1, N_MEM_RECALL_WORD)
               + strseq(FP_MEM_REPEAT_ADDR_TRIAL3, 1, N_MEM_REPEAT_RECALL_ADDR)
               + strseq(FP_MEM_FAMOUS, 1, N_MEM_FAMOUS)
               + strseq(FP_MEM_RECALL_ADDRESS, 1, N_MEM_REPEAT_RECALL_ADDR)
           ))
        + getMemRecognitionScore();
}

int Ace3::getFluencyScore() const
{
    return valueInt(FN_FLUENCY_LETTERS_SCORE)
        + valueInt(FN_FLUENCY_ANIMALS_SCORE);
}

int Ace3::getLangScore() const
{
    return getFollowCommandScore()
        + sumInt(values(strseq(
            FP_LANG_WRITE_SENTENCES_POINT, 1, N_LANG_WRITE_SENTENCES_POINT
        )))
        + getRepeatWordScore()
        + sumInt(values(
            strseq(FP_LANG_REPEAT_SENTENCE, 1, N_LANG_REPEAT_SENTENCE)
        ))
        + sumInt(values(strseq(FP_LANG_NAME_PICTURE, 1, N_LANG_NAME_PICTURE)))
        + sumInt(values(
            strseq(FP_LANG_IDENTIFY_CONCEPT, 1, N_LANG_IDENTIFY_CONCEPT)
        ))
        + valueInt(FN_LANG_READ_WORDS_ALOUD);
    /*
        Follow commands = 3 points
        Write sentences = 2 points
        Repeat words = 2 points
        Repeat sentences = 2 points
        Name pictures = 12 points
        Identify concepts = 4 points
        Read words aloud = 1 point
    */
}

int Ace3::getVisuospatialScore() const
{
    return valueInt(FN_VSP_COPY_INFINITY) + valueInt(FN_VSP_COPY_CUBE)
        + valueInt(FN_VSP_DRAW_CLOCK)
        + sumInt(values(strseq(FP_VSP_COUNT_DOTS, 1, N_VSP_COUNT_DOTS)))
        + sumInt(
               values(strseq(FP_VSP_IDENTIFY_LETTER, 1, N_VSP_IDENTIFY_LETTER))
        );
    /*
        Copy infinity = 1 point
        Copy cube = 2 points
        Draw clock = 5 points
    */
}

int Ace3::totalScore() const
{
    return getAttnScore() + getMemScore() + getFluencyScore() + getLangScore()
        + getVisuospatialScore();
}

int Ace3::miniAceScore() const
{
    return (
        sumInt(values(strseq(FP_ATTN_TIME, 1, N_ATTN_TIME_ACE - 1)))
        + valueInt(FN_FLUENCY_ANIMALS_SCORE)
        + sumInt(values(
            strseq(FP_MEM_REPEAT_ADDR_TRIAL3, 1, N_MEM_REPEAT_RECALL_ADDR)
        ))
        + valueInt(FN_VSP_DRAW_CLOCK)
        + sumInt(
            values(strseq(FP_MEM_RECALL_ADDRESS, 1, N_MEM_REPEAT_RECALL_ADDR))
        )
    );
    /*
        Attention/orientation = 4 points (season not used)
        Fluency, animals = 7 points
        Address registration/repetition = 7 points
        Draw clock = 5 points
        Adress recall = 7 points
    */
}

// ============================================================================
// Internal scoring/completeness tests
// ============================================================================

int Ace3::getFollowCommandScore() const
{
    if (!valueInt(FN_LANG_FOLLOW_CMD_PRACTICE)) {
        return 0;
    }
    return sumInt(values(strseq(FP_LANG_FOLLOW_CMD, 1, N_LANG_FOLLOW_CMD)));
}

int Ace3::getRepeatWordScore() const
{
    const int n = sumInt(values(strseq(FP_LANG_REPEAT_WORD, 1, 4)));
    return n >= 4 ? 2 : (n == 3 ? 1 : 0);
}

int Ace3::getMemRecognitionScore() const
{
    const int recall1 = valueInt(strnum(FP_MEM_RECALL_ADDRESS, 1));
    const int recall2 = valueInt(strnum(FP_MEM_RECALL_ADDRESS, 2));
    const int recall3 = valueInt(strnum(FP_MEM_RECALL_ADDRESS, 3));
    const int recall4 = valueInt(strnum(FP_MEM_RECALL_ADDRESS, 4));
    const int recall5 = valueInt(strnum(FP_MEM_RECALL_ADDRESS, 5));
    const int recall6 = valueInt(strnum(FP_MEM_RECALL_ADDRESS, 6));
    const int recall7 = valueInt(strnum(FP_MEM_RECALL_ADDRESS, 7));
    const int recog1 = valueInt(strnum(FP_MEM_RECOGNIZE_ADDRESS_SCORE, 1));
    const int recog2 = valueInt(strnum(FP_MEM_RECOGNIZE_ADDRESS_SCORE, 2));
    const int recog3 = valueInt(strnum(FP_MEM_RECOGNIZE_ADDRESS_SCORE, 3));
    const int recog4 = valueInt(strnum(FP_MEM_RECOGNIZE_ADDRESS_SCORE, 4));
    const int recog5 = valueInt(strnum(FP_MEM_RECOGNIZE_ADDRESS_SCORE, 5));
    int score = 0;
    score += (recall1 && recall2) ? 1 : recog1;  // forename, surname
    score += recall3 ? 1 : recog2;  // number
    score += (recall4 && recall5) ? 1 : recog3;  // streetname, streettype
    score += recall6 ? 1 : recog4;  // city
    score += recall7 ? 1 : recog5;  // county
    return score;
}

bool Ace3::isRecognitionComplete() const
{
    const int recall1 = valueInt(strnum(FP_MEM_RECALL_ADDRESS, 1));
    const int recall2 = valueInt(strnum(FP_MEM_RECALL_ADDRESS, 2));
    const int recall3 = valueInt(strnum(FP_MEM_RECALL_ADDRESS, 3));
    const int recall4 = valueInt(strnum(FP_MEM_RECALL_ADDRESS, 4));
    const int recall5 = valueInt(strnum(FP_MEM_RECALL_ADDRESS, 5));
    const int recall6 = valueInt(strnum(FP_MEM_RECALL_ADDRESS, 6));
    const int recall7 = valueInt(strnum(FP_MEM_RECALL_ADDRESS, 7));
    const bool recog1present
        = !valueIsNull(strnum(FP_MEM_RECOGNIZE_ADDRESS_CHOICE, 1));
    const bool recog2present
        = !valueIsNull(strnum(FP_MEM_RECOGNIZE_ADDRESS_CHOICE, 2));
    const bool recog3present
        = !valueIsNull(strnum(FP_MEM_RECOGNIZE_ADDRESS_CHOICE, 3));
    const bool recog4present
        = !valueIsNull(strnum(FP_MEM_RECOGNIZE_ADDRESS_CHOICE, 4));
    const bool recog5present
        = !valueIsNull(strnum(FP_MEM_RECOGNIZE_ADDRESS_CHOICE, 5));
    return (
        ((recall1 && recall2) || recog1present) &&  // forename, surname
        (recall3 || recog2present) &&  // number
        ((recall4 && recall5) || recog3present) &&  // streetname, streettype
        (recall6 || recog4present) &&  // city
        (recall7 || recog5present)  // county
    );
}

// ============================================================================
// Task address version support functions
// ============================================================================

QString Ace3::taskAddressVersion() const
{
    // Could be consolidated into AceFamily, but we follow the rule that access
    // to class-specific data is not put into the parent.
    const QString selected = valueString(FN_TASK_ADDRESS_VERSION);
    if (addressVersionsAvailable().contains(selected)) {
        return selected;
    }
    return TASK_DEFAULT_VERSION;
}

bool Ace3::isChangingAddressVersionOk() const
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
        ))
        && allNull(values(
            strseq(FP_MEM_RECOGNIZE_ADDRESS_CHOICE, 1, N_MEM_RECOGNIZE_ADDRESS)
        ));
}

bool Ace3::isAddressRecogAnswerCorrect(const int line) const
{
    Q_ASSERT(line >= 1 && line <= N_MEM_RECOGNIZE_ADDRESS);
    const QVector<int> correct_cols = correctColumnsAddressRecog();
    // correctColumnsAddressRecog() guarantees a vector of the correct size.
    const int line_idx = line - 1;
    const int correct_col_one_based = correct_cols[line_idx];
    const QChar answer
        = valueQChar(strnum(FP_MEM_RECOGNIZE_ADDRESS_CHOICE, line));
    switch (correct_col_one_based) {
        case 1:
            return answer == CHOICE_A;
        case 2:
            return answer == CHOICE_B;
        case 3:
            return answer == CHOICE_C;
    }
    // If we get here, something went wrong.
    return false;
}

QString Ace3::tagAddressRecog(int line) const
{
    return QString(QStringLiteral("addr_recog_%1")).arg(line);
}

QString Ace3::addressRecogElement(const int line, const int column) const
{
    // Five lines, three columns; we use one-based indexing here.
    Q_ASSERT(
        line >= 1 && line <= N_MEM_RECOGNIZE_ADDRESS && column >= 1
        && column <= N_ADDRESS_RECOG_OPTIONS
    );
    const QString task_address_version = taskAddressVersion();
    const QString x
        = QString(QStringLiteral("task_%1_address_recall_line_%2_option_%3"))
              .arg(task_address_version)
              .arg(line)
              .arg(column);
    return xstring(x);
}

QVector<int> Ace3::correctColumnsAddressRecog() const
{
    const QString v = taskAddressVersion();
    const QVector<int> correct_cols = correctColumnsAddressRecog(v);
    if (!isAddressRecogCorrectColumnInfoValid(correct_cols)) {
        // Duff information. Default to the values for English 'A'.
        return DEFAULT_ADDRESS_RECOG_CORRECT_COLS_ENGLISH_A;
    }
    return correct_cols;
}

QVector<int>
    Ace3::correctColumnsAddressRecog(const QString& task_address_version) const
{
    const QString x
        = QString(QStringLiteral("task_%1_address_recall_correct_options"))
              .arg(task_address_version);
    const QString csv_data = xstring(x);
    return convert::csvStringToIntVector(csv_data);
}

bool Ace3::isAddressRecogCorrectColumnInfoValid() const
{
    const QStringList versions = addressVersionsAvailable();
    for (const auto& v : versions) {
        const QVector<int> correct_cols = correctColumnsAddressRecog(v);
        if (!isAddressRecogCorrectColumnInfoValid(correct_cols)) {
            return false;
        }
    }
    return true;
}

bool Ace3::isAddressRecogCorrectColumnInfoValid(
    const QVector<int>& correct_cols
) const
{
    if (correct_cols.size() != N_MEM_RECOGNIZE_ADDRESS) {
        return false;
    }
    for (auto c : correct_cols) {
        if (c < 1 || c > N_ADDRESS_RECOG_OPTIONS) {
            return false;
        }
    }
    return true;
}

NameValueOptions Ace3::getAddressRecogOptions(int line) const
{
    return NameValueOptions{
        {addressRecogElement(line, 1), CHOICE_A},
        {addressRecogElement(line, 2), CHOICE_B},
        {addressRecogElement(line, 3), CHOICE_C},
    };
}

// ============================================================================
// Signal handlers
// ============================================================================

void Ace3::updateTaskVersionAddresses()
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

    // 3. Recognition.
    for (int line = 1; line <= N_MEM_RECOGNIZE_ADDRESS; ++line) {
        const NameValueOptions options_recog = getAddressRecogOptions(line);
        const QVector<QuElement*> candidate_elements
            = m_questionnaire->getElementsByTag(
                tagAddressRecog(line), false, TAG_PG_MEM_RECOGNITION
            );
        for (QuElement* e : candidate_elements) {
            auto recog = qobject_cast<QuMcq*>(e);
            if (!recog) {
                continue;
            }
            recog->setOptionNames(options_recog);
        }
    }
}

void Ace3::showStandardOrRemoteInstructions()
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

void Ace3::updateTaskVersionEditability()
{
    const bool editable = isChangingAddressVersionOk();
    m_questionnaire->setVisibleByTag(
        TAG_EL_CHOOSE_TASK_VERSION, editable, false, TAG_PG_PREAMBLE
    );
    m_questionnaire->setVisibleByTag(
        TAG_EL_SHOW_TASK_VERSION, !editable, false, TAG_PG_PREAMBLE
    );
}

void Ace3::updateAddressRecognition()
{
    // Parameter "const FieldRef* fieldref" not needed;
    // https://doc.qt.io/qt-6.5/signalsandslots.html
    // "... a slot may have a shorter signature than the signal it receives"

    if (!m_questionnaire) {
        return;
    }

    // Establish what's correct so far, from free recall.
    const QVector<bool> lines_correct{
        // Name:
        valueBool(strnum(FP_MEM_RECALL_ADDRESS, 1))
            && valueBool(strnum(FP_MEM_RECALL_ADDRESS, 2)),
        // Number:
        valueBool(strnum(FP_MEM_RECALL_ADDRESS, 3)),
        // Street:
        valueBool(strnum(FP_MEM_RECALL_ADDRESS, 4))
            && valueBool(strnum(FP_MEM_RECALL_ADDRESS, 5)),
        // Town:
        valueBool(strnum(FP_MEM_RECALL_ADDRESS, 6)),
        // County:
        valueBool(strnum(FP_MEM_RECALL_ADDRESS, 7)),
    };
    Q_ASSERT(lines_correct.size() == N_MEM_RECOGNIZE_ADDRESS);
    bool recog_required = false;
    for (const bool line_correct : lines_correct) {
        if (!line_correct) {
            recog_required = true;
            break;
        }
    }
    const bool recog_superfluous = !recog_required;

    // Set visibility and scores
    for (int line = 1; line <= N_MEM_RECOGNIZE_ADDRESS; ++line) {
        // Set visibility of all elements: text prompt and three options
        const int chunk_idx = line - 1;
        const bool line_correct = lines_correct[chunk_idx];
        const QString tag = tagAddressRecog(line);
        m_questionnaire->setVisibleByTag(
            tag, !line_correct, false, TAG_PG_MEM_RECOGNITION
        );
        // Update score
        // - bool to int 0/1 is guaranteed, so no need for " ? 1 : 0";
        //   http://stackoverflow.com/questions/5369770/bool-to-int-conversion
        const int recogscore
            = line_correct || isAddressRecogAnswerCorrect(line);
        setValue(strnum(FP_MEM_RECOGNIZE_ADDRESS_SCORE, line), recogscore);
    }
    // And two instructions:
    m_questionnaire->setVisibleByTag(
        TAG_RECOG_REQUIRED, recog_required, false, TAG_PG_MEM_RECOGNITION
    );
    m_questionnaire->setVisibleByTag(
        TAG_RECOG_SUPERFLUOUS, recog_superfluous, false, TAG_PG_MEM_RECOGNITION
    );
}

void Ace3::langPracticeChanged(const FieldRef* fieldref)
{
    // qDebug() << Q_FUNC_INFO;
    if (!m_questionnaire) {
        return;
    }
    const QVariant value = fieldref->value();
    const bool visible = !eq(value, false);
    const bool mandatory = value.toBool();
    for (int i = 1; i <= N_LANG_FOLLOW_CMD; ++i) {
        fieldRef(strnum(FP_LANG_FOLLOW_CMD, i))->setMandatory(mandatory);
    }
    m_questionnaire->setVisibleByTag(
        TAG_EL_LANG_OPTIONAL_COMMAND,
        visible,
        false,
        TAG_PG_LANG_COMMANDS_SENTENCES
    );
    m_questionnaire->setVisibleByTag(
        TAG_EL_LANG_NOT_SHOWN, !visible, false, TAG_PG_LANG_COMMANDS_SENTENCES
    );
}
