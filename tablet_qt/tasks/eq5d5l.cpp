#include "eq5d5l.h"

#include "lib/stringfunc.h"
#include "lib/version.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/quslider.h"
#include "tasklib/taskfactory.h"

const QString Eq5d5l::EQ5D5L_TABLENAME("eq5d5l");

const QString QPREFIX("q");
const QString TASK1_INSTRUCTION("t1_instruction");


const int FIRST_Q = 1;
const int N_SECTIONS = 5;
const int Q_PER_SECTION = 5;

using stringfunc::strnum;
using stringfunc::strseq;

void initializeEq5d5l(TaskFactory& factory)
{
    static TaskRegistrar<Eq5d5l> registered(factory);
}

Eq5d5l::Eq5d5l(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, EQ5D5L_TABLENAME, false, false, false),
    m_in_tickbox_change(false)
{
    const int n_questions = N_SECTIONS * Q_PER_SECTION;
    for (auto field : strseq(QPREFIX, FIRST_Q, n_questions)) {
        addField(field, QVariant::Int);
    }

    addField("slider", QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Eq5d5l::shortname() const
{
    return "EQ-5D-5L";
}


QString Eq5d5l::longname() const
{
    return tr("Self-rated health scale");
}


QString Eq5d5l::menusubtitle() const
{
    return tr("Self-rated health scale.");
}


Version Eq5d5l::minimumServerVersion() const
{
    return Version(2, 2, 8);
}


// ============================================================================
// Instance info
// ============================================================================

QStringList Eq5d5l::summary() const
{
    return QStringList{};
}


QStringList Eq5d5l::detail() const
{
    return QStringList{};
}


bool Eq5d5l::isComplete() const
{
    return true;
}


OpenableWidget* Eq5d5l::editor(const bool read_only)
{
    QVector<QuPagePtr> pages;
    auto addpage = [this, &pages](int n) -> void {
        NameValueOptions options;
        for (int i = 1; i <= Q_PER_SECTION; ++i) {
            const QString name = xstring(QString("q%1").arg(i+(n*Q_PER_SECTION)));
            options.append(NameValuePair(name, i));
        }
        const QString pagetitle = xstring(QString("h%1").arg(n));
        const QString instruction = xstring(QString(TASK1_INSTRUCTION));
        const QString fieldname = strnum(QPREFIX, n);
        QuPagePtr page((new QuPage{
            new QuText(instruction),
            new QuMcq(fieldRef(fieldname), options),
        })->setTitle(pagetitle));
        pages.append(page);
    };

    for (int n = 1; n <= N_SECTIONS; ++n) {
        addpage(n);
    }

    QuSlider *slider = (new QuSlider(fieldRef("slider"), 0, 100, 1))
                        ->setShowValue(true)
                        ->setTickInterval(5)
                        ->setTickPosition(QSlider::TicksRight)
                        ->setUseDefaultTickLabels(true)
                        ->setTickLabelPosition(QSlider::TicksRight)
                        ->setHorizontal(false);

    QuPagePtr page(new QuPage{
                       (new QuGridContainer{
                           QuGridCell(slider, 0, 1),
                       })
            });


    pages.append(page);

//                            ->setTickInterval(1)
//                            ->setTickPosition(QSlider::TicksBothSides)
//                            ->setShowValue(true)
//    page.append(page);

    auto q = new Questionnaire(m_app, pages);
    q->setReadOnly(read_only);
    return q;
}















