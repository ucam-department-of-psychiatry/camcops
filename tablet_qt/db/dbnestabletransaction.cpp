#include "dbnestabletransaction.h"
#include <QDebug>
#include "db/databasemanager.h"

int DbNestableTransaction::s_count = 0;
int DbNestableTransaction::s_level = 0;


DbNestableTransaction::DbNestableTransaction(DatabaseManager& db) :
    m_db(db),
    m_fail(false)
{
    ++s_count;
    if (s_count < 0) {
        // in case we get wraparound after long use
        // (don't want "-" in savepoint name)
        s_count = 0;
    }
    ++s_level;
    m_name = QString("svp_t%1_l%2").arg(s_count).arg(s_level);
    m_db.execNoAnswer(QString("SAVEPOINT %1").arg(m_name));
}


DbNestableTransaction::~DbNestableTransaction()
{
    if (m_fail) {
        m_db.execNoAnswer(QString("ROLLBACK TO SAVEPOINT %1").arg(m_name));
    } else {
        m_db.execNoAnswer(QString("RELEASE %1").arg(m_name));
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
