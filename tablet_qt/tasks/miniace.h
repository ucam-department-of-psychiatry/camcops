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

#include "acefamily.h"

class OpenableWidget;
class TaskFactory;

void initializeMiniAce(TaskFactory& factory);

class MiniAce : public AceFamily
{
    Q_OBJECT

public:
    MiniAce(
        CamcopsApp& app,
        DatabaseManager& db,
        int load_pk = dbconst::NONEXISTENT_PK,
        QObject* parent = nullptr
    );
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString description() const override;

    virtual bool hasClinician() const override
    {
        return true;
    }

    virtual bool prohibitsCommercial() const override
    {
        return true;
    }

    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QStringList summary() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Task-specific calculations
    // ------------------------------------------------------------------------
    int getAttnScore() const;  // out of 4
    int getMemScore() const;  // out of 14
    int getFluencyScore() const;  // out of 7
    int getVisuospatialScore() const;  // out of 5
    int miniAceScore() const;  // out of 30

protected:
    // ------------------------------------------------------------------------
    // Task address version support functions
    // ------------------------------------------------------------------------
    // Is it OK to change task address version? (The converse question: have we
    // collected data, such that changing task address version is dubious?)
    virtual QString taskAddressVersion() const override;
    bool isChangingAddressVersionOk() const override;

    // ------------------------------------------------------------------------
    // Signal handlers
    // ------------------------------------------------------------------------
public slots:
    // Update addresses according to the task version (A/B/C).
    void updateTaskVersionAddresses();

    // Show standard or remote administration instructions.
    void showStandardOrRemoteInstructions();

    // Update the ability to edit the task version address.
    void updateTaskVersionEditability();

protected:
    QPointer<Questionnaire> m_questionnaire;

public:
    static const QString MINIACE_TABLENAME;
};
