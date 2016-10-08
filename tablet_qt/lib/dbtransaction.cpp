#include "dbtransaction.h"
#include "lib/dbfunc.h"

DbTransaction::DbTransaction(const QSqlDatabase& db) :
    m_db(db),
    m_fail(false)
{
    DbFunc::exec(db, "BEGIN TRANSACTION");
}


DbTransaction::~DbTransaction()
{
    if (m_fail) {
        DbFunc::exec(m_db, "ROLLBACK");
    } else {
        DbFunc::exec(m_db, "COMMIT");
    }
}


void DbTransaction::fail()
{
    m_fail = true;
}


void DbTransaction::succeed()
{
    m_fail = false;
}
