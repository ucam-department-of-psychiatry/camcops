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

#include "khandaker2mojomedicationtable.h"
#include "common/cssconst.h"
#include "common/textconst.h"
#include "db/ancillaryfunc.h"
#include "db/fieldref.h"
#include "lib/convert.h"
#include "lib/uifunc.h"
#include "lib/version.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/qubutton.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/qupickerpopup.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
#include "taskxtra/khandaker2mojomedicationitem.h"
#include "taskxtra/khandaker2mojotherapyitem.h"

const QString Khandaker2MojoMedicationTable::KHANDAKER2MOJOMEDICATIONTABLE_TABLENAME(
    "khandaker_2_mojomedicationtable");

const QString Q_XML_PREFIX = "q_";



void initializeKhandaker2MojoMedicationTable(TaskFactory& factory)
{
    static TaskRegistrar<Khandaker2MojoMedicationTable> registered(factory);
}


Khandaker2MojoMedicationTable::Khandaker2MojoMedicationTable(
        CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, KHANDAKER2MOJOMEDICATIONTABLE_TABLENAME,
         false, false, false),  // ... anon, clin, resp
    m_custom_medication(0),
    m_fr_custom_medication(nullptr)
{
    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Khandaker2MojoMedicationTable::shortname() const
{
    return "Khandaker_2_Mojomedicationtable";
}


QString Khandaker2MojoMedicationTable::longname() const
{
    return tr("Khandaker GM — 2 MOJO Study — Medications and Treatment");
}


QString Khandaker2MojoMedicationTable::description() const
{
    return tr("Medications and Treatment Table for MOJO Study.");
}


// ============================================================================
// Ancillary management
// ============================================================================
QStringList Khandaker2MojoMedicationTable::ancillaryTables() const
{
    return QStringList{
        Khandaker2MojoMedicationItem::KHANDAKER2MOJOMEDICATIONITEM_TABLENAME,
        Khandaker2MojoTherapyItem::KHANDAKER2MOJOTHERAPYITEM_TABLENAME
    };
}


QString Khandaker2MojoMedicationTable::ancillaryTableFKToTaskFieldname() const
{
    Q_ASSERT(Khandaker2MojoTherapyItem::FN_FK_NAME == Khandaker2MojoMedicationItem::FN_FK_NAME);

    return Khandaker2MojoMedicationItem::FN_FK_NAME;
}

void Khandaker2MojoMedicationTable::loadAllAncillary(const int pk)
{
    const OrderBy medication_order_by{{Khandaker2MojoMedicationItem::FN_SEQNUM, true}};
    ancillaryfunc::loadAncillary<Khandaker2MojoMedicationItem,
                                 Khandaker2MojoMedicationItemPtr>(
                m_medication_table, m_app, m_db,
                Khandaker2MojoMedicationItem::FN_FK_NAME, medication_order_by, pk);

    const OrderBy therapy_order_by{{Khandaker2MojoTherapyItem::FN_SEQNUM, true}};
    ancillaryfunc::loadAncillary<Khandaker2MojoTherapyItem,
                                 Khandaker2MojoTherapyItemPtr>(
                m_therapy_table, m_app, m_db,
                Khandaker2MojoTherapyItem::FN_FK_NAME, therapy_order_by, pk);
}


QVector<DatabaseObjectPtr> Khandaker2MojoMedicationTable::getAncillarySpecimens() const
{
    return QVector<DatabaseObjectPtr>{
        DatabaseObjectPtr(new Khandaker2MojoMedicationItem(m_app, m_db)),
        DatabaseObjectPtr(new Khandaker2MojoTherapyItem(m_app, m_db)),
    };
}


QVector<DatabaseObjectPtr> Khandaker2MojoMedicationTable::getAllAncillary() const
{
    QVector<DatabaseObjectPtr> ancillaries;
    for (const Khandaker2MojoMedicationItemPtr& medication : m_medication_table) {
        ancillaries.append(medication);
    }
    for (const Khandaker2MojoTherapyItemPtr& therapy : m_therapy_table) {
        ancillaries.append(therapy);
    }
    return ancillaries;
}



// ============================================================================
// Instance info
// ============================================================================

bool Khandaker2MojoMedicationTable::isComplete() const
{
    // Whilst it's almost certain that anyone completing this task would be on
    // some kind of medication, we have no way of knowing when all medication
    // has been added to the table

    return true;
}


QStringList Khandaker2MojoMedicationTable::summary() const
{
    return QStringList{
        QString("%1 %2").arg(xstring("number_of_medications")).arg(
            m_medication_table.size()),
        QString("%1 %2").arg(xstring("number_of_therapies")).arg(
                m_therapy_table.size())
    };
}


QStringList Khandaker2MojoMedicationTable::detail() const
{
    return completenessInfo() + medicationDetail() + therapyDetail() + summary();
}


QStringList Khandaker2MojoMedicationTable::medicationDetail() const
{
    QStringList lines;

    if (m_medication_table.size() == 0) {
        return lines;
    }

    const QVector<QString> columns{
        Khandaker2MojoMedicationItem::FN_MEDICATION_NAME,
        Khandaker2MojoMedicationItem::FN_CHEMICAL_NAME,
        Khandaker2MojoMedicationItem::FN_DOSAGE,
        Khandaker2MojoMedicationItem::FN_DURATION,
        Khandaker2MojoMedicationItem::FN_INDICATION,
        Khandaker2MojoMedicationItem::FN_RESPONSE,
    };

    lines.append("<table>");
    lines.append("<tr>");

    for (const QString column : columns) {
        lines.append(QString("<th>%1</th>").arg(xstring(column)));
    }

    lines.append("</tr>");

    for (const Khandaker2MojoMedicationItemPtr& medication : m_medication_table) {
        lines.append("<tr>");

        for (const QString column : columns) {
            QString table_cell = "?";

            const QVariant field_value = medication->value(column);

            if (!field_value.isNull()) {
                table_cell = field_value.toString();

                if (column == Khandaker2MojoMedicationItem::FN_RESPONSE) {
                    table_cell = getOptionName("response", field_value.toInt());
                }
            }

            lines.append(QString("<td>%1</td>").arg(table_cell));
        }

        lines.append("</tr>");
    }

    lines.append("</table>");

    return lines;
}


QStringList Khandaker2MojoMedicationTable::therapyDetail() const
{
    QStringList lines;

    if (m_therapy_table.size() == 0) {
        return lines;
    }

    const QVector<QString> columns{
        Khandaker2MojoTherapyItem::FN_THERAPY,
        Khandaker2MojoTherapyItem::FN_FREQUENCY,
        Khandaker2MojoTherapyItem::FN_DURATION,
        Khandaker2MojoTherapyItem::FN_INDICATION,
        Khandaker2MojoTherapyItem::FN_RESPONSE,
    };

    lines.append("<table>");
    lines.append("<tr>");

    for (const QString column : columns) {
        lines.append(QString("<th>%1</th>").arg(xstring(column)));
    }

    lines.append("</tr>");

    for (const Khandaker2MojoTherapyItemPtr& therapy : m_therapy_table) {
        lines.append("<tr>");

        for (const QString column : columns) {
            QString table_cell = "?";

            const QVariant field_value = therapy->value(column);

            if (!field_value.isNull()) {
                table_cell = field_value.toString();

                if (column == Khandaker2MojoTherapyItem::FN_RESPONSE) {
                    table_cell = getOptionName("response", field_value.toInt());
                }
            }

            lines.append(QString("<td>%1</td>").arg(table_cell));
        }

        lines.append("</tr>");
    }

    lines.append("</table>");

    return lines;
}


OpenableWidget* Khandaker2MojoMedicationTable::editor(const bool read_only)
{
    auto page = (new QuPage())->setTitle(longname());

    // Display empty rows as examples if there are no rows. The user
    // can always delete them if they want to leave the tables empty
    if (m_medication_table.size() == 0) {
        addMedicationItem();
    }

    if (m_therapy_table.size() == 0) {
        addTherapyItem();
    }

    rebuildPage(page);

    m_questionnaire = new Questionnaire(m_app, {QuPagePtr(page)});
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}


void Khandaker2MojoMedicationTable::addMedicationItem()
{
    Khandaker2MojoMedicationItemPtr item = makeMedicationItem();
    item->setSeqnum(m_medication_table.size() + 1);

    item->setChemicalName(getCustomMedicationName());
    item->save();
    m_medication_table.append(item);

    refreshQuestionnaire();
}


void Khandaker2MojoMedicationTable::addTherapyItem()
{
    Khandaker2MojoTherapyItemPtr item = makeTherapyItem();
    item->setSeqnum(m_therapy_table.size() + 1);
    item->save();
    m_therapy_table.append(item);
    refreshQuestionnaire();
}


Khandaker2MojoMedicationItemPtr Khandaker2MojoMedicationTable::makeMedicationItem() const
{
    return Khandaker2MojoMedicationItemPtr(
        new Khandaker2MojoMedicationItem(pkvalueInt(), m_app, m_db)
    );
}


Khandaker2MojoTherapyItemPtr Khandaker2MojoMedicationTable::makeTherapyItem() const
{
    return Khandaker2MojoTherapyItemPtr(
        new Khandaker2MojoTherapyItem(pkvalueInt(), m_app, m_db)
    );
}


void Khandaker2MojoMedicationTable::deleteMedicationItem(const int index)
{
    if (index < 0 || index >= m_medication_table.size()) {
        return;
    }
    Khandaker2MojoMedicationItemPtr item = m_medication_table.at(index);
    item->deleteFromDatabase();
    m_medication_table.removeAt(index);
    renumberMedicationItems();
    refreshQuestionnaire();
}


void Khandaker2MojoMedicationTable::deleteTherapyItem(const int index)
{
    if (index < 0 || index >= m_therapy_table.size()) {
        return;
    }
    Khandaker2MojoTherapyItemPtr item = m_therapy_table.at(index);
    item->deleteFromDatabase();
    m_therapy_table.removeAt(index);
    renumberTherapyItems();
    refreshQuestionnaire();
}


void Khandaker2MojoMedicationTable::renumberMedicationItems()
{
    const int n = m_medication_table.size();
    for (int i = 0; i < n; ++i) {
        Khandaker2MojoMedicationItemPtr item = m_medication_table.at(i);
        item->setSeqnum(i + 1);
        item->save();
    }
}


void Khandaker2MojoMedicationTable::renumberTherapyItems()
{
    const int n = m_therapy_table.size();
    for (int i = 0; i < n; ++i) {
        Khandaker2MojoTherapyItemPtr item = m_therapy_table.at(i);
        item->setSeqnum(i + 1);
        item->save();
    }
}


void Khandaker2MojoMedicationTable::refreshQuestionnaire()
{
    if (!m_questionnaire) {
        return;
    }
    QuPage* page = m_questionnaire->currentPagePtr();
    rebuildPage(page);
    m_questionnaire->refreshCurrentPage();
}


void Khandaker2MojoMedicationTable::rebuildPage(QuPage* page)
{
    QVector<QuElement*> elements;

    elements.append((new QuText(xstring("medication_question")))->setBold());

    elements.append(new QuText(xstring("add_instructions")));
    elements.append(getMedicationPicker());

    elements.append(new QuButton(
        TextConst::add(),
        std::bind(&Khandaker2MojoMedicationTable::addMedicationItem, this)
    ));

    elements.append(getMedicationGrid());

    elements.append(new QuSpacer(QSize(uiconst::BIGSPACE, uiconst::BIGSPACE)));
    elements.append((new QuText(xstring("therapy_question")))->setBold());
    elements.append(new QuButton(
        TextConst::add(),
        std::bind(&Khandaker2MojoMedicationTable::addTherapyItem, this)
    ));

    elements.append(getTherapyGrid());

    page->clearElements();
    page->addElements(elements);
}

QuGridContainer* Khandaker2MojoMedicationTable::getMedicationGrid() {
    auto grid = new QuGridContainer();
    grid->setFixedGrid(false);
    grid->setExpandHorizontally(true);

    grid->addCell(QuGridCell(new QuText(xstring("medication_name")), 0, 0));
    grid->addCell(QuGridCell(new QuText(xstring("chemical_name")), 0, 1));
    grid->addCell(QuGridCell(new QuText(xstring("dosage")), 0, 2));
    grid->addCell(QuGridCell(new QuText(xstring("duration")), 0, 3));
    grid->addCell(QuGridCell(new QuText(xstring("indication")), 0, 4));
    grid->addCell(QuGridCell(new QuText(xstring("response")), 0, 5));

    int i = 0;

    for (const Khandaker2MojoMedicationItemPtr& medication : m_medication_table) {
        auto delete_button = new QuButton(
            TextConst::delete_(),
            std::bind(&Khandaker2MojoMedicationTable::deleteMedicationItem,
                      this, i)
        );

        auto medication_name_edit = new QuLineEdit(
            medication->fieldRef(
                Khandaker2MojoMedicationItem::FN_MEDICATION_NAME)
        );

        auto chemical_name_edit = new QuLineEdit(
            medication->fieldRef(
                Khandaker2MojoMedicationItem::FN_CHEMICAL_NAME)
        );

        auto dosage_edit = new QuLineEdit(
            medication->fieldRef(
                Khandaker2MojoMedicationItem::FN_DOSAGE)
        );

        auto duration_edit = new QuLineEditInteger(
            medication->fieldRef(
                Khandaker2MojoMedicationItem::FN_DURATION)
        );

        auto indication_edit = new QuLineEdit(
            medication->fieldRef(
                Khandaker2MojoMedicationItem::FN_INDICATION)
        );

        auto response_picker = getResponsePicker(
            medication->fieldRef(Khandaker2MojoMedicationItem::FN_RESPONSE),
            Khandaker2MojoMedicationItem::FN_RESPONSE
        );

        int row = i + 1;

        grid->addCell(QuGridCell(medication_name_edit, row, 0));
        grid->addCell(QuGridCell(chemical_name_edit, row, 1));
        grid->addCell(QuGridCell(dosage_edit, row, 2));
        grid->addCell(QuGridCell(duration_edit, row, 3));
        grid->addCell(QuGridCell(indication_edit, row, 4));
        grid->addCell(QuGridCell(response_picker, row, 5));
        grid->addCell(QuGridCell(delete_button, row, 6));

        i++;
    }

    return grid;
}


QuGridContainer* Khandaker2MojoMedicationTable::getTherapyGrid() {
    auto grid = new QuGridContainer();
    grid->setFixedGrid(false);
    grid->setExpandHorizontally(true);

    grid->addCell(QuGridCell(new QuText(xstring("therapy")), 0, 0));
    grid->addCell(QuGridCell(new QuText(xstring("frequency")), 0, 1));
    grid->addCell(QuGridCell(new QuText(xstring("duration")), 0, 2));
    grid->addCell(QuGridCell(new QuText(xstring("indication")), 0, 3));
    grid->addCell(QuGridCell(new QuText(xstring("response")), 0, 4));

    int i = 0;

    for (const Khandaker2MojoTherapyItemPtr& therapy : m_therapy_table) {
        auto delete_button = new QuButton(
            TextConst::delete_(),
            std::bind(&Khandaker2MojoMedicationTable::deleteTherapyItem, this, i)
        );

        auto therapy_edit = new QuLineEdit(
            therapy->fieldRef(
                Khandaker2MojoTherapyItem::FN_THERAPY)
        );

        auto frequency_edit = new QuLineEditInteger(
            therapy->fieldRef(
                Khandaker2MojoTherapyItem::FN_FREQUENCY)
        );

        auto duration_edit = new QuLineEditInteger(
            therapy->fieldRef(
                Khandaker2MojoTherapyItem::FN_DURATION)
        );

        auto indication_edit = new QuLineEdit(
            therapy->fieldRef(
                Khandaker2MojoTherapyItem::FN_INDICATION)
        );

        auto response_picker = getResponsePicker(
            therapy->fieldRef(Khandaker2MojoTherapyItem::FN_RESPONSE),
            Khandaker2MojoTherapyItem::FN_RESPONSE
        );

        int row = i + 1;

        grid->addCell(QuGridCell(therapy_edit, row, 0));
        grid->addCell(QuGridCell(frequency_edit, row, 1));
        grid->addCell(QuGridCell(duration_edit, row, 2));
        grid->addCell(QuGridCell(indication_edit, row, 3));
        grid->addCell(QuGridCell(response_picker, row, 4));
        grid->addCell(QuGridCell(delete_button, row, 5));

        i++;
    }

    return grid;
}


QuPickerPopup* Khandaker2MojoMedicationTable::getResponsePicker(
    FieldRefPtr fieldref, const QString fieldname) {
    NameValueOptions response_options;

    for (int i = 1; i <= 4; i++) {
        const QString name = getOptionName(fieldname, i);
        response_options.append(NameValuePair(name, i));
    }

    return new QuPickerPopup(fieldref, response_options);
}


QuPickerPopup* Khandaker2MojoMedicationTable::getMedicationPicker() {
    NameValueOptions medication_options;

    int i = 0;

    while (true) {
        const QString name = getCustomMedicationName(i);

        if (name == "__no_more_medications") {
            break;
        }

        medication_options.append(NameValuePair(name, i));

        i++;
    }

    FieldRef::GetterFunction getter = std::bind(
        &Khandaker2MojoMedicationTable::getCustomMedication, this
    );
    FieldRef::SetterFunction setter= std::bind(
        &Khandaker2MojoMedicationTable::setCustomMedication, this,
        std::placeholders::_1);

    m_fr_custom_medication = FieldRefPtr(new FieldRef(getter, setter, false));
    setCustomMedication(0);

    return new QuPickerPopup(
        m_fr_custom_medication,
        medication_options
    );
}


bool Khandaker2MojoMedicationTable::setCustomMedication(const QVariant& value)
{
    const bool changed = value != m_custom_medication;

    if (changed) {
        m_custom_medication = value;
    }

    return changed;
}


QVariant Khandaker2MojoMedicationTable::getCustomMedication() const
{
    return m_custom_medication;
}


QString Khandaker2MojoMedicationTable::getCustomMedicationName() const
{
    if (!isCustomMedicationSet()) {
        return nullptr;
    }

    return getCustomMedicationName(m_custom_medication.toInt());
}


bool Khandaker2MojoMedicationTable::isCustomMedicationSet() const
{
    Q_ASSERT(!m_custom_medication.isNull());

    return m_custom_medication != 0;
}


QString Khandaker2MojoMedicationTable::getCustomMedicationName(
    const int index) const
{
    return getOptionName("custom_medication",
                         index,
                         "__no_more_medications");
}


QString Khandaker2MojoMedicationTable::getOptionName(
    const QString &prefix, const int index) const
{
    return getOptionName(prefix, index, "");
}


QString Khandaker2MojoMedicationTable::getOptionName(
    const QString &prefix, const int index, const QString default_str) const
{
    return xstring(QString("%1_%2").arg(prefix).arg(index), default_str);
}
