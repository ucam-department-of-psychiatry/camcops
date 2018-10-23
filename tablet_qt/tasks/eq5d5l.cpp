#include "eq5d5l.h"

#include "lib/uifunc.h"
#include "lib/stringfunc.h"
#include "lib/version.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quboolean.h"
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
const QString TASK1_INSTRUCTION("t1_instruction");


const int FIRST_Q = 1;
const int LAST_Q = 5;

const int FIRST_OPT = 1;
const int LAST_OPT = 5;

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
    QVector<QuElement*> elements;


    for (auto field : strseq(QPREFIX, FIRST_Q, LAST_Q)) {

        const QString opt_stem = QString("%1_%2").arg(field, OPT_PREFIX);

        NameValueOptions options;
        int opt_val = 0;
        for (auto option : strseq(opt_stem, FIRST_OPT, LAST_OPT)) {
            options.append(NameValuePair(option, opt_val));
            opt_val++;
        }
        elements.append({
            new QuText(xstring("instruction")),
            new QuMcq(fieldRef(field), options),
        });

        pages.append(QuPagePtr(new QuPage(elements)));

        elements.clear();
    }
    QVector<QuThermometerItem> items;

    for (int i = 0; i <= 100; ++i) {
//        QString text = QString::number(i);
//        QuThermometerItem item;

//        item.text(text);

/*
            uifunc::resourceFilename(
                        QString("distressthermometer/dt_sel_%1.png").arg(i)),
            uifunc::resourceFilename(
                        QString("distressthermometer/dt_unsel_%1.png").arg(i)),
            text,
            i
        );
*/
        items.append(item);
    }

    pages.prepend(
       QuPagePtr(new QuPage{
         (new QuGridContainer{
            QuGridCell(new QuVerticalContainer{
                new QuText(xstring("t2_i1")),
                new QuText(xstring("t2_i2")),
                new QuText(xstring("t2_i3")),
                new QuText(xstring("t2_i4")),
                new QuText(xstring("t2_i5")),
                new QuSpacer(),
                new QuHorizontalContainer{
                  new QuText("YOUR HEALTH TODAY = "),
                 new QuLineEditInteger(fieldRef("thermometer"), 0, 100)
                },
            }, 0, 0, 3, 1),
           QuGridCell(
            (new QuThermometer(fieldRef("thermometer"), items))
                     ->setRescale(true, 0.5),
            0, 1, 2, 1, Qt::AlignRight | Qt::AlignRight)
         })
       })
    );

    /*
QuThermometerItem item(
        uifunc::resourceFilename(
                    QString("distressthermometer/eq5d5l%1.png").arg(i)),
        uifunc::resourceFilename(
                    QString("distressthermometer/dt_unsel_%1.png").arg(i)),
        text,
        i
    );
    thermometer_items.append(item);

    pages.append(new QuPage{
        (new QuThermometer(fieldRef("thermometer"), thermometer_items))
    });
*/

    auto questionnaire = new Questionnaire(m_app, pages);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}
/*

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
    return q;*/
















