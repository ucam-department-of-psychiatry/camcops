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

#pragma once
#include <QPointer>
#include <QString>

#include "tasklib/task.h"

class CamcopsApp;
class OpenableWidget;
class Questionnaire;
class QuFlowContainer;
class QuGridContainer;
class QuPickerPopup;
class TaskFactory;

void initializeKhandakerMojoMedicationTherapy(TaskFactory& factory);

class KhandakerMojoMedicationTherapy : public Task
{
    Q_OBJECT

public:
    KhandakerMojoMedicationTherapy(
        CamcopsApp& app,
        DatabaseManager& db,
        int load_pk = dbconst::NONEXISTENT_PK
    );
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString description() const override;
    virtual QString infoFilenameStem() const override;
    // ------------------------------------------------------------------------
    // Ancillary management
    // ------------------------------------------------------------------------
    virtual QStringList ancillaryTables() const override;
    virtual QString ancillaryTableFKToTaskFieldname() const override;
    virtual void loadAllAncillary(int pk) override;
    virtual QVector<DatabaseObjectPtr> getAncillarySpecimens() const override;
    virtual QVector<DatabaseObjectPtr> getAllAncillary() const override;
    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QStringList summary() const override;
    virtual QStringList detail() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Task-specific
    // ------------------------------------------------------------------------

private:
    QuPickerPopup*
        getResponsePicker(FieldRefPtr fieldref, const QString fieldname);
    QuFlowContainer* getMedicationButtons();
    bool isCustomMedicationSet() const;
    QString getCustomMedicationName() const;
    QString getCustomMedicationName(const int index) const;
    QString getOptionName(const QString& fieldname, const int index) const;
    QString getOptionName(
        const QString& fieldname, const int index, const QString default_str
    ) const;
    void addMedicationItem(int index);
    void addTherapyItem();
    void deleteMedicationItem(int index);
    void deleteTherapyItem(int index);
    QuGridContainer* getMedicationGrid();
    QuGridContainer* getTherapyGrid();
    KhandakerMojoMedicationItemPtr makeMedicationItem() const;
    KhandakerMojoTherapyItemPtr makeTherapyItem() const;
    void refreshQuestionnaire();
    void rebuildMedicationPage(QuPage* page);
    void rebuildTherapyPage(QuPage* page);
    void renumberMedicationItems();
    void renumberTherapyItems();
    QStringList medicationDetail() const;
    QStringList therapyDetail() const;

    // ------------------------------------------------------------------------
    // Data
    // ------------------------------------------------------------------------

protected:
    QVector<KhandakerMojoMedicationItemPtr> m_medications;
    QVector<KhandakerMojoTherapyItemPtr> m_therapies;
    QPointer<Questionnaire> m_questionnaire;
    // ------------------------------------------------------------------------
    // Getters/setters
    // ------------------------------------------------------------------------

public:
    QVariant getCustomMedication() const;
    bool setCustomMedication(const QVariant& value);

public:
    static const QString KHANDAKERMOJOMEDICATIONTHERAPY_TABLENAME;
};
