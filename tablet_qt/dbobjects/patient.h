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

#pragma once
#include "db/databaseobject.h"
#include <QDate>
#include <QMap>
#include <QPointer>
class CamcopsApp;
class IdPolicy;
class OpenableWidget;
class Questionnaire;

extern const QString FORENAME_FIELD;
extern const QString SURNAME_FIELD;
extern const QString DOB_FIELD;
extern const QString SEX_FIELD;
extern const QString ADDRESS_FIELD;
extern const QString GP_FIELD;
extern const QString OTHER_FIELD;
extern const QString IDNUM_FIELD_PREFIX;
extern const QString IDNUM_FIELD_FORMAT;
extern const QString ANY_IDNUM;


class Patient : public DatabaseObject
{
    Q_OBJECT
    using AttributesType = QMap<QString, bool>;
public:
    // ------------------------------------------------------------------------
    // Creation
    // ------------------------------------------------------------------------
    Patient(CamcopsApp& app,
            DatabaseManager& db,
            int load_pk = dbconst::NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // Ancillary management
    // ------------------------------------------------------------------------
    virtual void loadAllAncillary(int pk) override;
    virtual QVector<DatabaseObjectPtr> getAncillarySpecimens() const override;
    virtual QVector<DatabaseObjectPtr> getAllAncillary() const override;
    // ------------------------------------------------------------------------
    // Information about patients
    // ------------------------------------------------------------------------
    int id() const;
    QString forename() const;
    QString surname() const;
    QString sex() const;
    bool isFemale() const;
    bool isMale() const;
    QDate dob() const;
    QString dobText() const;
    int ageYears() const;
    bool hasForename() const;
    bool hasSurname() const;
    bool hasDob() const;
    bool hasSex() const;
    bool hasIdnum(int which_idnum) const;
    QVector<int> whichIdnumsPresent() const;
    QVector<int> whichIdnumsHaveEntries() const;
    QVariant idnumVariant(int which_idnum) const;
    qlonglong idnumInteger(int which_idnum) const;
    AttributesType policyAttributes() const;
    bool compliesWith(const IdPolicy& policy) const;
    bool compliesWithUpload() const;
    bool compliesWithFinalize() const;
    QString shortIdnumSummary() const;
    bool othersClashOnIdnum(int which_idnum) const;
    bool anyIdClash() const;
    int numTasks() const;
    virtual void deleteFromDatabase() override;
    bool matchesForMerge(const Patient* other) const;
    // Helper functions for various viewers:
    QString descriptionForMerge() const;
    QString forenameSurname() const;
    QString surnameUpperForename() const;
    QString sexAgeDob() const;
    QString ageSexDob() const;
    QString twoLineDetailString() const;
    QString oneLineHtmlDetailString() const;
    // ------------------------------------------------------------------------
    // Editing and other manipulations
    // ------------------------------------------------------------------------
    OpenableWidget* editor(bool read_only);
    void mergeInDetailsAndTakeTasksFrom(const Patient* other);
public:
    static const QString TABLENAME;
protected:
    void buildPage();
    void addIdNum();
    void deleteIdNum(int which_idnum);
    void sortIdNums();
    void updateQuestionnaireIndicators(const FieldRef* fieldref = nullptr,
                                       const QObject* originator = nullptr);
protected:
    QVector<PatientIdNumPtr> m_idnums;
    QuPagePtr m_page;
    QPointer<Questionnaire> m_questionnaire;
};
