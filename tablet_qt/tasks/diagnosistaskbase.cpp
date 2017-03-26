/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

#include "diagnosistaskbase.h"
#include <algorithm>
#include "diagnosisitembase.h"
#include "common/textconst.h"
#include "diagnosis/diagnosticcodeset.h"
#include "lib/uifunc.h"
#include "questionnairelib/qubutton.h"
#include "questionnairelib/qudiagnosticcode.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/quhorizontalcontainer.h"
#include "questionnairelib/quhorizontalline.h"
#include "questionnairelib/qutext.h"


DiagnosisTaskBase::DiagnosisTaskBase(CamcopsApp& app, const QSqlDatabase& db,
                                     const QString& tablename, int load_pk) :
    Task(app, db, tablename, false, true, false),  // ... anon, clin, resp
    m_questionnaire(nullptr),
    m_codeset(nullptr)
{
    load(load_pk);
}


// ============================================================================
// Instance info
// ============================================================================

bool DiagnosisTaskBase::isComplete() const
{
    return m_items.size() > 0;
}


QStringList DiagnosisTaskBase::summary() const
{
    QStringList lines;
    for (auto item : m_items) {
        lines.append(QString("%1: <b>%2 – %3</b>.").arg(
                         QString::number(item->seqnum()),
                         item->code(),
                         item->description()));
    }
    return lines;
}


QStringList DiagnosisTaskBase::detail() const
{
    return completenessInfo() + summary();
}


OpenableWidget* DiagnosisTaskBase::editor(bool read_only)
{
    m_codeset = makeCodeset();

    m_core_elements = QList<QuElementPtr>{
        getClinicianQuestionnaireBlockElementPtr(),
        QuElementPtr(new QuButton(
            textconst::ADD,
            std::bind(&DiagnosisTaskBase::addItem, this)
        )),
    };

    QuPage* page = (new QuPage())
                   ->setTitle(longname())
                   ->setType(QuPage::PageType::Clinician);
    rebuildPage(page);

    m_questionnaire = new Questionnaire(m_app, {QuPagePtr(page)});
    m_questionnaire->setType(QuPage::PageType::Clinician);
    m_questionnaire->setReadOnly(read_only);
    return m_questionnaire;
}


// ============================================================================
// Ancillary management
// ============================================================================

QList<DatabaseObjectPtr> DiagnosisTaskBase::getAllAncillary() const
{
    QList<DatabaseObjectPtr> ancillaries;
    for (auto item : m_items) {
        ancillaries.append(item);
    }
    return ancillaries;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

void DiagnosisTaskBase::addItem()
{
    bool one_is_empty = false;
    for (DiagnosisItemBasePtr item : m_items) {
        if (item->valueIsNullOrEmpty(DiagnosisItemBase::CODE)) {
            one_is_empty = true;
            break;
        }
    }
    if (one_is_empty) {
        uifunc::alert(tr("A diagnosis already needs setting; won’t add "
                         "another"));
        return;
    }
    DiagnosisItemBasePtr item = makeItem();
    item->setForeignKeyToOwner(pkvalueInt());
    item->setSeqnum(m_items.size());
    item->save();
    m_items.append(item);
    refreshQuestionnaire();
}


void DiagnosisTaskBase::deleteItem(int index)
{
    if (index < 0 || index >= m_items.size()) {
        return;
    }
    DiagnosisItemBasePtr item = m_items.at(index);
    item->deleteFromDatabase();
    m_items.removeAt(index);
    renumberItems();
    refreshQuestionnaire();
}


void DiagnosisTaskBase::moveUp(int index)
{
    if (index < 1 || index >= m_items.size()) {
        return;
    }
    std::swap(m_items[index - 1], m_items[index]);
    renumberItems();
    refreshQuestionnaire();
}


void DiagnosisTaskBase::moveDown(int index)
{
    if (index < 0 || index >= m_items.size() - 1) {
        return;
    }
    std::swap(m_items[index], m_items[index + 1]);
    renumberItems();
    refreshQuestionnaire();
}


QVariant DiagnosisTaskBase::getCode(int index) const
{
    if (index < 0 || index >= m_items.size()) {
        return QVariant();
    }
    DiagnosisItemBasePtr item = m_items.at(index);
    return item->value(DiagnosisItemBase::CODE);
}


bool DiagnosisTaskBase::setCode(int index, const QVariant& value)
{
    if (index < 0 || index >= m_items.size()) {
        return false;
    }
    DiagnosisItemBasePtr item = m_items.at(index);
    bool changed = item->setValue(DiagnosisItemBase::CODE, value);
    if (changed) {
        item->save();
    }
    return changed;
}


QVariant DiagnosisTaskBase::getDescription(int index) const
{
    if (index < 0 || index >= m_items.size()) {
        return QVariant();
    }
    DiagnosisItemBasePtr item = m_items.at(index);
    return item->value(DiagnosisItemBase::DESCRIPTION);
}


bool DiagnosisTaskBase::setDescription(int index, const QVariant& value)
{
    if (index < 0 || index >= m_items.size()) {
        return false;
    }
    DiagnosisItemBasePtr item = m_items.at(index);
    bool changed = item->setValue(DiagnosisItemBase::DESCRIPTION, value);
    if (changed) {
        item->save();
    }
    return changed;
}


void DiagnosisTaskBase::refreshQuestionnaire()
{
    if (!m_questionnaire) {
        return;
    }
    QuPage* page = m_questionnaire->currentPagePtr();
    rebuildPage(page);
    m_questionnaire->refreshCurrentPage();
}


void DiagnosisTaskBase::rebuildPage(QuPage* page)
{
    QList<QuElement*> elements;
    int n = m_items.size();
    for (int i = 0; i < n; ++i) {
        bool first = i == 0;
        bool last = i == n - 1;
        elements.append(new QuHorizontalLine());
        elements.append((new QuText(textconst::DIAGNOSIS + " " +
                                    QString::number(i + 1)))->setBold());
        FieldRef::GetterFunction get_code = std::bind(
                    &DiagnosisTaskBase::getCode, this, i);
        FieldRef::GetterFunction get_desc = std::bind(
                    &DiagnosisTaskBase::getDescription, this, i);
        FieldRef::SetterFunction set_code = std::bind(
                    &DiagnosisTaskBase::setCode, this, i, std::placeholders::_1);
        FieldRef::SetterFunction set_desc = std::bind(
                    &DiagnosisTaskBase::setDescription, this, i, std::placeholders::_1);
        FieldRefPtr fr_code = FieldRefPtr(new FieldRef(get_code, set_code, true));
        FieldRefPtr fr_desc = FieldRefPtr(new FieldRef(get_desc, set_desc, true));
        elements.append(new QuHorizontalContainer({
            new QuButton(
                textconst::DELETE,
                std::bind(&DiagnosisTaskBase::deleteItem, this, i)
            ),
            (new QuButton(
                textconst::MOVE_UP,
                std::bind(&DiagnosisTaskBase::moveUp, this, i)
            ))->setActive(!first),
            (new QuButton(
                textconst::MOVE_DOWN,
                std::bind(&DiagnosisTaskBase::moveDown, this, i)
            ))->setActive(!last),
            new QuDiagnosticCode(m_codeset, fr_code, fr_desc),
        }));
    }

    page->clearElements();
    page->addElements(m_core_elements);
    page->addElements(elements);
}


void DiagnosisTaskBase::renumberItems()
{
    // Fine to reset the number to something that doesn't change; the save()
    // call will do nothing.
    int n = m_items.size();
    for (int i = 0; i < n; ++i) {
        DiagnosisItemBasePtr item = m_items.at(i);
        item->setSeqnum(i + 1);
        item->save();
    }
}
