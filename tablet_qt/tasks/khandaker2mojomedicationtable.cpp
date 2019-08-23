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
#include "questionnairelib/qupickerinline.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
#include "taskxtra/khandaker2mojomedicationitem.h"

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
         false, false, false)  // ... anon, clin, resp
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
        Khandaker2MojoMedicationItem::KHANDAKER2MOJOMEDICATIONITEM_TABLENAME
    };
}


QString Khandaker2MojoMedicationTable::ancillaryTableFKToTaskFieldname() const
{
    return Khandaker2MojoMedicationItem::FN_FK_NAME;
}

void Khandaker2MojoMedicationTable::loadAllAncillary(const int pk)
{
    const OrderBy order_by{{Khandaker2MojoMedicationItem::FN_SEQNUM, true}};
    ancillaryfunc::loadAncillary<Khandaker2MojoMedicationItem, Khandaker2MojoMedicationItemPtr>(
                m_medication_table, m_app, m_db,
                Khandaker2MojoMedicationItem::FN_FK_NAME, order_by, pk);
}


QVector<DatabaseObjectPtr> Khandaker2MojoMedicationTable::getAncillarySpecimens() const
{
    return QVector<DatabaseObjectPtr>{
        DatabaseObjectPtr(new Khandaker2MojoMedicationItem(m_app, m_db)),
    };
}


QVector<DatabaseObjectPtr> Khandaker2MojoMedicationTable::getAllAncillary() const
{
    QVector<DatabaseObjectPtr> ancillaries;
    for (const Khandaker2MojoMedicationItemPtr& medication : m_medication_table) {
        ancillaries.append(medication);
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
    return QStringList{TextConst::noSummarySeeFacsimile()};
}


QStringList Khandaker2MojoMedicationTable::detail() const
{
    QStringList lines;

    // TODO

    return completenessInfo() + lines;
}


OpenableWidget* Khandaker2MojoMedicationTable::editor(const bool read_only)
{
    auto page = (new QuPage())->setTitle(longname());
    rebuildPage(page);

    m_questionnaire = new Questionnaire(m_app, {QuPagePtr(page)});
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    return m_questionnaire;
}


void Khandaker2MojoMedicationTable::addItem()
{
    Khandaker2MojoMedicationItemPtr item = makeItem();
    item->setSeqnum(m_medication_table.size() + 1);
    item->save();
    m_medication_table.append(item);
    refreshQuestionnaire();
}


Khandaker2MojoMedicationItemPtr Khandaker2MojoMedicationTable::makeItem() const
{
    return Khandaker2MojoMedicationItemPtr(
        new Khandaker2MojoMedicationItem(pkvalueInt(), m_app, m_db)
    );
}


void Khandaker2MojoMedicationTable::deleteItem(const int index)
{
    if (index < 0 || index >= m_medication_table.size()) {
        return;
    }
    Khandaker2MojoMedicationItemPtr item = m_medication_table.at(index);
    item->deleteFromDatabase();
    m_medication_table.removeAt(index);
    renumberItems();
    refreshQuestionnaire();
}


void Khandaker2MojoMedicationTable::renumberItems()
{
    const int n = m_medication_table.size();
    for (int i = 0; i < n; ++i) {
        Khandaker2MojoMedicationItemPtr item = m_medication_table.at(i);
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

    elements.append(new QuText(xstring("instructions")));

    int i = 0;

    auto grid = new QuGridContainer();
    grid->setFixedGrid(false);
    grid->setExpandHorizontally(true);

    grid->addCell(QuGridCell(new QuText(xstring("medication_name")), 0, 0));
    grid->addCell(QuGridCell(new QuText(xstring("chemical_name")), 0, 1));
    grid->addCell(QuGridCell(new QuText(xstring("dosage")), 0, 2));
    grid->addCell(QuGridCell(new QuText(xstring("duration")), 0, 3));
    grid->addCell(QuGridCell(new QuText(xstring("indication")), 0, 4));
    grid->addCell(QuGridCell(new QuText(xstring("response")), 0, 5));

    for (const Khandaker2MojoMedicationItemPtr& medication : m_medication_table) {
        auto delete_button = new QuButton(
            TextConst::delete_(),
            std::bind(&Khandaker2MojoMedicationTable::deleteItem, this, i)
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

        NameValueOptions response_options;

        for (int i = 1; i <= 4; i++) {
            const QString name = getOptionName(
                Khandaker2MojoMedicationItem::FN_RESPONSE, i
            );
            response_options.append(NameValuePair(name, i));
        }

        auto response_picker = new QuPickerInline(
            medication->fieldRef(
                Khandaker2MojoMedicationItem::FN_RESPONSE),
            response_options
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

    elements.append(grid);

    elements.append(new QuButton(
        TextConst::add(),
        std::bind(&Khandaker2MojoMedicationTable::addItem, this)
    ));

    page->clearElements();
    page->addElements(elements);
}


QString Khandaker2MojoMedicationTable::getOptionName(
    const QString &fieldname, const int index) const
{
    return xstring(QString("%1_%2").arg(fieldname).arg(index));
}
