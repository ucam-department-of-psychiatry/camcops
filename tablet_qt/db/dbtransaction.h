#pragma once
class QSqlDatabase;


class DbTransaction
{
public:
    DbTransaction(const QSqlDatabase& db);
    ~DbTransaction();
    void fail();
    void succeed();
protected:
    const QSqlDatabase& m_db;
    bool m_fail;
};
