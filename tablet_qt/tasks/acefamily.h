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
class QuElement;
class Questionnaire;

class AceFamily : public Task
{
    // This is an abstract class (it doesn't implement all of Task's pure
    // virtual methods). It supports the ACE-III and Mini-ACE tasks.

    Q_OBJECT

public:
    AceFamily(
        CamcopsApp& app,
        DatabaseManager& db,
        const QString& tablename,
        QObject* parent = nullptr
    );

    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual bool hasClinician() const override
    {
        return true;
    }

    virtual bool prohibitsCommercial() const override
    {
        return true;
    }

    virtual Version minimumServerVersion() const override;
    virtual bool isTaskProperlyCreatable(QString& why_not_creatable
    ) const override;
    virtual QString xstringTaskname() const override;

protected:
    // ------------------------------------------------------------------------
    // Cosmetic support functions
    // ------------------------------------------------------------------------
    QString scorePercent(int score, int out_of) const;

    // ------------------------------------------------------------------------
    // Task address version support functions
    // ------------------------------------------------------------------------
    // The task address version currently in use (A/B/C).
    // Guaranteed to be valid (even with missing/incorrect underlying data),
    // by defaulting to 'A'.
    virtual QString taskAddressVersion() const = 0;

    // Is it OK to change task address version? (The converse question: have we
    // collected data, such that changing task address version is dubious?)
    virtual bool isChangingAddressVersionOk() const = 0;

    // Internal: the CSV-split xstring providing task address version info.
    QStringList rawAddressVersionsAvailable() const;

    // Is the information provided by the server about available address
    // versions (e.g. A or A,B,C) valid?
    bool isAddressVersionInfoValid() const;

    // Internal function to provide the validity check on a specific list
    // of strings.
    bool isAddressVersionInfoValid(const QStringList& versions) const;

    // Address versions that are available. Each element is a character,
    // typically "A", "B", "C" (but this varies with language).
    // Defaults to "A" alone if the information is invalid.
    QStringList addressVersionsAvailable() const;

    // One of the seven components of the main (target) address:
    QString targetAddressComponent(int component) const;

    // ------------------------------------------------------------------------
    // Automatic tag generation
    // ------------------------------------------------------------------------
    QString tagAddressRegistration(int trial, int component) const;
    QString tagAddressFreeRecall(int component) const;

    // ------------------------------------------------------------------------
    // Editor assistance functions
    // ------------------------------------------------------------------------
    QuElement* textRaw(const QString& string) const;
    QuElement* text(const QString& stringname) const;
    QuElement* explanation(const QString& stringname) const;
    QuElement* stdExplan(const QString& stringname) const;
    QuElement* remExplan(const QString& stringname) const;
    QuElement* heading(const QString& stringname) const;
    QuElement* subheading(const QString& stringname) const;
    QuElement* instructionRaw(const QString& string) const;
    QuElement* instruction(const QString& stringname) const;
    QuElement* stdInstruct(const QString& stringname) const;
    QuElement* remInstruct(const QString& stringname) const;
    QuElement* boolean(
        const QString& stringname,
        const QString& fieldname,
        bool mandatory = true,
        bool bold = false
    );
    QuElement* boolimg(
        const QString& filenamestem,
        const QString& fieldname,
        bool mandatory = true
    );
    QuElement* warning(const QString& string) const;

protected:
    QPointer<Questionnaire> m_questionnaire;

public:
    static const QString ACE3_TABLENAME;  // used for xstring in ACE/miniACE

protected:
    static const int TOTAL_MINI_ACE = 30;
    static const int MIN_AGE = 0;
    static const int MAX_AGE_Y = 120;
    static const int FLUENCY_TIME_SEC = 60;
    static const int N_MEM_REPEAT_RECALL_ADDR = 7;
    static const int ADDR_LEARN_N_TRIALS = 3;

    static const QString TASK_DEFAULT_VERSION;  // A

    static const QString FN_TASK_EDITION;
    static const QString FN_TASK_ADDRESS_VERSION;
    static const QString FN_REMOTE_ADMINISTRATION;
    static const QString FN_AGE_FT_EDUCATION;
    static const QString FN_OCCUPATION;
    static const QString FN_HANDEDNESS;

    static const QString FP_ATTN_TIME;

    static const QString FP_MEM_REPEAT_ADDR_GENERIC;
    static const QString FP_MEM_REPEAT_ADDR_TRIAL1;
    static const QString FP_MEM_REPEAT_ADDR_TRIAL2;
    static const QString FP_MEM_REPEAT_ADDR_TRIAL3;
    static const QString FP_MEM_RECALL_ADDRESS;

    static const QString FN_FLUENCY_ANIMALS_SCORE;

    static const QString FN_VSP_DRAW_CLOCK;

    static const QString FN_PICTURE1_BLOBID;
    static const QString FN_PICTURE2_BLOBID;
    static const QString FN_COMMENTS;

    static const QString TAG_PG_PREAMBLE;
    static const QString TAG_EL_CHOOSE_TASK_VERSION;
    static const QString TAG_EL_SHOW_TASK_VERSION;
    static const QString TAG_REMOTE;
    static const QString TAG_STANDARD;
    static const QString TAG_PG_ADDRESS_LEARNING_FAMOUS;
    static const QString TAG_PG_MEM_FREE_RECALL;

    static const QString X_MINI_ACE_SCORE;
};
