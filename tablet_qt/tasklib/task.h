#pragma once
#include <QString>
#include "lib/databaseobject.h"

extern const QString PATIENT_FK_FIELDNAME;


class Task : public DatabaseObject
{
public:
    Task(const QSqlDatabase& db,
         const QString& tablename,
         bool is_anonymous,
         bool has_clinician,
         bool has_respondent);
    virtual ~Task() {}
    void setPatient(int patient_id);
    // ------------------------------------------------------------------------
    // General info
    // ------------------------------------------------------------------------
    // Things that should ideally be class methods but we'll do by instance:
    // tablename(): already implemented by DatabaseObject
    virtual QString shortname() const = 0;
    virtual QString longname() const = 0;
    virtual QString menutitle() const = 0;  // usually "longname (shortname)"
    virtual QString menusubtitle() const = 0;  // descriptive
    virtual bool isAnonymous() const { return false; }
    virtual bool hasClinician() const { return false; }
    virtual bool hasRespondent() const { return false; }
    virtual bool prohibitsCommercial() const { return false; }
    virtual bool prohibitsResearch() const { return false; }
    virtual bool isEditable() const { return true; }
    virtual bool isCrippled() const { return !hasExtraStrings(); }
    virtual bool hasExtraStrings() const { return false; }  // ***
    // ------------------------------------------------------------------------
    // Tables
    // ------------------------------------------------------------------------
    virtual void makeTables();
    virtual void makeAncillaryTables() {}
    // ------------------------------------------------------------------------
    // Database object functions
    // ------------------------------------------------------------------------
    // No need to override, but do need to CALL load() FROM CONSTRUCTOR:
    virtual bool load(int pk = NONEXISTENT_PK);
    // virtual bool save();
    // ------------------------------------------------------------------------
    // Specific info
    // ------------------------------------------------------------------------
    virtual bool isComplete() const = 0;
    virtual QString getSummary() const { return "?"; }
    virtual QString getDetail() const { return ""; }
    virtual void edit() {}
};
