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

#include "khandakermojomedicationtherapy.h"

#include "common/textconst.h"
#include "db/ancillaryfunc.h"
#include "db/fieldref.h"
#include "lib/uifunc.h"
#include "questionnairelib/qubutton.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quflowcontainer.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/qulineeditdouble.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/qupickerpopup.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
#include "tasklib/taskregistrar.h"
#include "taskxtra/khandakermojomedicationitem.h"
#include "taskxtra/khandakermojotherapyitem.h"

const QString
    KhandakerMojoMedicationTherapy::KHANDAKERMOJOMEDICATIONTHERAPY_TABLENAME(
        "khandaker_mojo_medicationtherapy"
    );

const QString Q_XML_PREFIX = "q_";

void initializeKhandakerMojoMedicationTherapy(TaskFactory& factory)
{
    static TaskRegistrar<KhandakerMojoMedicationTherapy> registered(factory);
}

KhandakerMojoMedicationTherapy::KhandakerMojoMedicationTherapy(
    CamcopsApp& app, DatabaseManager& db, const int load_pk
) :
    Task(
        app, db, KHANDAKERMOJOMEDICATIONTHERAPY_TABLENAME, false, false, false
    )  // ... anon, clin, resp
{
    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}

// ============================================================================
// Class info
// ============================================================================

QString KhandakerMojoMedicationTherapy::shortname() const
{
    return "Khandaker_MOJO_MedicationTherapy";
}

QString KhandakerMojoMedicationTherapy::longname() const
{
    return tr("Khandaker GM — MOJO — Medications and therapies");
}

QString KhandakerMojoMedicationTherapy::description() const
{
    return tr("Record of medications and talking therapies for MOJO study.");
}

QString KhandakerMojoMedicationTherapy::infoFilenameStem() const
{
    return "khandaker_mojo";
}

// ============================================================================
// Ancillary management
// ============================================================================

QStringList KhandakerMojoMedicationTherapy::ancillaryTables() const
{
    return QStringList{
        KhandakerMojoMedicationItem::KHANDAKERMOJOMEDICATIONITEM_TABLENAME,
        KhandakerMojoTherapyItem::KHANDAKER2MOJOTHERAPYITEM_TABLENAME};
}

QString KhandakerMojoMedicationTherapy::ancillaryTableFKToTaskFieldname() const
{
    Q_ASSERT(
        KhandakerMojoTherapyItem::FN_FK_NAME
        == KhandakerMojoMedicationItem::FN_FK_NAME
    );

    return KhandakerMojoMedicationItem::FN_FK_NAME;
}

void KhandakerMojoMedicationTherapy::loadAllAncillary(const int pk)
{
    const OrderBy medication_order_by{
        {KhandakerMojoMedicationItem::FN_SEQNUM, true}};
    ancillaryfunc::loadAncillary<
        KhandakerMojoMedicationItem,
        KhandakerMojoMedicationItemPtr>(
        m_medications,
        m_app,
        m_db,
        KhandakerMojoMedicationItem::FN_FK_NAME,
        medication_order_by,
        pk
    );

    const OrderBy therapy_order_by{
        {KhandakerMojoTherapyItem::FN_SEQNUM, true}};
    ancillaryfunc::
        loadAncillary<KhandakerMojoTherapyItem, KhandakerMojoTherapyItemPtr>(
            m_therapies,
            m_app,
            m_db,
            KhandakerMojoTherapyItem::FN_FK_NAME,
            therapy_order_by,
            pk
        );
}

QVector<DatabaseObjectPtr>
    KhandakerMojoMedicationTherapy::getAncillarySpecimens() const
{
    return QVector<DatabaseObjectPtr>{
        DatabaseObjectPtr(new KhandakerMojoMedicationItem(m_app, m_db)),
        DatabaseObjectPtr(new KhandakerMojoTherapyItem(m_app, m_db)),
    };
}

QVector<DatabaseObjectPtr> KhandakerMojoMedicationTherapy::getAllAncillary(
) const
{
    QVector<DatabaseObjectPtr> ancillaries;
    for (const KhandakerMojoMedicationItemPtr& medication : m_medications) {
        ancillaries.append(medication);
    }
    for (const KhandakerMojoTherapyItemPtr& therapy : m_therapies) {
        ancillaries.append(therapy);
    }
    return ancillaries;
}

// ============================================================================
// Instance info
// ============================================================================

bool KhandakerMojoMedicationTherapy::isComplete() const
{
    // Whilst it's almost certain that anyone completing this task would be on
    // some kind of medication, we have no way of knowing when all medication
    // has been added to the table

    for (const KhandakerMojoMedicationItemPtr& medication : m_medications) {
        if (!medication->isComplete()) {
            return false;
        }
    }

    for (const KhandakerMojoTherapyItemPtr& therapy : m_therapies) {
        if (!therapy->isComplete()) {
            return false;
        }
    }

    return true;
}

QStringList KhandakerMojoMedicationTherapy::summary() const
{
    return QStringList{
        QString("%1 %2")
            .arg(xstring("number_of_medications"))
            .arg(m_medications.size()),
        QString("%1 %2")
            .arg(xstring("number_of_therapies"))
            .arg(m_therapies.size())};
}

QStringList KhandakerMojoMedicationTherapy::detail() const
{
    return completenessInfo() + medicationDetail() + therapyDetail()
        + QStringList("") + summary();
}

QStringList KhandakerMojoMedicationTherapy::medicationDetail() const
{
    QStringList lines;

    if (m_medications.size() == 0) {
        return lines;
    }

    QString html;

    html.append("<table>");
    html.append("<tr>");

    for (const QString& fieldname :
         KhandakerMojoMedicationItem::TABLE_FIELDNAMES) {
        html.append(QString("<th>%1</th>").arg(xstring(fieldname)));
    }

    html.append("</tr>");

    for (const KhandakerMojoMedicationItemPtr& medication : m_medications) {
        html.append("<tr>");

        for (const QString& fieldname :
             KhandakerMojoMedicationItem::TABLE_FIELDNAMES) {
            QString table_cell = "?";

            const QVariant field_value = medication->value(fieldname);

            if (!field_value.isNull()) {
                table_cell = field_value.toString();

                if (fieldname == KhandakerMojoMedicationItem::FN_RESPONSE) {
                    table_cell
                        = getOptionName("response", field_value.toInt());
                }
            }

            html.append(QString("<td>%1</td>").arg(table_cell));
        }

        html.append("</tr>");
    }

    html.append("</table>");

    lines.append(html);

    return lines;
}

QStringList KhandakerMojoMedicationTherapy::therapyDetail() const
{
    QStringList lines;

    if (m_therapies.size() == 0) {
        return lines;
    }

    QString html;

    html.append("<table>");
    html.append("<tr>");

    for (const QString& fieldname :
         KhandakerMojoTherapyItem::TABLE_FIELDNAMES) {
        html.append(QString("<th>%1</th>").arg(xstring(fieldname)));
    }

    html.append("</tr>");

    for (const KhandakerMojoTherapyItemPtr& therapy : m_therapies) {
        html.append("<tr>");

        for (const QString& fieldname :
             KhandakerMojoTherapyItem::TABLE_FIELDNAMES) {
            QString table_cell = "?";

            const QVariant field_value = therapy->value(fieldname);

            if (!field_value.isNull()) {
                table_cell = field_value.toString();

                if (fieldname == KhandakerMojoTherapyItem::FN_RESPONSE) {
                    table_cell
                        = getOptionName("response", field_value.toInt());
                }
            }

            html.append(QString("<td>%1</td>").arg(table_cell));
        }

        html.append("</tr>");
    }

    html.append("</table>");

    lines.append(html);

    return lines;
}

OpenableWidget* KhandakerMojoMedicationTherapy::editor(const bool read_only)
{
    auto medication_page = (new QuPage())->setTitle(tr("Medications"));
    auto therapy_page = (new QuPage())->setTitle(tr("Therapies"));

    rebuildMedicationPage(medication_page);
    rebuildTherapyPage(therapy_page);

    m_questionnaire = new Questionnaire(
        m_app, {QuPagePtr(medication_page), QuPagePtr(therapy_page)}
    );
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}

void KhandakerMojoMedicationTherapy::addMedicationItem(int index)
{
    const QString chemical_name = getCustomMedicationName(index);

    if (chemical_name == nullptr) {
        for (const KhandakerMojoMedicationItemPtr& medication :
             m_medications) {
            if (medication->isEmpty()) {
                uifunc::alert(tr("A row is blank; won’t add another"));

                return;
            }
        }
    }

    KhandakerMojoMedicationItemPtr item = makeMedicationItem();
    item->setSeqnum(m_medications.size() + 1);

    item->setChemicalName(chemical_name);
    item->save();
    m_medications.append(item);

    refreshQuestionnaire();
}

void KhandakerMojoMedicationTherapy::addTherapyItem()
{
    for (const KhandakerMojoTherapyItemPtr& therapy : m_therapies) {
        if (therapy->isEmpty()) {
            uifunc::alert(tr("A row is blank; won’t add another"));

            return;
        }
    }

    KhandakerMojoTherapyItemPtr item = makeTherapyItem();
    item->setSeqnum(m_therapies.size() + 1);
    item->save();
    m_therapies.append(item);
    refreshQuestionnaire();
}

KhandakerMojoMedicationItemPtr
    KhandakerMojoMedicationTherapy::makeMedicationItem() const
{
    return KhandakerMojoMedicationItemPtr(
        new KhandakerMojoMedicationItem(pkvalueInt(), m_app, m_db)
    );
}

KhandakerMojoTherapyItemPtr KhandakerMojoMedicationTherapy::makeTherapyItem(
) const
{
    return KhandakerMojoTherapyItemPtr(
        new KhandakerMojoTherapyItem(pkvalueInt(), m_app, m_db)
    );
}

void KhandakerMojoMedicationTherapy::deleteMedicationItem(const int index)
{
    if (index < 0 || index >= m_medications.size()) {
        return;
    }
    KhandakerMojoMedicationItemPtr item = m_medications.at(index);
    item->deleteFromDatabase();
    m_medications.removeAt(index);
    renumberMedicationItems();
    refreshQuestionnaire();
}

void KhandakerMojoMedicationTherapy::deleteTherapyItem(const int index)
{
    if (index < 0 || index >= m_therapies.size()) {
        return;
    }
    KhandakerMojoTherapyItemPtr item = m_therapies.at(index);
    item->deleteFromDatabase();
    m_therapies.removeAt(index);
    renumberTherapyItems();
    refreshQuestionnaire();
}

void KhandakerMojoMedicationTherapy::renumberMedicationItems()
{
    const int n = m_medications.size();
    for (int i = 0; i < n; ++i) {
        KhandakerMojoMedicationItemPtr item = m_medications.at(i);
        item->setSeqnum(i + 1);
        item->save();
    }
}

void KhandakerMojoMedicationTherapy::renumberTherapyItems()
{
    const int n = m_therapies.size();
    for (int i = 0; i < n; ++i) {
        KhandakerMojoTherapyItemPtr item = m_therapies.at(i);
        item->setSeqnum(i + 1);
        item->save();
    }
}

void KhandakerMojoMedicationTherapy::refreshQuestionnaire()
{
    if (!m_questionnaire) {
        return;
    }
    QuPage* page = m_questionnaire->currentPagePtr();
    const int page_index = m_questionnaire->currentPageIndex();
    if (page_index == 0) {
        rebuildMedicationPage(page);
    } else {
        rebuildTherapyPage(page);
    }

    m_questionnaire->refreshCurrentPage();
}

void KhandakerMojoMedicationTherapy::rebuildMedicationPage(QuPage* page)
{
    QVector<QuElement*> elements;

    elements.append((new QuText(xstring("medication_question")))->setBold());

    elements.append(new QuText(xstring("add_instructions")));
    elements.append(new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE)));
    elements.append(new QuText(xstring("common_medicines")));
    elements.append(getMedicationButtons());
    elements.append(new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE)));
    elements.append(new QuText(xstring("not_listed")));
    elements.append(new QuButton(
        tr("Add a blank row to the table"),
        std::bind(&KhandakerMojoMedicationTherapy::addMedicationItem, this, 0)
    ));

    elements.append(new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE)));
    elements.append(getMedicationGrid());

    page->clearElements();
    page->addElements(elements);
}

void KhandakerMojoMedicationTherapy::rebuildTherapyPage(QuPage* page)
{
    QVector<QuElement*> elements;

    elements.append((new QuText(xstring("therapy_question")))->setBold());
    elements.append(new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE)));
    elements.append(new QuButton(
        tr("Add a row to the table"),
        std::bind(&KhandakerMojoMedicationTherapy::addTherapyItem, this)
    ));

    elements.append(new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE)));
    elements.append(getTherapyGrid());

    page->clearElements();
    page->addElements(elements);
}

QuGridContainer* KhandakerMojoMedicationTherapy::getMedicationGrid()
{
    auto grid = new QuGridContainer();
    grid->setFixedGrid(false);
    grid->setExpandHorizontally(true);

    int row = 0;

    grid->addCell(QuGridCell(new QuText(xstring("chemical_name")), row, 0));
    grid->addCell(QuGridCell(new QuText(xstring("brand_name")), row, 1));
    grid->addCell(QuGridCell(new QuText(xstring("dose")), row, 2));
    grid->addCell(QuGridCell(new QuText(xstring("frequency")), row, 3));
    grid->addCell(QuGridCell(new QuText(xstring("duration_months")), row, 4));
    grid->addCell(QuGridCell(new QuText(xstring("indication")), row, 5));
    grid->addCell(QuGridCell(new QuText(xstring("response")), row, 6));

    row++;

    grid->addCell(QuGridCell(
        (new QuText(xstring("chemical_name_hint")))->setItalic(), row, 0
    ));
    grid->addCell(QuGridCell(
        (new QuText(xstring("brand_name_hint")))->setItalic(), row, 1
    ));
    grid->addCell(
        QuGridCell((new QuText(xstring("dose_hint")))->setItalic(), row, 2)
    );
    grid->addCell(QuGridCell(
        (new QuText(xstring("medication_frequency_hint")))->setItalic(), row, 3
    ));
    grid->addCell(QuGridCell(
        (new QuText(xstring("duration_months_hint")))->setItalic(), row, 4
    ));
    grid->addCell(QuGridCell(
        (new QuText(xstring("medication_indication_hint")))->setItalic(),
        row,
        5
    ));
    grid->addCell(
        QuGridCell((new QuText(xstring("response_hint")))->setItalic(), row, 6)
    );

    row++;

    int item_index = 0;

    for (const KhandakerMojoMedicationItemPtr& medication : m_medications) {
        auto delete_button = new QuButton(
            TextConst::delete_(),
            std::bind(
                &KhandakerMojoMedicationTherapy::deleteMedicationItem,
                this,
                item_index
            )
        );
        auto chemical_name_edit = new QuLineEdit(
            medication->fieldRef(KhandakerMojoMedicationItem::FN_CHEMICAL_NAME)
        );
        auto brand_name_edit = new QuLineEdit(
            medication->fieldRef(KhandakerMojoMedicationItem::FN_BRAND_NAME)
        );
        auto dose_edit = new QuLineEdit(
            medication->fieldRef(KhandakerMojoMedicationItem::FN_DOSE)
        );
        auto frequency_edit = new QuLineEdit(
            medication->fieldRef(KhandakerMojoMedicationItem::FN_FREQUENCY)
        );
        auto duration_edit = new QuLineEditDouble(
            medication->fieldRef(
                KhandakerMojoMedicationItem::FN_DURATION_MONTHS
            ),
            0,
            1800
        );
        auto indication_edit = new QuLineEdit(
            medication->fieldRef(KhandakerMojoMedicationItem::FN_INDICATION)
        );
        auto response_picker = getResponsePicker(
            medication->fieldRef(KhandakerMojoMedicationItem::FN_RESPONSE),
            KhandakerMojoMedicationItem::FN_RESPONSE
        );

        grid->addCell(QuGridCell(chemical_name_edit, row, 0));
        grid->addCell(QuGridCell(brand_name_edit, row, 1));
        grid->addCell(QuGridCell(dose_edit, row, 2));
        grid->addCell(QuGridCell(frequency_edit, row, 3));
        grid->addCell(QuGridCell(duration_edit, row, 4));
        grid->addCell(QuGridCell(indication_edit, row, 5));
        grid->addCell(QuGridCell(response_picker, row, 6));
        grid->addCell(QuGridCell(delete_button, row, 7));

        item_index++;
        row++;
    }

    return grid;
}

QuGridContainer* KhandakerMojoMedicationTherapy::getTherapyGrid()
{
    auto grid = new QuGridContainer();
    grid->setFixedGrid(false);
    grid->setExpandHorizontally(true);

    int row = 0;

    grid->addCell(QuGridCell(new QuText(xstring("therapy")), row, 0));
    grid->addCell(QuGridCell(new QuText(xstring("frequency")), row, 1));
    grid->addCell(QuGridCell(new QuText(xstring("sessions_completed")), row, 2)
    );
    grid->addCell(QuGridCell(new QuText(xstring("sessions_planned")), row, 3));
    grid->addCell(QuGridCell(new QuText(xstring("indication")), row, 4));
    grid->addCell(QuGridCell(new QuText(xstring("response")), row, 5));

    row++;

    grid->addCell(
        QuGridCell((new QuText(xstring("therapy_hint")))->setItalic(), row, 0)
    );
    grid->addCell(QuGridCell(
        (new QuText(xstring("therapy_frequency_hint")))->setItalic(), row, 1
    ));
    grid->addCell(QuGridCell(
        (new QuText(xstring("sessions_completed_hint")))->setItalic(), row, 2
    ));
    grid->addCell(QuGridCell(
        (new QuText(xstring("sessions_planned_hint")))->setItalic(), row, 3
    ));
    grid->addCell(QuGridCell(
        (new QuText(xstring("therapy_indication_hint")))->setItalic(), row, 4
    ));
    grid->addCell(
        QuGridCell((new QuText(xstring("response_hint")))->setItalic(), row, 5)
    );

    row++;

    int item_index = 0;

    for (const KhandakerMojoTherapyItemPtr& therapy : m_therapies) {
        auto delete_button = new QuButton(
            TextConst::delete_(),
            std::bind(
                &KhandakerMojoMedicationTherapy::deleteTherapyItem,
                this,
                item_index
            )
        );
        auto therapy_edit = new QuLineEdit(
            therapy->fieldRef(KhandakerMojoTherapyItem::FN_THERAPY)
        );
        auto frequency_edit = new QuLineEdit(
            therapy->fieldRef(KhandakerMojoTherapyItem::FN_FREQUENCY)
        );
        auto sessions_completed_edit = new QuLineEditInteger(
            therapy->fieldRef(KhandakerMojoTherapyItem::FN_SESSIONS_COMPLETED),
            0,
            500
        );
        auto sessions_planned_edit = new QuLineEditInteger(
            therapy->fieldRef(KhandakerMojoTherapyItem::FN_SESSIONS_PLANNED),
            0,
            500
        );
        auto indication_edit = new QuLineEdit(
            therapy->fieldRef(KhandakerMojoTherapyItem::FN_INDICATION)
        );
        auto response_picker = getResponsePicker(
            therapy->fieldRef(KhandakerMojoTherapyItem::FN_RESPONSE),
            KhandakerMojoTherapyItem::FN_RESPONSE
        );

        grid->addCell(QuGridCell(therapy_edit, row, 0));
        grid->addCell(QuGridCell(frequency_edit, row, 1));
        grid->addCell(QuGridCell(sessions_completed_edit, row, 2));
        grid->addCell(QuGridCell(sessions_planned_edit, row, 3));
        grid->addCell(QuGridCell(indication_edit, row, 4));
        grid->addCell(QuGridCell(response_picker, row, 5));
        grid->addCell(QuGridCell(delete_button, row, 6));

        item_index++;
        row++;
    }

    return grid;
}

QuPickerPopup* KhandakerMojoMedicationTherapy::getResponsePicker(
    FieldRefPtr fieldref, const QString fieldname
)
{
    NameValueOptions response_options;

    for (int i = 1; i <= 4; i++) {
        const QString name = getOptionName(fieldname, i);
        response_options.append(NameValuePair(name, i));
    }

    return new QuPickerPopup(fieldref, response_options);
}

QuFlowContainer* KhandakerMojoMedicationTherapy::getMedicationButtons()
{
    auto container = new QuFlowContainer();

    int i = 1;

    while (true) {
        const QString name = getCustomMedicationName(i);

        if (name == "__no_more_medications") {
            break;
        }

        container->addElement(new QuButton(
            name,
            std::bind(
                &KhandakerMojoMedicationTherapy::addMedicationItem, this, i
            )
        ));

        i++;
    }

    return container;
}

QString KhandakerMojoMedicationTherapy::getCustomMedicationName(const int index
) const
{
    if (index == 0) {
        return nullptr;
    }

    return getOptionName("custom_medication", index, "__no_more_medications");
}

QString KhandakerMojoMedicationTherapy::getOptionName(
    const QString& prefix, const int index
) const
{
    return getOptionName(prefix, index, "");
}

QString KhandakerMojoMedicationTherapy::getOptionName(
    const QString& prefix, const int index, const QString default_str
) const
{
    return xstring(QString("%1_%2").arg(prefix).arg(index), default_str);
}
