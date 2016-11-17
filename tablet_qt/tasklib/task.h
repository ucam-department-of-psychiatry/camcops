#pragma once
#include <QCoreApplication>  // for Q_DECLARE_TR_FUNCTIONS
#include <QDateTime>
#include <QString>
#include "db/databaseobject.h"

class CamcopsApp;
class Patient;
class OpenableWidget;

extern const QString PATIENT_FK_FIELDNAME;


class Task : public DatabaseObject
{
    Q_OBJECT
    friend class SingleTaskMenu;  // so it can call setPatient
public:
    Task(CamcopsApp& app,
         const QSqlDatabase& db,
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
    virtual bool isAnonymous() const { return false; }
    virtual bool hasClinician() const { return false; }
    virtual bool hasRespondent() const { return false; }
    virtual bool prohibitsCommercial() const { return false; }
    virtual bool prohibitsResearch() const { return false; }
    virtual bool isEditable() const { return true; }
    virtual bool isCrippled() const { return !hasExtraStrings(); }
    virtual bool hasExtraStrings() const;
    // ------------------------------------------------------------------------
    // Tables
    // ------------------------------------------------------------------------
    virtual void makeTables();
    virtual void makeAncillaryTables() {}
    // ------------------------------------------------------------------------
    // Database object functions
    // ------------------------------------------------------------------------
    // No need to override, but do need to CALL load() FROM CONSTRUCTOR:
    virtual bool load(int pk = DbConst::NONEXISTENT_PK);
    virtual bool save();
    // ------------------------------------------------------------------------
    // Specific info
    // ------------------------------------------------------------------------
    virtual bool isComplete() const = 0;
    virtual QString summary() const;
    virtual QString detail() const;
    virtual OpenableWidget* editor(bool read_only = false);
    // ------------------------------------------------------------------------
    // Assistance functions
    // ------------------------------------------------------------------------
    QDateTime whenCreated() const;
    QString summaryWithCompleteSuffix() const;
    QString xstring(const QString& stringname) const;
    // ------------------------------------------------------------------------
    // Editing
    // ------------------------------------------------------------------------
public slots:
    void editStarted();
    void editFinished(bool aborted = false);
    // ------------------------------------------------------------------------
    // Patient functions (for non-anonymous tasks)
    // ------------------------------------------------------------------------
public:
    Patient* patient() const;
protected:
    void setPatient(int patient_id);  // used by derived classes
protected:
    CamcopsApp& m_app;
    mutable QSharedPointer<Patient> m_patient;
    bool m_editing;
    QDateTime m_editing_started;
};


// ===========================================================================
// Typedefs
// ===========================================================================

using TaskPtr = QSharedPointer<Task>;
using TaskWeakPtr = QWeakPointer<Task>;
using TaskPtrList = QList<TaskPtr>;
