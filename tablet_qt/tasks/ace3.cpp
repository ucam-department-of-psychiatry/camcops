/*
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

#include "ace3.h"
#include "common/uiconstants.h"
#include "lib/datetimefunc.h"
#include "lib/mathfunc.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/qucontainerhorizontal.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qulineedit.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
using MathFunc::eq;
using MathFunc::noneNull;
using MathFunc::percent;
using MathFunc::sumInt;
using StringFunc::bold;
using StringFunc::strnum;
using StringFunc::strseq;

const QString IMAGE_SPOON("ace3/spoon.png");
const QString IMAGE_BOOK("ace3/book.png");
const QString IMAGE_KANGAROO("ace3/kangaroo.png");
const QString IMAGE_PENGUIN("ace3/penguin.png");
const QString IMAGE_ANCHOR("ace3/anchor.png");
const QString IMAGE_CAMEL("ace3/camel.png");
const QString IMAGE_HARP("ace3/harp.png");
const QString IMAGE_RHINOCEROS("ace3/rhinoceros.png");
const QString IMAGE_BARREL("ace3/barrel.png");
const QString IMAGE_CROWN("ace3/crown.png");
const QString IMAGE_CROCODILE("ace3/crocodile.png");
const QString IMAGE_ACCORDION("ace3/accordion.png");
const QString IMAGE_INFINITY("ace3/infinity.png");
const QString IMAGE_CUBE("ace3/cube.png");
const QString IMAGE_DOTS8("ace3/dots8.png");
const QString IMAGE_DOTS10("ace3/dots10.png");
const QString IMAGE_DOTS7("ace3/dots7.png");
const QString IMAGE_DOTS9("ace3/dots9.png");
const QString IMAGE_K("ace3/k.png");
const QString IMAGE_M("ace3/m.png");
const QString IMAGE_A("ace3/a.png");
const QString IMAGE_T("ace3/t.png");

const QString TAG_MEM_RECOGNIZE( "mem_recognize");
const QString TAG_LANG_COMMANDS_SENTENCES("lang_commands_sentences");
const QString TAG_LANG_OPTIONAL_COMMAND("lang_optional_command");

// Field names, field prefixes, and field counts
const QString FN_AGE_FT_EDUCATION("age_at_leaving_full_time_education");
const QString FN_OCCUPATION("occupation");
const QString FN_HANDEDNESS("handedness");
const QString FP_ATTN_TIME("attn_time");
const int N_ATTN_TIME = 5;
const QString FP_ATTN_PLACE("attn_place");
const int N_ATTN_PLACE = 5;
const QString FP_ATTN_REPEAT_WORD("attn_repeat_word");
const int N_ATTN_REPEAT_WORD = 3;
const QString FN_ATTN_NUM_REGISTRATION_TRIALS("attn_num_registration_trials");
const QString FP_ATTN_SERIAL7("attn_serial7_subtraction");
const int N_ATTN_SERIAL7 = 5;
const QString FP_MEM_RECALL_WORD("mem_recall_word");
const int N_MEM_RECALL_WORD = 3;
const QString FN_FLUENCY_LETTERS_SCORE("fluency_letters_score");
const QString FN_FLUENCY_ANIMALS_SCORE("fluency_animals_score");
const QString FP_MEM_REPEAT_ADDR_TRIAL1("mem_repeat_address_trial1_");
const QString FP_MEM_REPEAT_ADDR_TRIAL2("mem_repeat_address_trial2_");
const QString FP_MEM_REPEAT_ADDR_TRIAL3("mem_repeat_address_trial3_");
const int N_MEM_REPEAT_ADDR = 7;
const QString FP_MEM_FAMOUS("mem_famous");
const int N_MEM_FAMOUS = 4;
const QString FN_LANG_FOLLOW_CMD_PRACTICE("lang_follow_command_practice");
const QString FP_LANG_FOLLOW_CMD("lang_follow_command");
const int N_LANG_FOLLOW_CMD = 3;
const QString FP_LANG_WRITE_SENTENCES_POINT("lang_write_sentences_point");
const int N_LANG_WRITE_SENTENCES_POINT = 2;
const QString FP_LANG_REPEAT_WORD("lang_repeat_word");
const int N_LANG_REPEAT_WORD = 4;
const QString FP_LANG_REPEAT_SENTENCE("lang_repeat_sentence");
const int N_LANG_REPEAT_SENTENCE = 2;
const QString FP_LANG_NAME_PICTURE("lang_name_picture");
const int N_LANG_NAME_PICTURE = 12;
const QString FP_LANG_IDENTIFY_CONCEPT("lang_identify_concept");
const int N_LANG_IDENTIFY_CONCEPT = 4;
const QString FN_LANG_READ_WORDS_ALOUD("lang_read_words_aloud");
const QString FN_VSP_COPY_INFINITY("vsp_copy_infinity");
const QString FN_VSP_COPY_CUBE("vsp_copy_cube");
const QString FN_VSP_DRAW_CLOCK("vsp_draw_clock");
const QString FP_VSP_COUNT_DOTS("vsp_count_dots");
const int N_VSP_COUNT_DOTS = 4;
const QString FP_VSP_IDENTIFY_LETTER("vsp_identify_letter");
const int N_VSP_IDENTIFY_LETTER = 4;
const QString FP_MEM_RECALL_ADDRESS("mem_recall_address");
const int N_MEM_RECALL_ADDRESS = 7;
const QString FP_MEM_RECOGNIZE_ADDRESS("mem_recognize_address");
const int N_MEM_RECOGNIZE_ADDRESS = 5;
const QString FN_PICTURE1_BLOBID("picture1_blobid");
// defunct: picture1_rotation
const QString FN_PICTURE2_BLOBID("picture2_blobid");
// defunct: picture2_rotation
const QString FN_COMMENTS("comments");

// Subtotals. No magic numbers...
const int TOTAL_OVERALL = 100;
const int TOTAL_ATTN = 18;
const int TOTAL_MEM = 26;
const int TOTAL_FLUENCY = 14;
const int TOTAL_LANG = 26;
const int TOTAL_VSP = 16;

const int MIN_AGE = 0;
const int MAX_AGE = 120;


void initializeAce3(TaskFactory& factory)
{
    static TaskRegistrar<Ace3> registered(factory);
}


Ace3::Ace3(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, "ace3", false, true, false)
{
    addField(FN_AGE_FT_EDUCATION, QVariant::Int);
    addField(FN_OCCUPATION, QVariant::String);
    addField(FN_HANDEDNESS, QVariant::String);
    addFields(strseq(FP_ATTN_TIME, 1, N_ATTN_TIME), QVariant::Int);
    addFields(strseq(FP_ATTN_PLACE, 1, N_ATTN_PLACE), QVariant::Int);
    addFields(strseq(FP_ATTN_REPEAT_WORD, 1, N_ATTN_REPEAT_WORD), QVariant::Int);
    addField(FN_ATTN_NUM_REGISTRATION_TRIALS, QVariant::Int);
    addFields(strseq(FP_ATTN_SERIAL7, 1, N_ATTN_SERIAL7), QVariant::Int);
    addFields(strseq(FP_MEM_RECALL_WORD, 1, N_MEM_RECALL_WORD), QVariant::Int);
    addField(FN_FLUENCY_LETTERS_SCORE, QVariant::Int);
    addField(FN_FLUENCY_ANIMALS_SCORE, QVariant::Int);
    addFields(strseq(FP_MEM_REPEAT_ADDR_TRIAL1, 1, N_MEM_REPEAT_ADDR), QVariant::Int);
    addFields(strseq(FP_MEM_REPEAT_ADDR_TRIAL2, 1, N_MEM_REPEAT_ADDR), QVariant::Int);
    addFields(strseq(FP_MEM_REPEAT_ADDR_TRIAL3, 1, N_MEM_REPEAT_ADDR), QVariant::Int);
    addFields(strseq(FP_MEM_FAMOUS, 1, N_MEM_FAMOUS), QVariant::Int);
    addField(FN_LANG_FOLLOW_CMD_PRACTICE, QVariant::Int);
    addFields(strseq(FP_LANG_FOLLOW_CMD, 1, N_LANG_FOLLOW_CMD), QVariant::Int);
    addFields(strseq(FP_LANG_WRITE_SENTENCES_POINT, 1, N_LANG_WRITE_SENTENCES_POINT), QVariant::Int);
    addFields(strseq(FP_LANG_REPEAT_WORD, 1, N_LANG_REPEAT_WORD), QVariant::Int);
    addFields(strseq(FP_LANG_REPEAT_SENTENCE, 1, N_LANG_REPEAT_SENTENCE), QVariant::Int);
    addFields(strseq(FP_LANG_NAME_PICTURE, 1, N_LANG_NAME_PICTURE), QVariant::Int);
    addFields(strseq(FP_LANG_IDENTIFY_CONCEPT, 1, N_LANG_IDENTIFY_CONCEPT), QVariant::Int);
    addField(FN_LANG_READ_WORDS_ALOUD, QVariant::Int);
    addField(FN_VSP_COPY_INFINITY, QVariant::Int);
    addField(FN_VSP_COPY_CUBE, QVariant::Int);
    addField(FN_VSP_DRAW_CLOCK, QVariant::Int);
    addFields(strseq(FP_VSP_COUNT_DOTS, 1, N_VSP_COUNT_DOTS), QVariant::Int);
    addFields(strseq(FP_VSP_IDENTIFY_LETTER, 1, N_VSP_IDENTIFY_LETTER), QVariant::Int);
    addFields(strseq(FP_MEM_RECALL_ADDRESS, 1, N_MEM_RECALL_ADDRESS), QVariant::Int);
    addFields(strseq(FP_MEM_RECOGNIZE_ADDRESS, 1, N_MEM_RECOGNIZE_ADDRESS), QVariant::Int);
    addField(FN_PICTURE1_BLOBID, QVariant::Int);
    addField(FN_PICTURE2_BLOBID, QVariant::Int);
    addField(FN_COMMENTS, QVariant::String);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Ace3::shortname() const
{
    return "ACE-III";
}


QString Ace3::longname() const
{
    return tr("Addenbrooke’s Cognitive Examination, revision 3");
}


QString Ace3::menusubtitle() const
{
    return tr("100-point clinician-administered assessment of attention/"
              "orientation, memory, fluency, language, and visuospatial "
              "domains.");
}


// ============================================================================
// Instance info
// ============================================================================

bool Ace3::isComplete() const
{
    return noneNull(values(strseq(FP_ATTN_TIME, 1, N_ATTN_TIME))) &&
            noneNull(values(strseq(FP_ATTN_PLACE, 1, N_ATTN_PLACE))) &&
            noneNull(values(strseq(FP_ATTN_REPEAT_WORD, 1, N_ATTN_REPEAT_WORD))) &&
            noneNull(values(strseq(FP_ATTN_SERIAL7, 1, N_ATTN_SERIAL7))) &&
            noneNull(values(strseq(FP_MEM_RECALL_WORD, 1, N_MEM_RECALL_WORD))) &&
            !value(FN_FLUENCY_LETTERS_SCORE).isNull() &&
            !value(FN_FLUENCY_ANIMALS_SCORE).isNull() &&
            noneNull(values(strseq(FP_MEM_REPEAT_ADDR_TRIAL3, 1, N_MEM_REPEAT_ADDR))) &&
            noneNull(values(strseq(FP_MEM_FAMOUS, 1, N_MEM_FAMOUS))) &&
            !value(FN_LANG_FOLLOW_CMD_PRACTICE).isNull() &&
            (eq(value(FN_LANG_FOLLOW_CMD_PRACTICE), 0) ||
                noneNull(values(strseq(FP_LANG_FOLLOW_CMD, 1, N_LANG_FOLLOW_CMD)))) &&
            // ... failed practice, or completed all three actual tests
            noneNull(values(strseq(FP_LANG_WRITE_SENTENCES_POINT, 1, N_LANG_WRITE_SENTENCES_POINT))) &&
            noneNull(values(strseq(FP_LANG_REPEAT_WORD, 1, N_LANG_REPEAT_WORD))) &&
            noneNull(values(strseq(FP_LANG_REPEAT_SENTENCE, 1, N_LANG_REPEAT_SENTENCE))) &&
            noneNull(values(strseq(FP_LANG_NAME_PICTURE, 1, N_LANG_NAME_PICTURE))) &&
            noneNull(values(strseq(FP_LANG_IDENTIFY_CONCEPT, 1, N_LANG_IDENTIFY_CONCEPT))) &&
            !value(FN_LANG_READ_WORDS_ALOUD).isNull() &&
            !value(FN_VSP_COPY_INFINITY).isNull() &&
            !value(FN_VSP_COPY_CUBE).isNull() &&
            !value(FN_VSP_DRAW_CLOCK).isNull() &&
            noneNull(values(strseq(FP_VSP_COUNT_DOTS, 1, N_VSP_COUNT_DOTS))) &&
            noneNull(values(strseq(FP_VSP_IDENTIFY_LETTER, 1, N_VSP_IDENTIFY_LETTER))) &&
            noneNull(values(strseq(FP_MEM_RECALL_ADDRESS, 1, N_MEM_RECALL_ADDRESS))) &&
            isRecognitionComplete();
}


QString Ace3::summary() const
{
    int a = getAttnScore();
    int m = getMemScore();
    int f = getFluencyScore();
    int l = getLangScore();
    int v = getVisuospatialScore();
    int t = a + m + f + l + v;
    auto scorelambda = [](int score, int out_of, bool space = true) -> QString {
        QString result = QString(" %1/%2 (%3).")
                .arg(score)
                .arg(out_of)
                .arg(percent(score, out_of));
        if (space) {
            result += " ";
        }
        return result;
    };
    return tr("Total score") + QString(" %1/%2. ").arg(t).arg(TOTAL_OVERALL) +
            xstring("cat_attn") + scorelambda(a, TOTAL_ATTN) +
            xstring("cat_mem") + scorelambda(m, TOTAL_MEM) +
            xstring("cat_fluency") + scorelambda(f, TOTAL_FLUENCY) +
            xstring("cat_lang") + scorelambda(l, TOTAL_LANG) +
            xstring("cat_vsp") + scorelambda(v, TOTAL_VSP, false);
}


QString Ace3::detail() const
{
    return summary() + "<br><br>" + recordSummary();
}


OpenableWidget* Ace3::editor(bool read_only)
{
    int pagenum = 1;
    auto makeTitle = [this, &pagenum]() -> QString {
        return xstring("title_prefix") + QString(" %1").arg(pagenum++);
    };

    // ------------------------------------------------------------------------
    // Preamble; age-leaving-full-time-education; handedness
    // ------------------------------------------------------------------------

    NameValueOptions options_handedness{
        {xstring("left_handed"), "L"},
        {xstring("right_handed"), "R"},
    };

    QuPagePtr page_preamble((new QuPage{
        (new QuText(xstring("instruction_need_paper")))->bold(),
        getClinicianQuestionnaireBlockRawPointer(),
        new QuText(xstring("preamble_instruction")),
        QuestionnaireFunc::defaultGridRawPointer({
            {xstring("q_age_leaving_fte"),
             new QuLineEditInteger(fieldRef(FN_AGE_FT_EDUCATION), MIN_AGE, MAX_AGE)},
            {xstring("q_occupation"), new QuLineEdit(fieldRef(FN_OCCUPATION))},
        }, UiConst::DEFAULT_COLSPAN_Q, UiConst::DEFAULT_COLSPAN_A),
        (new QuMCQ(fieldRef(FN_HANDEDNESS), options_handedness))->setHorizontal(true),
    })->setTitle(makeTitle())->setType(QuPage::PageType::Clinician));

    // ------------------------------------------------------------------------
    // Attention/orientation
    // ------------------------------------------------------------------------

    QDateTime now = DateTime::now();
    QString season;
    switch (DateTime::now().date().month()) {
        // 1 = Jan, 12 = Dec
    case 12:
    case 1:
    case 2:
        season = xstring("season_winter");
        break;
    case 3:
    case 4:
    case 5:
        season = xstring("season_spring");
        break;
    case 6:
    case 7:
    case 8:
        season = xstring("season_summer");
        break;
    case 9:
    case 10:
    case 11:
        season = xstring("season_autumn");
        break;
    default:
        season = "?(season_bug)";
        break;
    }
    QString correct_date = "     " + now.toString("dddd d MMMM yyyy") + "; " +
            season;
    // ... e.g. "Monday 2 January 2016; winter"
    // http://doc.qt.io/qt-5/qdate.html#toString

    NameValueOptions options_registration{
        {"1", 1},
        {"2", 2},
        {"3", 3},
        {"4", 4},
        {">4", 0},
    };

    QuPagePtr page_attn((new QuPage{
        new QuHeading(xstring("cat_attn")),
        // Orientation
        new QuText(xstring("attn_q_time")),
        new QuContainerHorizontal{
            new QuBoolean(xstring("attn_time1"), fieldRef(strnum(FP_ATTN_TIME, 1))),
            new QuBoolean(xstring("attn_time2"), fieldRef(strnum(FP_ATTN_TIME, 2))),
            new QuBoolean(xstring("attn_time3"), fieldRef(strnum(FP_ATTN_TIME, 3))),
            new QuBoolean(xstring("attn_time4"), fieldRef(strnum(FP_ATTN_TIME, 4))),
            new QuBoolean(xstring("attn_time5"), fieldRef(strnum(FP_ATTN_TIME, 5))),
        },
        (new QuText(xstring("instruction_time")))->italic(),
        (new QuText(correct_date))->italic(),
        new QuText(xstring("attn_q_place")),
        new QuContainerHorizontal{
            new QuBoolean(xstring("attn_place1"), fieldRef(strnum(FP_ATTN_PLACE, 1))),
            new QuBoolean(xstring("attn_place2"), fieldRef(strnum(FP_ATTN_PLACE, 2))),
            new QuBoolean(xstring("attn_place3"), fieldRef(strnum(FP_ATTN_PLACE, 3))),
            new QuBoolean(xstring("attn_place4"), fieldRef(strnum(FP_ATTN_PLACE, 4))),
            new QuBoolean(xstring("attn_place5"), fieldRef(strnum(FP_ATTN_PLACE, 5))),
        },
        (new QuText(xstring("instruction_place")))->italic(),
        // Lemon, key, ball (registration)
        new QuHeading(xstring("cat_attn")),
        new QuText(xstring("attn_q_words")),
        (new QuText(xstring("attn_instruction_words")))->italic(),
        new QuContainerHorizontal{
            new QuBoolean(xstring("mem_word1"), fieldRef(strnum(FP_ATTN_REPEAT_WORD, 1))),
            new QuBoolean(xstring("mem_word2"), fieldRef(strnum(FP_ATTN_REPEAT_WORD, 2))),
            new QuBoolean(xstring("mem_word3"), fieldRef(strnum(FP_ATTN_REPEAT_WORD, 3))),
        },
        new QuContainerHorizontal{
            new QuText(xstring("attn_q_register_n_trials")),
            (new QuMCQ(fieldRef(FN_ATTN_NUM_REGISTRATION_TRIALS),
                                 options_registration))->setHorizontal(true),
        },
        // Serial 7s
        new QuHeading(xstring("cat_attn")),
        new QuText(xstring("attn_q_serial_sevens")),
        (new QuText(xstring("attn_instruction_sevens")))->italic(),
        new QuContainerHorizontal{
            new QuBoolean(xstring("attn_subtraction1"), fieldRef(strnum(FP_ATTN_SERIAL7, 1))),
            new QuBoolean(xstring("attn_subtraction2"), fieldRef(strnum(FP_ATTN_SERIAL7, 2))),
            new QuBoolean(xstring("attn_subtraction3"), fieldRef(strnum(FP_ATTN_SERIAL7, 3))),
            new QuBoolean(xstring("attn_subtraction4"), fieldRef(strnum(FP_ATTN_SERIAL7, 4))),
            new QuBoolean(xstring("attn_subtraction5"), fieldRef(strnum(FP_ATTN_SERIAL7, 5))),
        },
        // Lemon, key, ball (recall)
        new QuHeading(xstring("cat_mem")),
        new QuText(xstring("mem_q_recall_words")),
        (new QuText(xstring("mem_instruction_recall")))->italic(),
        new QuContainerHorizontal{
            new QuBoolean(xstring("mem_word1"), fieldRef(strnum(FP_MEM_RECALL_WORD, 1))),
            new QuBoolean(xstring("mem_word2"), fieldRef(strnum(FP_MEM_RECALL_WORD, 2))),
            new QuBoolean(xstring("mem_word3"), fieldRef(strnum(FP_MEM_RECALL_WORD, 3))),
        },
    })->setTitle(makeTitle())->setType(QuPage::PageType::Clinician));

    // ------------------------------------------------------------------------
    // Questionnaire
    // ------------------------------------------------------------------------

    Questionnaire* questionnaire = new Questionnaire(m_app, {
        page_preamble, page_attn, /* page_fluency, page_repeat_addr_famous,
        page_commands_sentences, page_repetition,
        page_name_pictures, page_read_words_aloud,
        page_infinity, page_cube, page_clock,
        page_dots, page_letters,
        page_recall_address_free, page_recall_address_prompted,
        page_comments, page_photo_1, page_photo_2, */
    });
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Ace3::getAttnScore() const
{
    return sumInt(values(strseq(FP_ATTN_TIME, 1, N_ATTN_TIME) +
                         strseq(FP_ATTN_PLACE, 1, N_ATTN_PLACE) +
                         strseq(FP_ATTN_REPEAT_WORD, 1, N_ATTN_REPEAT_WORD) +
                         strseq(FP_ATTN_SERIAL7, 1, N_ATTN_SERIAL7)));
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
    const int recog1 = valueInt(strnum(FP_MEM_RECOGNIZE_ADDRESS, 1));
    const int recog2 = valueInt(strnum(FP_MEM_RECOGNIZE_ADDRESS, 2));
    const int recog3 = valueInt(strnum(FP_MEM_RECOGNIZE_ADDRESS, 3));
    const int recog4 = valueInt(strnum(FP_MEM_RECOGNIZE_ADDRESS, 4));
    const int recog5 = valueInt(strnum(FP_MEM_RECOGNIZE_ADDRESS, 5));
    int score = 0;
    score += (recall1 && recall2) ? 1 : recog1;  // forename, surname
    score += recall3 ? 1 : recog2;  // number
    score += (recall4 && recall5) ? 1 : recog3;  // streetname, streettype
    score += recall6 ? 1 : recog4;  // city
    score += recall7 ? 1 : recog5; // county
    return score;
}


int Ace3::getMemScore() const
{
    return sumInt(values(strseq(FP_MEM_RECALL_WORD, 1, N_MEM_RECALL_WORD) +
                         strseq(FP_MEM_REPEAT_ADDR_TRIAL3, 1, N_MEM_REPEAT_ADDR) +
                         strseq(FP_MEM_FAMOUS, 1, N_MEM_FAMOUS) +
                         strseq(FP_MEM_RECALL_ADDRESS, 1, N_MEM_RECALL_ADDRESS))) +
            getMemRecognitionScore();
}


int Ace3::getFluencyScore() const
{
    return valueInt(FN_FLUENCY_LETTERS_SCORE) +
            valueInt(FN_FLUENCY_ANIMALS_SCORE);
}


int Ace3::getFollowCommandScore() const
{
    if (!valueInt(FN_LANG_FOLLOW_CMD_PRACTICE)) {
        return 0;
    }
    return sumInt(values(strseq(FP_LANG_FOLLOW_CMD, 1, N_LANG_FOLLOW_CMD)));
}


int Ace3::getRepeatWordScore() const
{
    int n = sumInt(values(strseq(FP_LANG_REPEAT_WORD, 1, 4)));
    return n >= 4 ? 2 : (n == 3 ? 1 : 0);
}


int Ace3::getLangScore() const
{
    return getFollowCommandScore() +  // 3 points
            sumInt(values(strseq(FP_LANG_WRITE_SENTENCES_POINT, 1, N_LANG_WRITE_SENTENCES_POINT))) +
            getRepeatWordScore() +  // 2 points
            sumInt(values(strseq(FP_LANG_REPEAT_SENTENCE, 1, N_LANG_REPEAT_SENTENCE))) +
            sumInt(values(strseq(FP_LANG_NAME_PICTURE, 1, N_LANG_NAME_PICTURE))) +
            sumInt(values(strseq(FP_LANG_IDENTIFY_CONCEPT, 1, N_LANG_IDENTIFY_CONCEPT))) +
            valueInt(FN_LANG_READ_WORDS_ALOUD);  // 1 point
}


int Ace3::getVisuospatialScore() const
{
    return valueInt(FN_VSP_COPY_INFINITY) +  // 1 point
            valueInt(FN_VSP_COPY_CUBE) +  // 2 points
            valueInt(FN_VSP_DRAW_CLOCK) +  // 5 points
            sumInt(values(strseq(FP_VSP_COUNT_DOTS, 1, N_VSP_COUNT_DOTS))) +
            sumInt(values(strseq(FP_VSP_IDENTIFY_LETTER, 1, N_VSP_IDENTIFY_LETTER)));
}


int Ace3::totalScore() const
{
    return getAttnScore() +
            getMemScore() +
            getFluencyScore() +
            getLangScore() +
            getVisuospatialScore();
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
    const bool recog1present = !value(strnum(FP_MEM_RECOGNIZE_ADDRESS, 1)).isNull();
    const bool recog2present = !value(strnum(FP_MEM_RECOGNIZE_ADDRESS, 2)).isNull();
    const bool recog3present = !value(strnum(FP_MEM_RECOGNIZE_ADDRESS, 3)).isNull();
    const bool recog4present = !value(strnum(FP_MEM_RECOGNIZE_ADDRESS, 4)).isNull();
    const bool recog5present = !value(strnum(FP_MEM_RECOGNIZE_ADDRESS, 5)).isNull();
    return (
        ((recall1 && recall2) || recog1present) &&  // forename, surname
        (recall3 || recog2present) &&  // number
        ((recall4 && recall5) || recog3present) &&  // streetname, streettype
        (recall6 || recog4present) &&  // city
        (recall7 || recog5present)  // county
    );
}
