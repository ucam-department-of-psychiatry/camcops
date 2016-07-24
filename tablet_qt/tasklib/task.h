#pragma once
#include <QString>
#include <QVariant>
#include "lib/databaseobject.h"

#define PATIENT_FK_FIELDNAME "patient_id"

// To make makeTables() static, we need something like:
// - a static member object detailing the fields, via that static member's
//   constructor - e.g. a TableSpec class:
//      static MyTableSpec m_tablespec;
//      ...
//      MyTableSpec::MyTableSpec()
//      {
//          addField("thing", QVariant::Int);
//          ...
//      }
// - a normal member object containing field values for those fields, e.g.
//      MyFieldValues m_fields;
//      ...
//      MyTask::MyTask() :
//          m_fields(m_tablespec)
//      {
//      }
// - however, I don't see how the static constructor for the fieldspec is going
//   to be able to read other static properties like hasClinician().
//   Others agree:
//      http://stackoverflow.com/questions/1197106/static-constructors-in-c-need-to-initialize-private-static-objects
// - Then beware static init order:
//   https://isocpp.org/wiki/faq/ctors#static-init-order
// - Moreover, functions cannot be both static and virtual.
//   http://stackoverflow.com/questions/1820477/c-static-virtual-members
//   So you can't do, e.g. "virtual static bool anonymous() const { return false; }"
//   and override that in derived classes.
//   All sorts of nasty template hacks follow...
// - So we're probably better off with the idiom that isolated class instances
//   perform "static" functions.
// - http://cplusplus.bordoon.com/static_initialization.html
//   "... the basic rule that class object constructors and static variable
//   initializer expressions should not refer to class static methods or
//   external variables."

class Task
{
public:
    Task(const QSqlDatabase& db);
    virtual ~Task() {}
    // Things that should ideally be class methods but we'll do by instance:
    virtual QString tablename() const = 0;
    virtual QString shortname() const = 0;
    virtual QString longname() const = 0;
    virtual bool anonymous() const { return false; }
    virtual bool hasClinician() const { return false; }
    virtual bool hasRespondent() const { return false; }
    virtual bool prohibitsCommercial() const { return false; }
    virtual bool prohibitsResearch() const { return false; }
    DatabaseObject* makeBaseDatabaseObject();
    virtual DatabaseObject* makeDatabaseObject();
    virtual void makeTables();
    virtual void makeAncillaryTables() {}
    // No need to override, but do need to CALL FROM CONSTRUCTOR:
    void initDatabaseObject(int loadPk = NONEXISTENT_PK);
    // Setters:
    void setEditable(bool editable);
    void setCrippled(bool crippled);
    // Getters:
    bool editable() const { return m_editable; }
    bool crippled() const { return m_crippled; }
    // Field access:
    QVariant value(const QString& fieldname);
    bool setValue(const QString& fieldname, const QVariant& value);  // returns: changed?

protected:
    QSqlDatabase m_db;
    DatabaseObject* m_pDbObject;
    bool m_editable;
    bool m_crippled;

public:
    friend QDebug operator<<(QDebug debug, const Task& t);
};
