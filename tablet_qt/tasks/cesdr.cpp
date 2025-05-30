#include "cesdr.h"

#include "core/camcopsapp.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "lib/version.h"
#include "maths/mathfunc.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
using mathfunc::countNull;
using mathfunc::countWhere;
using mathfunc::noneNull;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;
using stringfunc::standardResult;
using stringfunc::strnum;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_QUESTIONS = 20;
const int MAX_QUESTION_SCORE = 60;

const int CAT_NONCLINICAL = 0;
const int CAT_SUB = 1;
const int CAT_POSS_MAJOR = 2;
const int CAT_PROB_MAJOR = 3;
const int CAT_MAJOR = 4;

const int DEPRESSION_RISK_THRESHOLD = 16;

const int FREQ_NOT_AT_ALL = 0;
const int FREQ_1_2_DAYS_LAST_WEEK = 1;
const int FREQ_3_4_DAYS_LAST_WEEK = 2;
const int FREQ_5_7_DAYS_LAST_WEEK = 3;
const int FREQ_DAILY_2_WEEKS = 4;

const int POSS_MAJOR_THRESH = 2;
const int PROB_MAJOR_THRESH = 3;
const int MAJOR_THRESH = 4;

const QString QPREFIX("q");
const QString Cesdr::CESDR_TABLENAME("cesdr");

void initializeCesdr(TaskFactory& factory)
{
    static TaskRegistrar<Cesdr> registered(factory);
}

Cesdr::Cesdr(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, CESDR_TABLENAME, false, false, false),
    m_questionnaire(nullptr)
{
    addFields(
        strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QMetaType::fromType<int>()
    );

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString Cesdr::shortname() const
{
    return "CESD-R";
}

QString Cesdr::longname() const
{
    return tr("Center for Epidemiologic Studies Depression Scale (Revised)");
}

QString Cesdr::description() const
{
    return tr("20-item self-report depression scale.");
}

Version Cesdr::minimumServerVersion() const
{
    return Version(2, 2, 8);
}

QString Cesdr::infoFilenameStem() const
{
    return "cesd";
}

// ============================================================================
// Instance info
// ============================================================================

bool Cesdr::isComplete() const
{
    return noneNull(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}

QStringList Cesdr::summary() const
{
    return QStringList{
        totalScorePhrase(totalScore(), MAX_QUESTION_SCORE),
        standardResult(
            xstring("depression_or_risk_of"),
            uifunc::yesNoUnknown(totalScore() >= DEPRESSION_RISK_THRESHOLD)
        ),
    };
}

QStringList Cesdr::detail() const
{
    QStringList lines = completenessInfo();
    lines += summary();

    const int cat = depressionCategory();
    lines.append("");
    lines.append(xstring("category_" + QString::number(cat)));

    return lines;
}

int Cesdr::depressionCategory() const
{
    /*
     * Determining CESD-R categories
     * See: https://cesd-r.com/cesdr/
     */

    if (totalScore() < DEPRESSION_RISK_THRESHOLD) {
        return CAT_SUB;
    }

    // DSM Categories
    const QVector<int> qs_dysphoria = {2, 4, 6};
    const QVector<int> qs_anhedonia = {8, 10};
    const QVector<int> qs_appetite = {1, 18};
    const QVector<int> qs_sleep = {5, 11, 19};
    const QVector<int> qs_thinking = {3, 20};
    const QVector<int> qs_guilt = {9, 17};
    const QVector<int> qs_tired = {7, 16};
    const QVector<int> qs_movement = {12, 13};
    const QVector<int> qs_suicidal = {14, 15};
    const QVector<QVector<int>> non_anhedonia_groups{
        qs_appetite,
        qs_sleep,
        qs_movement,
        qs_tired,
        qs_guilt,
        qs_thinking,
        qs_suicidal};

    // Dysphoria or anhedonia must be present at frequency FREQ_DAILY_2_WEEKS
    const bool anhedonia_criterion = fulfilsGroupCriteria(qs_dysphoria, true)
        || fulfilsGroupCriteria(qs_anhedonia, true);
    if (anhedonia_criterion) {
        int categoryCountHighFrequency = 0;
        int categoryCountLowerFrequency = 0;
        for (auto qgroup : non_anhedonia_groups) {
            if (fulfilsGroupCriteria(qgroup, true)) {
                // Category contains an answer == FREQ_DAILY_2_WEEKS
                categoryCountHighFrequency += 1;
            }
            if (fulfilsGroupCriteria(qgroup, false)) {
                // Category contains an answer == FREQ_DAILY_2_WEEKS or
                // FREQ_5_7_DAYS_LAST_WEEK
                categoryCountLowerFrequency += 1;
            }
        }

        if (categoryCountHighFrequency >= MAJOR_THRESH) {
            // Anhedonia or dysphoria (at FREQ_DAILY_2_WEEKS)
            // plus 4 other symptom groups at FREQ_DAILY_2_WEEKS
            return CAT_MAJOR;
        } else if (categoryCountLowerFrequency >= PROB_MAJOR_THRESH) {
            // Anhedonia or dysphoria (at FREQ_DAILY_2_WEEKS)
            // plus 3 other symptom groups at FREQ_DAILY_2_WEEKS or
            // FREQ_5_7_DAYS_LAST_WEEK
            return CAT_PROB_MAJOR;
        } else if (categoryCountLowerFrequency >= POSS_MAJOR_THRESH) {
            // Anhedonia or dysphoria (at FREQ_DAILY_2_WEEKS)
            // plus 2 other symptom groups at FREQ_DAILY_2_WEEKS or
            // FREQ_5_7_DAYS_LAST_WEEK
            return CAT_POSS_MAJOR;
        }
    }

    const int cesd_score = totalScore();
    if (cesd_score >= DEPRESSION_RISK_THRESHOLD) {
        // Total CESD-style score >= 16 but doesn't meet other criteria.
        return CAT_SUB;
    }
    return CAT_NONCLINICAL;
}

OpenableWidget* Cesdr::editor(const bool read_only)
{
    const NameValueOptions options{
        {xstring("a0"), FREQ_NOT_AT_ALL},
        {xstring("a1"), FREQ_1_2_DAYS_LAST_WEEK},
        {xstring("a2"), FREQ_3_4_DAYS_LAST_WEEK},
        {xstring("a3"), FREQ_5_7_DAYS_LAST_WEEK},
        {xstring("a4"), FREQ_DAILY_2_WEEKS},
    };

    const int question_width = 50;
    const QVector<int> option_widths{10, 10, 10, 10, 10};

    QuPagePtr page(
        (new QuPage{
             new QuText(xstring("instructions")),
             (new QuMcqGrid(
                  {QuestionWithOneField(xstring("q1"), fieldRef("q1")),
                   QuestionWithOneField(xstring("q2"), fieldRef("q2")),
                   QuestionWithOneField(xstring("q3"), fieldRef("q3")),
                   QuestionWithOneField(xstring("q4"), fieldRef("q4")),
                   QuestionWithOneField(xstring("q5"), fieldRef("q5")),
                   QuestionWithOneField(xstring("q6"), fieldRef("q6")),
                   QuestionWithOneField(xstring("q7"), fieldRef("q7")),
                   QuestionWithOneField(xstring("q8"), fieldRef("q8")),
                   QuestionWithOneField(xstring("q9"), fieldRef("q9")),
                   QuestionWithOneField(xstring("q10"), fieldRef("q10")),
                   QuestionWithOneField(xstring("q11"), fieldRef("q11")),
                   QuestionWithOneField(xstring("q12"), fieldRef("q12")),
                   QuestionWithOneField(xstring("q13"), fieldRef("q13")),
                   QuestionWithOneField(xstring("q14"), fieldRef("q14")),
                   QuestionWithOneField(xstring("q15"), fieldRef("q15")),
                   QuestionWithOneField(xstring("q16"), fieldRef("q16")),
                   QuestionWithOneField(xstring("q17"), fieldRef("q17")),
                   QuestionWithOneField(xstring("q18"), fieldRef("q18")),
                   QuestionWithOneField(xstring("q19"), fieldRef("q19")),
                   QuestionWithOneField(xstring("q20"), fieldRef("q20"))},
                  options
              ))
                 ->setTitle(xstring("stem"))
                 ->setWidth(question_width, option_widths)
                 ->setExpand(true)
                 ->setQuestionsBold(false)})
            ->setTitle(xstring("title"))
    );

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}

// ============================================================================
// Task-specific calculations
// ============================================================================

bool Cesdr::fulfilsGroupCriteria(
    const QVector<int>& qnums, bool nearly_every_day_2w
) const
{
    for (const int qnum : qnums) {
        const int v = valueInt(stringfunc::strnum("q", qnum));
        if (v == FREQ_DAILY_2_WEEKS) {
            return true;
        }
        if (v == FREQ_5_7_DAYS_LAST_WEEK && !nearly_every_day_2w) {
            // A lower threshold for some symptoms, when nearly_every_day_2w
            // is false.
            return true;
        }
    }
    return false;
}

int Cesdr::totalScore() const
{
    // So that the CESD-R has the same range as the CESD (the "CESD-style
    // score"), the values for the top two responses are given the same value.
    // See: https://cesd-r.com/cesdr/

    QVector<QVariant> responses
        = values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS));

    // Sum the response values, and subtract the count of answers marked as
    // occurring daily. Makes the 5-7 and daily responses value-quivalent, so
    // scoring is out of 60 and comparable to CESD.
    return sumInt(responses)
        - countWhere(responses, QVector<QVariant>{FREQ_DAILY_2_WEEKS});
}

int Cesdr::numNull(const int first, const int last) const
{
    return countNull(values(strseq(QPREFIX, first, last)));
}
