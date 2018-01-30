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
#include <QCoreApplication>  // for Q_DECLARE_TR_FUNCTIONS
#include <QDateTime>
#include <QString>
#include "common/aliases_camcops.h"
#include "db/databaseobject.h"

class CamcopsApp;
class OpenableWidget;
class QGraphicsScene;
class Version;

extern const QString PATIENT_FK_FIELDNAME;


class Task : public DatabaseObject
{
    Q_OBJECT
    friend class SingleTaskMenu;  // so it can call setPatient
    friend class Patient;  // so it can call setPatient
public:
    Task(CamcopsApp& app,
         DatabaseManager& db,
         const QString& tablename,
         bool is_anonymous,
         bool has_clinician,
         bool has_respondent);
    virtual ~Task() {}
    // ------------------------------------------------------------------------
    // General info
    // ------------------------------------------------------------------------
    // Things that should ideally be class methods but we'll do by instance:
    // tablename(): already implemented by DatabaseObject
    virtual QString shortname() const = 0;
    virtual QString longname() const = 0;
    virtual QString menutitle() const;  // default: "longname (shortname)"
    virtual QString menusubtitle() const = 0;  // descriptive
    virtual QString infoFilenameStem() const;  // default: tablename
    virtual QString xstringTaskname() const;  // default: tablename
    virtual QString instanceTitle() const;
    virtual bool isAnonymous() const;
    virtual bool hasClinician() const;
    virtual bool hasRespondent() const;
    virtual bool prohibitsClinical() const { return false; }
    virtual bool prohibitsCommercial() const { return false; }
    virtual bool prohibitsEducational() const { return false; }
    virtual bool prohibitsResearch() const { return false; }
    virtual bool isEditable() const { return true; }  // ... once created
    virtual bool isCrippled() const { return !hasExtraStrings(); }
    virtual bool hasExtraStrings() const;
    virtual bool isTaskPermissible(QString& why_not_permissible) const;
    virtual Version minimumServerVersion() const;
    virtual bool isTaskUploadable(QString& why_not_uploadable) const;
    // ------------------------------------------------------------------------
    // Tables and other classmethods
    // ------------------------------------------------------------------------
    virtual QStringList ancillaryTables() const { return QStringList(); }
    virtual QString ancillaryTableFKToTaskFieldname() const { return ""; }
    QStringList allTables() const;
    virtual void makeTables();
    virtual void makeAncillaryTables() {}
    int count(const WhereConditions& where = WhereConditions()) const;
    int countForPatient(int patient_id) const;
    virtual void upgradeDatabase(const Version& old_version,
                                 const Version& new_version);
    // ------------------------------------------------------------------------
    // Database object functions
    // ------------------------------------------------------------------------
    // No need to override, but do need to CALL load() FROM CONSTRUCTOR:
    virtual bool load(int pk = dbconst::NONEXISTENT_PK);
    virtual bool save();
    // ------------------------------------------------------------------------
    // Specific info
    // ------------------------------------------------------------------------
    virtual bool isComplete() const = 0;
    virtual QStringList summary() const;
    virtual QStringList detail() const;
    virtual OpenableWidget* editor(bool read_only = false);
    // ------------------------------------------------------------------------
    // Assistance functions
    // ------------------------------------------------------------------------
    QDateTime whenCreated() const;
    QStringList completenessInfo() const;
    QString xstring(const QString& stringname,
                    const QString& default_str = "") const;
    QString appstring(const QString& stringname,
                      const QString& default_str = "") const;
    QStringList fieldSummaries(const QString& xstringprefix,
                               const QString& xstringsuffix,
                               const QString& spacer,
                               const QString& fieldprefix,
                               int first,
                               int last,
                               const QString& suffix = "") const;
    QStringList fieldSummariesYesNo(const QString& xstringprefix,
                                    const QString& xstringsuffix,
                                    const QString& spacer,
                                    const QString& fieldprefix,
                                    int first,
                                    int last,
                                    const QString& suffix = "") const;
    QStringList clinicianDetails(const QString& separator = ": ") const;
    QStringList respondentDetails() const;
    // ------------------------------------------------------------------------
    // Editing
    // ------------------------------------------------------------------------
    double editingTimeSeconds() const;
    void setDefaultClinicianVariablesAtFirstUse();
    virtual void setDefaultsAtFirstUse() {}
protected:
    OpenableWidget* makeGraphicsWidget(
            QGraphicsScene* scene, const QColor& background_colour,
            bool fullscreen = true, bool esc_can_abort = true);
    OpenableWidget* makeGraphicsWidgetForImmediateEditing(
            QGraphicsScene* scene, const QColor& background_colour,
            bool fullscreen = true, bool esc_can_abort = true);
    QuElement* getClinicianQuestionnaireBlockRawPointer();
    QuElementPtr getClinicianQuestionnaireBlockElementPtr();
    QuPagePtr getClinicianDetailsPage();
    bool isClinicianComplete() const;
    bool isRespondentComplete() const;
    QVariant respondentRelationship() const;
    QuElement* getRespondentQuestionnaireBlockRawPointer(bool second_person);
    QuElementPtr getRespondentQuestionnaireBlockElementPtr(bool second_person);
    QuPagePtr getRespondentDetailsPage(bool second_person);
    QuPagePtr getClinicianAndRespondentDetailsPage(bool second_person);
public slots:
    void editStarted();
    void editFinished(bool aborted = false);
    void editFinishedProperly();
    void editFinishedAbort();
    // ------------------------------------------------------------------------
    // Patient functions (for non-anonymous tasks)
    // ------------------------------------------------------------------------
public:
    Patient* patient() const;
    QString getPatientName() const;
    bool isFemale() const;
    bool isMale() const;
protected:
    void setPatient(int patient_id);  // used when tasks are being added
    void moveToPatient(int patient_id);  // used for patient merges
protected:
    mutable QSharedPointer<Patient> m_patient;
    bool m_editing;
    QDateTime m_editing_started;

    // ------------------------------------------------------------------------
    // Class data
    // ------------------------------------------------------------------------
protected:
    bool m_is_anonymous;
    bool m_has_clinician;
    bool m_has_respondent;

    // ------------------------------------------------------------------------
    // Static data
    // ------------------------------------------------------------------------
public:
    static const QString PATIENT_FK_FIELDNAME;
    static const QString FIRSTEXIT_IS_FINISH_FIELDNAME;
    static const QString FIRSTEXIT_IS_ABORT_FIELDNAME;
    static const QString WHEN_FIRSTEXIT_FIELDNAME;
    static const QString EDITING_TIME_S_FIELDNAME;

    static const QString CLINICIAN_SPECIALTY;
    static const QString CLINICIAN_NAME;
    static const QString CLINICIAN_PROFESSIONAL_REGISTRATION;
    static const QString CLINICIAN_POST;
    static const QString CLINICIAN_SERVICE;
    static const QString CLINICIAN_CONTACT_DETAILS;

    static const QString RESPONDENT_NAME;
    static const QString RESPONDENT_RELATIONSHIP;

    static const QString INCOMPLETE_MARKER;
};
