#include "dbnestabletransaction.h"
#include <QDebug>
#include <QSqlDatabase>
#include "db/dbfunc.h"

int DbNestableTransaction::s_count = 0;
int DbNestableTransaction::s_level = 0;


DbNestableTransaction::DbNestableTransaction(const QSqlDatabase& db) :
    m_db(db),
    m_fail(false)
{
    ++s_count;
    ++s_level;
    m_name = QString("svp_t%1_l%2").arg(s_count).arg(s_level);
    dbfunc::exec(m_db, QString("SAVEPOINT %1").arg(m_name));
}


DbNestableTransaction::~DbNestableTransaction()
{
    if (m_fail) {
        dbfunc::exec(m_db, QString("ROLLBACK TO SAVEPOINT %1").arg(m_name));
    } else {
        dbfunc::exec(m_db, QString("RELEASE %1").arg(m_name));
    }

    --s_level;
    if (s_level < 0) {
        qCritical() << Q_FUNC_INFO << "BUG: s_level < 0; is" << s_level;
        s_level = 0;
    }
}


void DbNestableTransaction::fail()
{
    m_fail = true;
}


void DbNestableTransaction::succeed()
{
    m_fail = false;
}
