#include "eq5d5l.h"

#include "lib/uifunc.h"
#include "lib/stringfunc.h"
#include "lib/version.h"
#include "maths/mathfunc.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quboolean.h"
#include "questionnairelib/quflowcontainer.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/quhorizontalcontainer.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/quthermometer.h"
#include "questionnairelib/quverticalcontainer.h"
#include "tasklib/taskfactory.h"

const QString Eq5d5l::EQ5D5L_TABLENAME("eq5d5l");

const QString QPREFIX("q");
const QString OPT_PREFIX("o");


const int FIRST_Q = 1;
const int LAST_Q = 5;

using mathfunc::noneNull;
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
    addFields(strseq(QPREFIX, FIRST_Q, LAST_Q), QVariant::Int);

    addField("thermometer", QVariant::Int);

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
    return tr("EQ 5-Dimension, 5-Level Health Scale");
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
//    return QStringList{totalScorePhrase(totalScore(), MAX_SCORE)};
}

QStringList Eq5d5l::detail() const
{
    QStringList lines = completenessInfo();
    lines.append(xstring("hstate_raw"));

    for (auto s : getScoreStrings()) {
        lines.append(s);
    }

    return lines;
}

QVector<QString> Eq5d5l::getScoreStrings() const {
    QString descriptive = "";
    QVariant v;
    for (auto field : strseq(QPREFIX, FIRST_Q, LAST_Q)) {
        v = value(field);
        descriptive += (v.isNull() ? "9" : QString::number(v.toInt() + 1));
    }

    QString visual = "";
    v = value("thermometer");
    visual += (v.isNull() ? "999" : QString::number(v.toInt()));

    return QVector<QString>{descriptive, visual};
}

bool Eq5d5l::isComplete() const
{
    return noneNull(values(strseq(QPREFIX, FIRST_Q, LAST_Q))) &&
            !value("thermometer").isNull();
}


OpenableWidget* Eq5d5l::editor(const bool read_only)
{
    QVector<QuPagePtr> pages;
    QVector<QuElement*> elements;

    for (auto field : strseq(QPREFIX, FIRST_Q, LAST_Q)) {
        const QString heading = QString("%1_h").arg(field);
        const QString qnumstr = QString("%1_%2").arg(field, OPT_PREFIX);

        NameValueOptions options{
            {xstring(qnumstr + "1"), 0},
            {xstring(qnumstr + "2"), 1},
            {xstring(qnumstr + "3"), 2},
            {xstring(qnumstr + "4"), 3},
            {xstring(qnumstr + "5"), 4},
        };

        elements.append({
            (new QuText(xstring("t1_instruction")))->setBold(),
            new QuMcq(fieldRef(field), options)
        });

        pages.append(QuPagePtr(
            (new QuPage(elements))
                ->setTitle(shortname())
                ->setIndexTitle(xstring(heading))
        ));

        elements.clear();
    }
    QVector<QuThermometerItem> items;

    QString prefix("eq5d5lslider");
    QString n, resource;

    items.append(QuThermometerItem(
        uifunc::resourceFilename("eq5d5lslider/base.png"),
        uifunc::resourceFilename("eq5d5lslider/base_unsel.png"),
        "0", 0
    ));

    const int overspill_rows = 3;
    QString itemtext;
    for (int i = 1; i < 100; ++i) {

        n = QString::number(i);

        if (i % 5 == 0) {
            // larger ticks with numbers every 5
            resource = "eq5d5lslider/mid%1.png";
            itemtext = n;
        } else {
            resource = "eq5d5lslider/tick%1.png";
            itemtext = "";
        }

        QuThermometerItem item(
            uifunc::resourceFilename(resource.arg("")),  // active
            uifunc::resourceFilename(resource.arg("_unsel")),  // inactive
            itemtext,  // text
            i,  // value
            overspill_rows
        );

        items.append(item);
    }

    items.append(QuThermometerItem(
        uifunc::resourceFilename("eq5d5lslider/top.png"),
        uifunc::resourceFilename("eq5d5lslider/top_unsel.png"),
        "100", 100
    ));

    QVector<QuElementPtr> instructions;
    for (int i = 1; i <= 5; ++i) {
        instructions.append(
           QuElementPtr(new QuFlowContainer{
            (new QuText(xstring(strnum("t2_i", i))))
                ->setBig()
           })
        );
        instructions.append(QuElementPtr(new QuSpacer));
    }

    instructions.append(QuElementPtr(new QuSpacer));
    instructions.append(QuElementPtr(
        new QuHorizontalContainer{
            (new QuText("YOUR HEALTH TODAY ="))->setBig(),
            new QuLineEditInteger(fieldRef("thermometer"), 0, 100)
        }
    ));

    QuThermometer* therm = new QuThermometer(fieldRef("thermometer"), items);
    // ... will be owned by the grid when inserted;
    therm->setRescale(true, 0.75, true);

    pages.append(
       QuPagePtr((new QuPage{
        new QuGridContainer{
            QuGridCell(
                new QuVerticalContainer{instructions}, 0, 0, 4),
            QuGridCell(therm, 0, 1, 4)
       }})->setTitle(shortname())
          ->setIndexTitle(xstring("t2_h")))
    );

    auto questionnaire = new Questionnaire(m_app, pages);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}
