#include "cesdr.h"
#include "core/camcopsapp.h"
#include "lib/version.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "tasklib/taskfactory.h"
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
const int MAX_SCORE = 60;

const int CAT_SUB = 0;
const int CAT_POSS_MAJOR = 2;
const int CAT_PROB_MAJOR = 3;
const int CAT_MAJOR = 4;

const int FREQ_DAILY    = 4;
const int FREQ_5_7_DAYS = 3;
const int FREQ_3_4_DAYS = 2;
const int FREQ_1_2_DAYS = 1;
const int FREQ_NOT_AT_ALL = 0;

const int PROB_MAJOR_THRESH = 4;
const int POSS_MAJOR_THRESH = 3;
const int MAJOR_THRESH = 2;

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
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);

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
    return tr("CESD-R: Center for Epidemiologic Studies Depression Scale Revised");
}


QString Cesdr::menusubtitle() const
{
    return tr("20-item self-report depression scale.");
}


Version Cesdr::minimumServerVersion() const
{
    return Version(2, 2, 8);
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
        totalScorePhrase(totalScore(), MAX_SCORE),
        standardResult(xstring("depression_or_risk_of"),
                       uifunc::yesNoUnknown(hasDepressionRisk())),
    };
}


QStringList Cesdr::detail() const
{
    QStringList lines = completenessInfo();
    lines += summary();

    const int cat = depressionCategory(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
    lines.append(xstring("depression_category") + " " + xstring("category_" + QString::number(cat)));

    return lines;
}

int Cesdr::depressionCategory(QVector<QVariant> responses) const
{
    /*
     * Determining CESD-R categories
     * See: https://cesd-r.com/cesdr/
     */
    if (countWhere(responses, QVector<QVariant>{FREQ_DAILY}) >= MAJOR_THRESH) {
        return CAT_MAJOR;
    } else if (countWhere(responses, QVector<QVariant>{FREQ_5_7_DAYS}) > PROB_MAJOR_THRESH) {
        return CAT_PROB_MAJOR;
    } else if (countWhere(responses, QVector<QVariant>{FREQ_5_7_DAYS}) > POSS_MAJOR_THRESH) {
        return CAT_POSS_MAJOR;
    }

    return CAT_SUB;
}

OpenableWidget* Cesdr::editor(const bool read_only)
{
    const NameValueOptions options{
        {xstring("a0"), FREQ_NOT_AT_ALL},
        {xstring("a1"), FREQ_1_2_DAYS},
        {xstring("a2"), FREQ_3_4_DAYS},
        {xstring("a3"), FREQ_5_7_DAYS},
        {xstring("a4"), FREQ_DAILY},
    };

    QuPagePtr page((new QuPage{
        new QuText(xstring("instructions")),
        (new QuMcqGrid(
            {
                QuestionWithOneField(xstring("q1"), fieldRef("q1")),
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
                QuestionWithOneField(xstring("q20"), fieldRef("q20"))
            },
            options
        ))->setTitle(xstring("stem")),
    })->setTitle(xstring("title")));

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Cesdr::totalScore() const
{
    // In order to make the revised CESD-R have the same range as the original version i.e., the ‘CESD style score’),
    // the values for the top two responses are given the same value.
    // See: https://cesd-r.com/cesdr/

    QVector<QVariant> responses = values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS));

    return sumInt(responses) - countWhere(responses, QVector<QVariant>{FREQ_DAILY});
}


QVariant Cesdr::hasDepressionRisk() const
{
    return totalScore() >= 16;
}


int Cesdr::numNull(const int first, const int last) const
{
    return countNull(values(strseq(QPREFIX, first, last)));
}
