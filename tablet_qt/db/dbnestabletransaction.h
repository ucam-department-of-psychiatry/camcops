#pragma once
#include <QString>
class QSqlDatabase;


class DbNestableTransaction
{
    // https://www.sqlite.org/lang_savepoint.html
public:
    DbNestableTransaction(const QSqlDatabase& db);
    ~DbNestableTransaction();
    void fail();
    void succeed();
protected:
    const QSqlDatabase& m_db;
    bool m_fail;
    QString m_name;

    static int s_count;
    static int s_level;
};
