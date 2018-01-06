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
#include <QMap>
#include <QMutex>
#include <QSharedPointer>
#include <QSqlDatabase>
#include <QVector>
#include <QWaitCondition>
#include "db/dbfunc.h"
#include "db/queryresult.h"
#include "db/sqlargs.h"
#include "db/sqlitepragmainfofield.h"
#include "db/threadedqueryrequest.h"
#include "db/whereconditions.h"
#include "db/whichdb.h"
class DatabaseWorkerThread;
class Field;


class DatabaseManager
{
    /*

     Called by the main (GUI) thread.
     Owns and operates a worker thread which handles ALL database comms for
     a single database, if multithreading mode is used.

     See database_performance.txt

     In terms of the number of threads: threads are cheap when they're
     waiting and we don't really want a single thread having to wait both
     for "open" requests and for query requests. The thread has to own its
     database connection fully. So: one thread per database, and one
     DatabaseManager per database. There should be no file-level crosstalk
     between the databases (it all goes via CamCOPS) so there is no
     requirement to synchronize mutexes across >1 database.

     In terms of the thread control mechanism:

     There are several ways to operate with QThread:
     - QThread (owned by creator thread) running a thread with a worker
       QObject (living in the new, QThread, thread) -- this model has the
       QThread running an event loop, and allows the worker QThread to
       receive signals;
     - subclassing QThread and overriding run(), for when you don't care
       about event loops or signals.
     The latter is tempting. However, we do have to deal with waiting for
     both an exit signal (e.g. an atomic bool), and database events to
     arrive. In a run() loop, we don't want to "spin" needlessly in what
     becomes a while(1) loop, like this:

        while (!exit_flag) {
            if (stuff_waiting) {
                process_stuff();
            }
            // otherwise loop around and around
        }

      but we can't do this:

        while (!exit_flag) {
            wait_for_stuff_to_arrive_eg_mutex_signal();  // WON'T NOTICE EXIT SIGNAL HERE
            process_stuff();
        }

      so the correct solution may be:

        event loop
        -> signal "quit" [well, just QThread::quit()]
        -> signal "stuff arrived" -> process it and return to event loop
        ... and can never be in both at the same time.

      ... probably more elegant and safer.
      How will we mimic a blocking call to the thread?
      Can still use QWaitCondition m_queries_are_complete.

      Note also another pattern:
        https://stackoverflow.com/questions/3556421/blocked-waiting-for-a-asynchronous-qt-signal

      Mind you, there is overhead to an event loop, and we are not going to use
      a dummy event loop to receive "blocking" notifications back on the main
      thread.

      And we can share a QWaitCondition between "incoming" and "abort":

        forever {
            // Fetch a request
            m_mutex_requests.lock();
            if (m_requests.isEmpty()) {
                m_requests_waiting_or_abort.wait(&m_mutex_requests);
            }
            if (m_requests.isEmpty()) {
                // m_requests_waiting_or_abort triggered with no requests;
                // this means "abort"!
            }
            QueryRequest request = m_requests.pop_front();
            bool now_empty = m_requests.isEmpty();
            m_mutex_requests.unlock();

            // Execute the request and push result if required
            execute(request);

            // If that (even transiently) cleared the request queue, let anyone
            // who was waiting for the results know
            if (now_empty) {
                m_queries_are_complete.wakeAll();
            }
        }

      or we could use a request that is a "quit" request...

      These things all save some (potentially large) copying.

    */

    friend class DatabaseWorkerThread;

public:
    // What to fetch from queries:

    // ========================================================================
    // Constructor and destructor:
    // ========================================================================
    DatabaseManager(const QString& filename,
                    const QString& connection_name,
                    const QString& database_type = whichdb::DBTYPE,
                    bool threaded = true);
    ~DatabaseManager();

    // ========================================================================
    // Settings
    // ========================================================================
    void setVacuumOnClose(bool vacuum_on_close);

    // ========================================================================
    // Main methods:
    // ========================================================================
    void execNoAnswer(const SqlArgs& sqlargs, bool suppress_errors = false);
    QueryResult query(const SqlArgs& sqlargs,
                      QueryResult::FetchMode fetch_mode = QueryResult::FetchMode::FetchAll,
                      bool store_column_names = false,
                      bool suppress_errors = false);
    bool exec(const SqlArgs& sqlargs, bool suppress_errors = false);

    // ========================================================================
    // Convenience query methods
    // ========================================================================
    void execNoAnswer(const QString& sql, const ArgList& args = ArgList());
    bool exec(const QString& sql, const ArgList& args = ArgList());
    QueryResult query(const QString& sql,
                      const ArgList& args = ArgList(),
                      QueryResult::FetchMode fetch_mode = QueryResult::FetchMode::FetchAll,
                      bool store_column_names = false,
                      bool suppress_errors = false);
    QueryResult query(const QString& sql,
                      QueryResult::FetchMode fetch_mode,
                      bool store_column_names = false,
                      bool suppress_errors = false);

    // ========================================================================
    // SQL
    // ========================================================================

    // ------------------------------------------------------------------------
    // Select
    // ------------------------------------------------------------------------
    QVariant fetchFirstValue(const SqlArgs& sqlargs);
    QVariant fetchFirstValue(const QString& sql);
    int fetchInt(const SqlArgs& sqlargs, int failure_default = -1);
    int count(const QString& tablename,
              const WhereConditions& where = WhereConditions());
    QVector<int> getSingleFieldAsIntList(const QString& tablename,
                                         const QString& fieldname,
                                         const WhereConditions& where);
    QVector<int> getPKs(const QString& tablename,
                        const QString& pkname,
                        const WhereConditions& where = WhereConditions());
    bool existsByPk(const QString& tablename,
                    const QString& pkname, int pkvalue);

    // ------------------------------------------------------------------------
    // Transactions
    // ------------------------------------------------------------------------
    void beginTransaction();
    void commit();
    void rollback();

    // ------------------------------------------------------------------------
    // Modifications
    // ------------------------------------------------------------------------
    bool deleteFrom(const QString& tablename,
                    const WhereConditions& where = WhereConditions());

    // ------------------------------------------------------------------------
    // Reading schema/structure
    // ------------------------------------------------------------------------
    QStringList getAllTables();
    bool tableExists(const QString& tablename);
    QVector<SqlitePragmaInfoField> getPragmaInfo(const QString& tablename);
    QStringList getFieldNames(const QString& tablename);
    QString dbTableDefinitionSql(const QString& tablename);

    // ------------------------------------------------------------------------
    // Altering schema/structure
    // ------------------------------------------------------------------------
    bool createIndex(const QString& indexname,
                     const QString& tablename,
                     QStringList fieldnames);
    void renameColumns(const QString& tablename,
                       const QVector<QPair<QString, QString>>& from_to,
                       const QString& tempsuffix = dbfunc::TABLE_TEMP_SUFFIX);
    void renameTable(const QString& from, const QString& to);
    void changeColumnTypes(const QString& tablename,
                           const QVector<QPair<QString, QString>>& field_newtype,
                           const QString& tempsuffix = dbfunc::TABLE_TEMP_SUFFIX);
    void createTable(const QString& tablename,
                     const QVector<Field>& fieldlist,
                     const QString& tempsuffix = dbfunc::TABLE_TEMP_SUFFIX);
    void dropTable(const QString& tablename);
    void dropTablesNotIn(const QStringList& good_tables);
    void dropTablesNotExplicitlyCreatedByUs();

    // ------------------------------------------------------------------------
    // Performance tweaks
    // ------------------------------------------------------------------------
    void vacuum();

    // ------------------------------------------------------------------------
    // Encryption queries, via SQLCipher
    // ------------------------------------------------------------------------
    bool canReadDatabase();
    bool pragmaKey(const QString& passphase);
    bool pragmaRekey(const QString& passphase);
    bool databaseIsEmpty();
    bool encryptToAnother(const QString& filename, const QString& passphrase);

    // ========================================================================
    // Internals
    // ========================================================================
protected:

    // Opening/closing internals
    void openDatabaseOrDie();
    bool openDatabase();
    bool openDatabaseActual();
    void closeDatabase();
    void closeDatabaseActual();

    // GUI thread internals
    void pushRequest(const ThreadedQueryRequest& request);
    void waitForQueriesToComplete();
    QueryResult popResult();

    // Worker thread internals
    void work();
    void execute(const ThreadedQueryRequest& request);
    void pushResult(const QueryResult& result);

    // Debugging and DANGEROUS internals
    QSqlDriver* driver() const;  // UNCERTAIN IF THIS IS OK to return the driver on the GUI thread, even if it lives in another

protected:
    // How to open our database:
    QString m_filename;  // written only in constructor; thread-safe access
    QString m_connection_name;  // written only in constructor; thread-safe access
    QString m_database_type;  // written only in constructor; thread-safe access
    // How to operate:
    bool m_threaded;  // written only in constructor; thread-safe access
    bool m_vacuum_on_close;

    // Internal data:
    QSharedPointer<DatabaseWorkerThread> m_thread;
    bool m_opened_database;  // used in a thread-safe way
    QString m_opening_failure_msg;
    QSqlDatabase m_db;  // connection owned by worker thread if m_threaded, else GUI thread

    QMutex m_mutex_requests;
    QVector<ThreadedQueryRequest> m_requests;  // execution queue

    QMutex m_mutex_results;
    QVector<QueryResult> m_results;

    QWaitCondition m_open_db_complete;
    QWaitCondition m_requests_waiting;
    QWaitCondition m_queries_are_complete;

    QStringList m_created_tables;  // trivial internal helper; accessed only by GUI thread

    friend class HelpMenu;  // for driver() access
};
