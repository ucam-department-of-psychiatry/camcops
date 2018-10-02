#include "cesd.h"
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
using mathfunc::noneNull;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;
using stringfunc::standardResult;
using stringfunc::strnum;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_QUESTIONS = 20;
const int MAX_SCORE = 60;

const QString QPREFIX("q");
const QString Cesd::CESD_TABLENAME("cesd");


void initializeCesd(TaskFactory& factory)
{
    static TaskRegistrar<Cesd> registered(factory);
}


Cesd::Cesd(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
            Task(app, db, CESD_TABLENAME, false, false, false),
            m_questionnaire(nullptr)
{
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Cesd::shortname() const
{
    return "CESD";
}


QString Cesd::longname() const
{
    return tr("CESD: Center for Epidemiologic Studies Depression Scale");
}


QString Cesd::menusubtitle() const
{
    return tr("20-item self-report depression scale.");
}


Version Cesd::minimumServerVersion() const
{
    return Version(2, 2, 8);
}


// ============================================================================
// Instance info
// ============================================================================

bool Cesd::isComplete() const
{
    return noneNull(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


QStringList Cesd::summary() const
{
    return QStringList{
        totalScorePhrase(totalScore(), MAX_SCORE),
        standardResult(xstring("depression_or_risk_of"),
                       uifunc::yesNoUnknown(hasDepressionRisk()))
    };
}


QStringList Cesd::detail() const
{
    QStringList lines = completenessInfo();
    lines += summary();
    return lines;
}


OpenableWidget* Cesd::editor(const bool read_only)
{
    const NameValueOptions options{
        {xstring("a0"), 0},
        {xstring("a1"), 1},
        {xstring("a2"), 2},
        {xstring("a3"), 3}
    };

    const NameValueOptions options_reversed{
        {xstring("a0"), 3},
        {xstring("a1"), 2},
        {xstring("a2"), 1},
        {xstring("a3"), 0},
    };

    const int question_width = 40;
    const QVector<int> option_widths{15, 15, 15, 15};

    QuPagePtr page((new QuPage{
                        (new QuText(xstring("instruction_1")))->setBold(true),
                        new QuText(xstring("instruction_2")),
                        (new QuMcqGrid(
                        {
                            QuestionWithOneField(xstring("q1"), fieldRef("q1")),
                            QuestionWithOneField(xstring("q2"), fieldRef("q2")),
                            QuestionWithOneField(xstring("q3"), fieldRef("q3")),
                        },
                        options
                        ))
                        ->setTitle(xstring("stem"))
                        ->setWidth(question_width, option_widths)
                        ->setExpand(true)
                        ->setQuestionsBold(false),
                        (new QuMcqGrid(
                        {
                            QuestionWithOneField(xstring("q4"), fieldRef("q4")),
                        },
                        options_reversed
                        ))
                        ->showTitle(false)
                        ->setWidth(question_width, option_widths)
                        ->setExpand(true)
                        ->setQuestionsBold(false),
                        (new QuMcqGrid(
                        {
                            QuestionWithOneField(xstring("q5"), fieldRef("q5")),
                            QuestionWithOneField(xstring("q6"), fieldRef("q6")),
                            QuestionWithOneField(xstring("q7"), fieldRef("q7")),
                        },
                        options
                        ))
                        ->showTitle(false)
                        ->setWidth(question_width, option_widths)
                        ->setExpand(true)
                        ->setQuestionsBold(false),
                        (new QuMcqGrid(
                        {
                            QuestionWithOneField(xstring("q8"), fieldRef("q8")),
                        },
                        options_reversed
                        ))
                        ->showTitle(false)
                        ->setWidth(question_width, option_widths)
                        ->setExpand(true)
                        ->setQuestionsBold(false),
                        (new QuMcqGrid(
                        {
                            QuestionWithOneField(xstring("q9"), fieldRef("q9")),
                            QuestionWithOneField(xstring("q10"), fieldRef("q10")),
                            QuestionWithOneField(xstring("q11"), fieldRef("q11")),
                        },
                        options
                        ))
                        ->showTitle(false)
                        ->setWidth(question_width, option_widths)
                        ->setExpand(true)
                        ->setQuestionsBold(false),
                        (new QuMcqGrid(
                        {
                            QuestionWithOneField(xstring("q12"), fieldRef("q12")),
                        },
                        options_reversed
                        ))
                        ->showTitle(false)
                        ->setWidth(question_width, option_widths)
                        ->setExpand(true)
                        ->setQuestionsBold(false),
                        (new QuMcqGrid(
                        {
                            QuestionWithOneField(xstring("q13"), fieldRef("q13")),
                            QuestionWithOneField(xstring("q14"), fieldRef("q14")),
                            QuestionWithOneField(xstring("q15"), fieldRef("q15")),
                        },
                        options
                        ))
                        ->showTitle(false)
                        ->setWidth(question_width, option_widths)
                        ->setExpand(true)
                        ->setQuestionsBold(false),
                        (new QuMcqGrid(
                        {
                            QuestionWithOneField(xstring("q16"), fieldRef("q16")),
                        },
                        options_reversed
                        ))
                        ->showTitle(false)
                        ->setWidth(question_width, option_widths)
                        ->setExpand(true)
                        ->setQuestionsBold(false),
                        (new QuMcqGrid(
                        {
                            QuestionWithOneField(xstring("q17"), fieldRef("q17")),
                            QuestionWithOneField(xstring("q18"), fieldRef("q18")),
                            QuestionWithOneField(xstring("q19"), fieldRef("q19")),
                            QuestionWithOneField(xstring("q20"), fieldRef("q20")),
                        },
                        options
                        ))
                        ->showTitle(false)
                        ->setWidth(question_width, option_widths)
                        ->setExpand(true)
                        ->setQuestionsBold(false),
                    }));

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Cesd::totalScore() const
{
    return sumInt(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


QVariant Cesd::hasDepressionRisk() const
{
    return totalScore() >= 16;
}


int Cesd::numNull(const int first, const int last) const
{
    return countNull(values(strseq(QPREFIX, first, last)));
}
