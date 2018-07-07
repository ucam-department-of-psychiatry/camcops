/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

#include "khandaker1medicalhistory.h"
#include "common/cssconst.h"
#include "common/textconst.h"
#include "maths/mathfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/qubackground.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "tasklib/taskfactory.h"

struct KQInfo {
    KQInfo(const QString& stem, const QString& heading_xml = "") {
        // Fieldnames:
        fieldname_yn = stem + "_yn";
        fieldname_comment = stem + "_comment";
        // XML:
        question_xmlstr = "q_" + stem;
        heading_xmlstr = heading_xml;
    }
    bool hasHeading() const {
        return !heading_xmlstr.isEmpty();
    }

    QString fieldname_yn;
    QString fieldname_comment;
    QString question_xmlstr;
    QString heading_xmlstr;
};

const QVector<KQInfo> QUESTIONS{
    KQInfo("cancer", "heading_cancer"),
    KQInfo("epilepsy", "heading_brain"),
    KQInfo("cva_headinjury_braintumour"),
    KQInfo("ms_pd_dementia"),
    KQInfo("cerebralpalsy_otherbrain"),
    KQInfo("visual_impairment"),
    KQInfo("heart_disorder", "heading_cardiovascular"),
    KQInfo("respiratory", "heading_respiratory"),
    KQInfo("gastrointestinal", "heading_gastrointestinal"),
    KQInfo("other_inflammatory", "heading_inflammatory"),
    KQInfo("musculoskeletal", "heading_musculoskeletal"),
    KQInfo("renal_urinary", "heading_renal_urinary"),
    KQInfo("dermatological", "heading_dermatological"),
    KQInfo("diabetes", "heading_endocrinological"),
    KQInfo("other_endocrinological"),
    KQInfo("haematological", "heading_haematological"),
    KQInfo("infections", "heading_infections"),
};

const QString Khandaker1MedicalHistory::KHANDAKER1MEDICALHISTORY_TABLENAME(
        "khandaker_1_medicalhistory");

const QString X_TITLE("title");
const QString X_INSTRUCTION("instruction");
const QString X_HEADING_CONDITION("heading_condition");
const QString X_HEADING_YN("heading_yn");
const QString X_HEADING_COMMENT("heading_comment");
const QString X_COMMENT_HINT("comment_hint");

const int COLUMN_Q = 0;
const int COLUMN_YN = 1;
const int COLUMN_COMMENT = 2;
const int NCOL = 3;

const int STRETCH_Q = 40;
const int STRETCH_YN = 20;
const int STRETCH_COMMENT = 40;


void initializeKhandaker1MedicalHistory(TaskFactory& factory)
{
    static TaskRegistrar<Khandaker1MedicalHistory> registered(factory);
}


Khandaker1MedicalHistory::Khandaker1MedicalHistory(
        CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, KHANDAKER1MEDICALHISTORY_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    for (const KQInfo& info : QUESTIONS) {
        addField(info.fieldname_yn, QVariant::Bool);
        addField(info.fieldname_comment, QVariant::String);
    }

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}



// ============================================================================
// Class info
// ============================================================================

QString Khandaker1MedicalHistory::shortname() const
{
    return "Khandaker_1_MedicalHistory";
}


QString Khandaker1MedicalHistory::longname() const
{
    return "Khandaker GM — 1 — Insight — Medical history";
}


QString Khandaker1MedicalHistory::menusubtitle() const
{
    return "Medical history screening for Insight immunopsychiatry study.";
}


QString Khandaker1MedicalHistory::infoFilenameStem() const
{
    return "khandaker_1";
}


// ============================================================================
// Instance info
// ============================================================================

bool Khandaker1MedicalHistory::isComplete() const
{
    for (const KQInfo& info : QUESTIONS) {
        if (valueIsNull(info.fieldname_yn)) {
            return false;
        }
        if (valueBool(info.fieldname_yn) &&
                valueIsNullOrEmpty(info.fieldname_comment)) {
            return false;
        }
    }
    return true;
}


QStringList Khandaker1MedicalHistory::summary() const
{
    return QStringList{textconst::NO_SUMMARY_SEE_FACSIMILE};
}


QStringList Khandaker1MedicalHistory::detail() const
{
    QStringList lines;
    for (const KQInfo& info : QUESTIONS) {
        QString comment = "";
        if (!valueIsNullOrEmpty(info.fieldname_comment) ||
                valueBool(info.fieldname_yn)) {
            // Show comment if the answer was yes or there is a comment.
            comment = QString(" - %1").arg(valueString(info.fieldname_comment));
        }
        lines.append(QString("%1: <b>%2%3</b>").arg(
                         xstring(info.question_xmlstr),
                         uifunc::yesNoNull(value(info.fieldname_yn)),
                         comment));
    }
    return completenessInfo() + lines;
}


OpenableWidget* Khandaker1MedicalHistory::editor(const bool read_only)
{
    const NameValueOptions yn_options = CommonOptions::yesNoBoolean();
    const Qt::Alignment cell_alignment = Qt::AlignTop;
    // AlignLeft makes multiline expanding text boxes become too narrow.

    QuPagePtr page(new QuPage);
    page->setTitle(menusubtitle());
    page->addElement(new QuHeading(xstring(X_TITLE)));
    page->addElement(new QuText(xstring(X_INSTRUCTION)));

    QuGridContainer* grid = new QuGridContainer;
    int row = 0;

    // Column headings
    QuText* heading_q = new QuText(xstring(X_HEADING_CONDITION));
    heading_q->setBold(true);
    QuGridCell headcell_q(heading_q, row, COLUMN_Q, 1, 1, cell_alignment);
    grid->addCell(headcell_q);

    QuText* heading_yn = new QuText(xstring(X_HEADING_YN));
    heading_yn->setBold(true);
    QuGridCell headcell_yn(heading_yn, row, COLUMN_YN, 1, 1, cell_alignment);
    grid->addCell(headcell_yn);

    QuText* heading_comment = new QuText(xstring(X_HEADING_COMMENT));
    heading_comment->setBold(true);
    QuGridCell headcell_comment(heading_comment, row, COLUMN_COMMENT, 1, 1, cell_alignment);
    grid->addCell(headcell_comment);

    ++row;

    // Questions and subheadings
    for (const KQInfo& info : QUESTIONS) {
        if (info.hasHeading()) {
            QuBackground* subhead_bg = new QuBackground(cssconst::OPTION_BACKGROUND);
            QuGridCell subhead_bg_cell(subhead_bg, row, COLUMN_Q, 1, NCOL);
            grid->addCell(subhead_bg_cell);
            QuText* heading = new QuText(xstring(info.heading_xmlstr));
            QuGridCell subhead_cell(heading, row, COLUMN_Q, 1, NCOL, cell_alignment);
            grid->addCell(subhead_cell);
            ++row;
        }

        const bool even = row % 2 == 0;
        const char* bg_obj_name = even ? cssconst::STRIPE_BACKGROUND_EVEN
                                       : cssconst::STRIPE_BACKGROUND_ODD;
        QuBackground* row_bg = new QuBackground(bg_obj_name);
        QuGridCell bg_cell(row_bg, row, COLUMN_Q, 1, NCOL);
        grid->addCell(bg_cell);

        QuText* question = new QuText(xstring(info.question_xmlstr));
        QuGridCell q_cell(question, row, COLUMN_Q, 1, 1, cell_alignment);
        grid->addCell(q_cell);

        FieldRefPtr yn_fieldref = fieldRef(info.fieldname_yn);
        connect(yn_fieldref.data(), &FieldRef::valueChanged,
                this, &Khandaker1MedicalHistory::updateMandatory);
        QuMcq* mcq = new QuMcq(yn_fieldref, yn_options);
        mcq->setAsTextButton(true);
        mcq->setHorizontal(true);
        QuGridCell yn_cell(mcq, row, COLUMN_YN, 1, 1, cell_alignment);
        grid->addCell(yn_cell);

        QuTextEdit* comment = new QuTextEdit(fieldRef(info.fieldname_comment));
        comment->setHint(xstring(X_COMMENT_HINT));
        QuGridCell comment_cell(comment, row, COLUMN_COMMENT, 1, 1, cell_alignment);
        grid->addCell(comment_cell);

        ++row;
    }

    grid->setColumnStretch(COLUMN_Q, STRETCH_Q);
    grid->setColumnStretch(COLUMN_YN, STRETCH_YN);
    grid->setColumnStretch(COLUMN_COMMENT, STRETCH_COMMENT);
    page->addElement(grid);

    QVector<QuPagePtr> pages{page};

    updateMandatory();

    Questionnaire* questionnaire = new Questionnaire(m_app, pages);
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Signal handlers
// ============================================================================

void Khandaker1MedicalHistory::updateMandatory()
{
    // This could be more efficient with lots of signal handlers, but...

    for (const KQInfo& info : QUESTIONS) {
        const bool y = valueBool(info.fieldname_yn);
        fieldRef(info.fieldname_comment)->setMandatory(y);
    }
}
