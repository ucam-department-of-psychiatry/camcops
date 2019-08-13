/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

#include "khandaker2mojosociodemographics.h"
#include "common/cssconst.h"
#include "common/textconst.h"
#include "maths/mathfunc.h"
#include "lib/uifunc.h"
#include "lib/version.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "tasklib/taskfactory.h"


const QString Khandaker2MojoSociodemographics::KHANDAKER2MOJOSOCIODEMOGRAPHICS_TABLENAME(
    "khandaker_2_mojosociodemographics");

struct K2QInfo {
    K2QInfo(const QString& stem, const int max_option,
            const bool has_other = false) {
        m_fieldname = stem;

        m_has_other = has_other;

        if (has_other) {
            m_other_fieldname = "other_" + stem;
        }
        m_question_xml_name = "q_" + stem;
        m_max_option = max_option;
    }

    bool hasOther() const {
        return m_has_other;
    }

    QString getFieldname() const {
        return m_fieldname;
    }

    QString getOtherFieldname() const {
        return m_other_fieldname;
    }

    QString getQuestionXmlName() const {
        return m_question_xml_name;
    }

    int getMaxOption() const {
        return m_max_option;
    }

private:
    QString m_fieldname;
    QString m_other_fieldname = QString();
    QString m_question_xml_name;
    int m_max_option;
    bool m_has_other;
};

const QVector<K2QInfo> MC_QUESTIONS{
    K2QInfo("gender", 2, true),
    K2QInfo("ethnicity", 10, true),
    K2QInfo("with_whom_live", 7, true),
    K2QInfo("relationship_status", 4),
    K2QInfo("education", 4),
    K2QInfo("employment", 7, true),
    K2QInfo("accommodation", 6, true),
};

void initializeKhandaker2MojoSociodemographics(TaskFactory& factory)
{
    static TaskRegistrar<Khandaker2MojoSociodemographics> registered(factory);
}


Khandaker2MojoSociodemographics::Khandaker2MojoSociodemographics(
        CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, KHANDAKER2MOJOSOCIODEMOGRAPHICS_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    addField("age", QVariant::Int);

    for (const K2QInfo& info : MC_QUESTIONS) {
        addField(info.getFieldname(), QVariant::Int);

        if (info.hasOther()) {
            addField(info.getOtherFieldname(), QVariant::String);
        }
    }

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}



// ============================================================================
// Class info
// ============================================================================

QString Khandaker2MojoSociodemographics::shortname() const
{
    return "Khandaker_2_MOJOSociodemographics";
}


QString Khandaker2MojoSociodemographics::longname() const
{
    return tr("Khandaker GM — 2 MOJO Study — Sociodemographics Questionnaire");
}


QString Khandaker2MojoSociodemographics::description() const
{
    return tr("Sociodemographics Questionnaire for MOJO Study.");
}




// ============================================================================
// Instance info
// ============================================================================

bool Khandaker2MojoSociodemographics::isComplete() const
{
    if (valueIsNull("age")) {
        return false;
    }

    for (const K2QInfo& info : MC_QUESTIONS) {
        if (valueIsNull(info.getFieldname())) {
            return false;
        }

        if (answeredOther(info) && valueIsNull(info.getOtherFieldname())) {
            return false;
        }
    }

    return true;
}


QStringList Khandaker2MojoSociodemographics::summary() const
{
    return QStringList{TextConst::noSummarySeeFacsimile()};
}


QStringList Khandaker2MojoSociodemographics::detail() const
{
    QStringList lines;

    lines.append(QString("%1: <b>%2</b>").arg(
                     xstring("q_age"), valueString("age")));

    for (const K2QInfo& info : MC_QUESTIONS) {
        const QString question_xml_name = info.getQuestionXmlName();
        const QString option_xml_name = getOptionName(
            info, valueInt(info.getFieldname()));

        QString other_value;

        if (answeredOther(info)) {
            const QString other_field_name = info.getOtherFieldname();
            other_value = valueString(other_field_name);
        } else {
            other_value = "";
        }

        lines.append(QString("%1: <b>%2 %3</b>").arg(
                         xstring(question_xml_name),
                         option_xml_name,
                         other_value));

    }

    return completenessInfo() + lines;
}


OpenableWidget* Khandaker2MojoSociodemographics::editor(const bool read_only)
{
    QuPagePtr page(new QuPage);
    page->setTitle(description());
    page->addElement(new QuHeading(xstring("title")));

    page->addElement(new QuText(xstring("q_age")));
    page->addElement(new QuLineEditInteger(fieldRef("age"), 0, 150));
    page->addElement(new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE)));

    for (const K2QInfo& info : MC_QUESTIONS) {
        page->addElement(new QuText(xstring(info.getQuestionXmlName())));

        FieldRefPtr fieldref = fieldRef(info.getFieldname());
        connect(fieldref.data(), &FieldRef::valueChanged,
                this, &Khandaker2MojoSociodemographics::updateMandatory);

        QuMcq* mcq = new QuMcq(fieldref, getOptions(info));
        page->addElement(mcq);

        if (info.hasOther()) {
            QString fieldname = info.getOtherFieldname();
            auto text_edit = new QuTextEdit(fieldRef(fieldname));
            text_edit->addTag(fieldname);
            page->addElement(text_edit);
        }

        page->addElement(new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE)));
    }

    QVector<QuPagePtr> pages{page};

    m_questionnaire = new Questionnaire(m_app, pages);
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    updateMandatory();

    return m_questionnaire;
}


bool Khandaker2MojoSociodemographics::answeredOther(const K2QInfo info) const {
    // For this task, the 'other' option is always the last one
    return info.hasOther() && valueInt(info.getFieldname()) == info.getMaxOption();
}

NameValueOptions Khandaker2MojoSociodemographics::getOptions(const K2QInfo info) const {
    NameValueOptions options;

    for (int i = 0; i <= info.getMaxOption(); i++) {
        const QString name = getOptionName(info, i);
        options.append(NameValuePair(name, i));
    }

    return options;
}

QString Khandaker2MojoSociodemographics::getOptionName(
    const K2QInfo info, const int index) const {
    return xstring(QString("%1_option%2").arg(info.getFieldname()).arg(index));
}

// ============================================================================
// Signal handlers
// ============================================================================

void Khandaker2MojoSociodemographics::updateMandatory()
{
    // This could be more efficient with lots of signal handlers, but...

    for (const K2QInfo& info : MC_QUESTIONS) {
        if (info.hasOther()) {
            const bool mandatory = answeredOther(info);
            fieldRef(info.getOtherFieldname())->setMandatory(mandatory);

            if (m_questionnaire) {
                m_questionnaire->setVisibleByTag(info.getOtherFieldname(),
                                                 mandatory);
            }
        }
    }
}
