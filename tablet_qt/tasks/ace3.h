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

void initializeAce3(TaskFactory& factory);

class Ace3 : public AceFamily
{
    Q_OBJECT

public:
    Ace3(
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
    virtual bool isTaskProperlyCreatable(QString& why_not_creatable
    ) const override;
    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QStringList summary() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Task-specific calculations
    // ------------------------------------------------------------------------
    int getAttnScore() const;  // out of 18
    int getMemScore() const;  // out of 26
    int getFluencyScore() const;  // out of 14
    int getLangScore() const;  // out of 26
    int getVisuospatialScore() const;  // out of 16
    int totalScore() const;  // out of 100
    int miniAceScore() const;  // out of 30

protected:
    // ------------------------------------------------------------------------
    // Internal scoring/completeness tests
    // ------------------------------------------------------------------------
    int getFollowCommandScore() const;
    int getRepeatWordScore() const;
    int getMemRecognitionScore() const;
    bool isRecognitionComplete() const;

    // ------------------------------------------------------------------------
    // Task address version support functions
    // ------------------------------------------------------------------------

    // The task address version currently in use (A/B/C).
    // Guaranteed to be valid (even with missing/incorrect underlying data),
    // by defaulting to 'A'.
    QString taskAddressVersion() const override;

    // Is it OK to change task address version? (The converse question: have we
    // collected data, such that changing task address version is dubious?)
    bool isChangingAddressVersionOk() const override;

    // Is a specific answer both present and correct?
    bool isAddressRecogAnswerCorrect(int line) const;

    // An element from the 5-row, 3-alternative-column grid for address
    // recognition (using 1-based numbering):
    QString addressRecogElement(int line, int column) const;

    // Is the "correct column" information for the current task version valid?
    bool isAddressRecogCorrectColumnInfoValid() const;

    // Is the given "correct column" information valid?
    bool isAddressRecogCorrectColumnInfoValid(const QVector<int>& correct_cols
    ) const;

    // The correct option for each of the 5 lines for address recognition, for
    // the current task version. Guaranteed to return correctly formatted data,
    // by defaulting to English 'A'.
    QVector<int> correctColumnsAddressRecog() const;

    // The correct option for each of the 5 lines for address recognition, for
    // any given task version. May return invalid data.
    QVector<int> correctColumnsAddressRecog(const QString& task_address_version
    ) const;

    // MCQ options for a given address recognition line
    NameValueOptions getAddressRecogOptions(int line) const;

    // ------------------------------------------------------------------------
    // Automatic tag generation
    // ------------------------------------------------------------------------
    QString tagAddressRecog(int line) const;

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

    // Update the recognition display according to what the subject recalled.
    void updateAddressRecognition();

    // Update language elements depending on the subject's practice trial.
    void langPracticeChanged(const FieldRef* fieldref);
};
