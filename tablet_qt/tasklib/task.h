#pragma once
#include <QString>
#include <QVariant>
#include "lib/databaseobject.h"


class Task
{
public:
    Task(const QSqlDatabase& db);
    virtual ~Task() {}
    // Things that should ideally be class methods but we'll do by instance:
    virtual QString tablename() const = 0;
    virtual QString shortname() const = 0;
    virtual QString longname() const = 0;
    virtual bool isAnonymous() const { return false; }
    virtual bool hasClinician() const { return false; }
    virtual bool hasRespondent() const { return false; }
    virtual bool prohibitsCommercial() const { return false; }
    virtual bool prohibitsResearch() const { return false; }
    virtual void makeTables();
    virtual void makeAncillaryTables() {}
    // No need to override, but do need to CALL FROM CONSTRUCTOR:
    void loadByPk(int loadPk = NONEXISTENT_PK);
    // Setters:
    void setEditable(bool editable);
    void setCrippled(bool crippled);
    // Getters:
    bool isEditable() const { return m_editable; }
    bool isCrippled() const { return m_crippled; }
    // Field access:
    QVariant getValue(const QString& fieldname);
    bool setValue(const QString& fieldname, const QVariant& value);  // returns: changed?

protected:
    QSqlDatabase m_db;
    DatabaseObject* m_p_dbobject;
    bool m_editable;
    bool m_crippled;

public:
    friend QDebug operator<<(QDebug debug, const Task& t);
};
