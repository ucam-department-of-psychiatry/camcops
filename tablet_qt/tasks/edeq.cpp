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

#include "edeq.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/quheight.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumass.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/quunitselector.h"
#include "tasklib/taskfactory.h"
using mathfunc::anyNull;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_QUESTIONS = 28;
const QString QPREFIX("q");
const QString Q_MASS_KG("q_mass_kg");
const QString Q_HEIGHT_M("q_height_m");
const QString Q_NUM_PERIODS_MISSED("q_num_periods_missed");
const QString Q_PILL("q_pill");

const QString Edeq::EDEQ_TABLENAME("edeq");


void initializeEdeq(TaskFactory& factory)
{
    static TaskRegistrar<Edeq> registered(factory);
}

Edeq::Edeq(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, EDEQ_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr),
    m_have_missed_periods_fr(nullptr),
    m_num_periods_missed_grid(nullptr)
{
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);

    addField(Q_MASS_KG, QVariant::Double);
    addField(Q_HEIGHT_M, QVariant::Double);
    addField(Q_NUM_PERIODS_MISSED, QVariant::Int, false, false, false, 0);
    addField(Q_PILL, QVariant::Bool, false, false, false, false);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}
// ============================================================================
// Class info
// ============================================================================

QString Edeq::shortname() const
{
    return "EDE-Q";
}


QString Edeq::longname() const
{
    return tr("Eating Disorder Examination Questionnaire");
}


QString Edeq::description() const
{
    return tr("A self-report version of the Eating Disorder Examination (EDE)");
}


QStringList Edeq::fieldNames() const
{
    auto field_names = strseq(QPREFIX, FIRST_Q, N_QUESTIONS) + QStringList {
        Q_MASS_KG, Q_HEIGHT_M};

    if (isFemale()) {
        field_names += {Q_NUM_PERIODS_MISSED, Q_PILL};
    }

    return field_names;
}

// ============================================================================
// Instance info
// ============================================================================


bool Edeq::isComplete() const
{
    if (anyNull(values(fieldNames()))) {
        return false;
    }

    return true;
}


QStringList Edeq::summary() const
{
    return QStringList{};
}


QStringList Edeq::detail() const
{
    QStringList lines;

    return lines;
}


OpenableWidget* Edeq::editor(const bool read_only)
{
    const NameValueOptions days_options{
        {xstring("days_option_0"), 0},
        {xstring("days_option_1"), 1},
        {xstring("days_option_2"), 2},
        {xstring("days_option_3"), 3},
        {xstring("days_option_4"), 4},
        {xstring("days_option_5"), 5},
        {xstring("days_option_6"), 6},
    };

    const NameValueOptions freq_options{
        {xstring("freq_option_0"), 0},
        {xstring("freq_option_1"), 1},
        {xstring("freq_option_2"), 2},
        {xstring("freq_option_3"), 3},
        {xstring("freq_option_4"), 4},
        {xstring("freq_option_5"), 5},
        {xstring("freq_option_6"), 6},
    };

    const NameValueOptions how_much_options{
        {xstring("how_much_option_0"), 0},
        {xstring("how_much_option_1"), 1},
        {xstring("how_much_option_2"), 2},
        {xstring("how_much_option_3"), 3},
        {xstring("how_much_option_4"), 4},
        {xstring("how_much_option_5"), 5},
        {xstring("how_much_option_6"), 6},
    };

    auto instructions = new QuHeading(xstring("instructions"));
    auto instructions1_12 = new QuHeading(xstring("q1_12_instructions"));
    auto heading1_12 = new QuHeading(xstring("q1_12_heading"));
    QString title = xstring("title_main");
    QVector<QuPagePtr> pages;
    for (int q_num = 1; q_num <= 12; q_num++) {
        auto question = new QuMcq(fieldRef(QPREFIX + QString::number(q_num)),
                                  days_options);
        pages.append(QuPagePtr((new QuPage({instructions, instructions1_12, heading1_12,
                                            question}))->setTitle(title)));
    }

    auto instructions13_18 = new QuHeading(xstring("q13_18_instructions"));
    auto heading13_18 = new QuHeading(xstring("q13_18_heading"));

    for (int q_num = 13; q_num <= 18; q_num++) {
        const QString& fieldname = QPREFIX + QString::number(q_num);
        auto number_edit = new QuLineEditInteger(fieldRef(fieldname),
0, 1000); // TODO: Better maximum
        auto question_text = new QuText(xstring(fieldname));
        pages.append(QuPagePtr((new QuPage({instructions, instructions13_18, heading13_18,
                                            question_text, number_edit}))->setTitle(title)));
    }

    auto instructions19_21 = new QuHeading(xstring("q19_21_instructions"));
    auto question19 = new QuMcq(fieldRef(QPREFIX + QString::number(19)),
                                days_options);
    pages.append(QuPagePtr((new QuPage({instructions, instructions19_21, new QuText(xstring(QPREFIX + "19")),
                                        question19}))->setTitle(title)));
    auto question20 = new QuMcq(fieldRef(QPREFIX + QString::number(20)), freq_options);
    pages.append(QuPagePtr((new QuPage({
                        instructions,
                        instructions19_21,
                        new QuText(xstring(QPREFIX + "20")),
                        question20}))->setTitle(title)));
    auto question21 = new QuMcq(fieldRef(QPREFIX + QString::number(21)),
                                freq_options);
    pages.append(QuPagePtr((new QuPage({instructions, instructions19_21, new QuText(xstring(QPREFIX + "21")),
                                        question21}))->setTitle(title)));

    auto instructions22_28 = new QuHeading(xstring("q22_28_instructions"));
    auto heading22_28 = new QuHeading(xstring("q22_28_heading"));
    for (int q_num = 22; q_num <= 28; q_num++) {
        auto question = new QuMcq(fieldRef(QPREFIX + QString::number(q_num)),
                                  days_options);
        pages.append(QuPagePtr((new QuPage({instructions, instructions22_28, heading22_28,
                                            question}))->setTitle(title)));
    }

    auto mass_text = new QuText(xstring(Q_MASS_KG));
    auto mass_units = new QuUnitSelector(CommonOptions::massUnits());
    auto mass_edit = new QuMass(fieldRef(Q_MASS_KG), mass_units);
    pages.append(QuPagePtr((new QuPage({mass_text, mass_units, mass_edit}))->setTitle(title)));
    auto height_text = new QuText(xstring(Q_HEIGHT_M));
    auto height_units = new QuUnitSelector(CommonOptions::heightUnits());
    auto height_edit = new QuHeight(fieldRef(Q_HEIGHT_M), height_units);
    pages.append(QuPagePtr((new QuPage({height_text, height_units, height_edit}))->setTitle(title)));

    if (isFemale()) {
        FieldRef::GetterFunction get_have_missed_periods = std::bind(&Edeq::getHaveMissedPeriods, this);
        FieldRef::SetterFunction set_have_missed_periods = std::bind(&Edeq::setHaveMissedPeriods, this, std::placeholders::_1);
        m_have_missed_periods_fr = FieldRefPtr(new FieldRef(get_have_missed_periods, set_have_missed_periods, true));
        auto have_missed_periods_edit = (
            new QuMcq(
                m_have_missed_periods_fr,
                CommonOptions::yesNoBoolean()
                )
            );
        auto num_periods_missed_edit = new QuLineEditInteger(fieldRef(Q_NUM_PERIODS_MISSED), 0, 10);
        auto have_missed_periods_grid = questionnairefunc::defaultGridRawPointer(
            {
                {xstring("q_have_missed_periods"), have_missed_periods_edit},
            }, 1, 1);
        m_num_periods_missed_grid = questionnairefunc::defaultGridRawPointer(
            {
                {xstring(Q_NUM_PERIODS_MISSED), num_periods_missed_edit}
            }, 1, 1);
        pages.append(QuPagePtr((new QuPage({have_missed_periods_grid,
                                            m_num_periods_missed_grid}))->setTitle(title)));

        auto pill_edit = new QuMcq(fieldRef(Q_PILL), CommonOptions::yesNoBoolean());
        auto pill_grid = questionnairefunc::defaultGridRawPointer(
            {{xstring("q_pill"), pill_edit}}, 1, 1);
        pages.append(QuPagePtr((new QuPage({pill_grid}))->setTitle(title)));
    }

    auto thanks = new QuText(xstring("thanks"));
    pages.append(QuPagePtr((new QuPage({thanks}))->setTitle(title)));

    m_questionnaire = new Questionnaire(m_app, pages);
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    m_have_missed_periods_fr->setValue(valueInt(Q_NUM_PERIODS_MISSED) > 0);

    return m_questionnaire;
}


QVariant Edeq::getHaveMissedPeriods()
{
    return m_have_missed_periods;
}


bool Edeq::setHaveMissedPeriods(const QVariant& value)
{
    const bool changed = value != m_have_missed_periods;

    if (changed) {
        m_have_missed_periods = value;

        const bool have_missed = value.toBool();

        if (!have_missed) {
            setValue(Q_NUM_PERIODS_MISSED, 0);
        }

        m_num_periods_missed_grid->setVisible(have_missed);
    }

    return changed;
}
