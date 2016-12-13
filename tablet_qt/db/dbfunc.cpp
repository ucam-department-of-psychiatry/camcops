/*
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

#define DEBUG_SQL_QUERY
// #define DEBUG_QUERY_END
// #define DEBUG_SQL_RESULT

#include "dbfunc.h"
#include <QDir>
#include <QSqlError>
#include <QSqlQuery>
#include <QSqlRecord>
#include <QStandardPaths>
#include "db/fieldcreationplan.h"
#include "db/sqlitepragmainfofield.h"
#include "lib/convert.h"
#include "lib/debugfunc.h"
#include "lib/uifunc.h"


namespace DbFunc {

    const QString DATA_DATABASE_FILENAME("camcops_data.sqlite");
    const QString SYSTEM_DATABASE_FILENAME("camcops_sys.sqlite");
    const QString TABLE_TEMP_SUFFIX("_temp");

}


void DbFunc::openDatabaseOrDie(QSqlDatabase& db, const QString& filename)
{
    // Opens a database.
    QString dir = QStandardPaths::standardLocations(
        QStandardPaths::AppDataLocation).first();
    // Under Linux: ~/.local/share/camcops/
    if (!QDir(dir).exists()) {
        if (QDir().mkdir(dir)) {
            qDebug() << "Made directory:" << dir;
        } else {
            UiFunc::stopApp("DbFunc::openDatabaseOrDie: Failed to make "
                            "directory: " + dir);
        }
    }
    // http://stackoverflow.com/questions/3541529/is-there-qpathcombine-in-qt4
    QString fullpath = QDir::cleanPath(dir + "/" + filename);
    db.setDatabaseName(fullpath);
    if (db.open()) {
        qInfo() << "Opened databasec:" << fullpath;
    } else {
        QSqlError error = db.lastError();
        qCritical() << "Last database error:" << error;
        qCritical() << "Database:" << db;
        QString errmsg = QString(
            "DbFunc::openDatabaseOrDie: Error: connection to database failed. "
            "Database = %1; error number = %2; error text = %3"
        ).arg(fullpath, QString::number(error.number()), error.text());
        UiFunc::stopApp(errmsg);
    }
}


QString DbFunc::delimit(const QString& identifier)
{
    // Delimits a table or fieldname, by ANSI SQL standards.

    // http://www.sqlite.org/lang_keywords.html
    // http://stackoverflow.com/questions/2901453/sql-standard-to-escape-column-names
    // You must delimit anything with funny characters or any keyword,
    // and the list of potential keywords is long, so just delimit everything.
    return "\"" + identifier + "\"";
}


QString DbFunc::selectColumns(const QStringList& columns, const QString& table)
{
    QStringList delimited_columns;
    for (auto column : columns) {
        delimited_columns.append(delimit(column));
    }
    return QString("SELECT %1 FROM %2")
            .arg(delimited_columns.join(","))
            .arg(delimit(table));
}


void DbFunc::addWhereClause(const WhereConditions& where,
                            SqlArgs& sqlargs_altered)
{
    if (where.isEmpty()) {
        return;
    }
    QStringList whereclauses;
    QMapIterator<QString, QVariant> it(where);
    while (it.hasNext()) {
        it.next();
        QString wherefield = it.key();
        QVariant wherevalue = it.value();
        whereclauses.append(delimit(wherefield) + "=?");
        sqlargs_altered.args.append(wherevalue);
    }
    sqlargs_altered.sql += " WHERE " + whereclauses.join(" AND ");
}


void DbFunc::addArgs(QSqlQuery& query, const ArgList& args)
{
    // Adds arguments to a QSqlQuery from a QList.
    const int size = args.size();
    for (int i = 0; i < size; ++i) {
        query.addBindValue(args.at(i), QSql::In);
    }
}


bool DbFunc::execQuery(QSqlQuery& query, const QString& sql,
                       const ArgList& args)
{
    // Executes an existing query (in place) with the supplied SQL/args.
    // THIS IS THE MAIN POINT THROUGH WHICH ALL QUERIES SHOULD BE EXECUTED.
    query.prepare(sql);
    addArgs(query, args);

#ifdef DEBUG_SQL_QUERY
    {
        qDebug() << "Executing:" << qUtf8Printable(sql);
        QDebug debug = qDebug().nospace();
        debug << "... args: ";
        DebugFunc::debugConcisely(debug, args);
    }  // endl on destruction
#endif

    bool success = query.exec();
#ifdef DEBUG_QUERY_END
    qDebug() << "... query finished";
#endif
    if (!success) {
        qCritical() << "Query failed; error was:" << query.lastError();
    }
#ifdef DEBUG_SQL_RESULT
    if (success && query.isSelect() && !query.isForwardOnly()) {
        qDebug() << "Resultset preview:";
        int row = 0;
        while (query.next()) {
            QDebug debug = qDebug().nospace();
            QSqlRecord rec = query.record();
            int ncols = rec.count();
            debug << "... row " << row << ": ";
            for (int col = 0; col < ncols; ++col) {
                if (col > 0) {
                    debug << "; ";
                }
                debug << rec.fieldName(col) << "=";
                DebugFunc::debugConcisely(debug, query.value(col));
            }
            ++row;
        }  // endl on destruction
        if (row == 0) {
            qDebug() << "<no rows>";
        }
        query.seek(QSql::BeforeFirstRow);  // the original starting position
    }
#endif
    return success;
    // The return value is boolean (success?).
    // Use query.next() to iterate through a result set; see
    // http://doc.qt.io/qt-4.8/sql-sqlstatements.html
}


bool DbFunc::execQuery(QSqlQuery& query, const QString& sql)
{
    ArgList args;
    return execQuery(query, sql, args);
}


bool DbFunc::execQuery(QSqlQuery& query, const SqlArgs& sqlargs)
{
    return execQuery(query, sqlargs.sql, sqlargs.args);
}


bool DbFunc::exec(const QSqlDatabase& db, const QString& sql,
                  const ArgList& args)
{
    // Executes a new query and returns success.
    QSqlQuery query(db);
    return execQuery(query, sql, args);
}


// http://stackoverflow.com/questions/2816293/passing-optional-parameter-by-reference-in-c
bool DbFunc::exec(const QSqlDatabase& db, const QString& sql)
{
    ArgList args;
    return exec(db, sql, args);
}


bool DbFunc::exec(const QSqlDatabase& db, const SqlArgs& sqlargs)
{
    return exec(db, sqlargs.sql, sqlargs.args);
}


bool DbFunc::commit(const QSqlDatabase &db)
{
    // If we ever need to do proper transations, use an RAII object that
    // executes BEGIN TRANSATION on creation and either COMMIT or ROLLBACK
    // on deletion, and/or handles nesting via SAVEPOINT/RELEASE.
    return exec(db, "COMMIT");
}


QVariant DbFunc::dbFetchFirstValue(const QSqlDatabase& db,
                                   const QString& sql,
                                   const ArgList& args)
{
    QSqlQuery query(db);
    execQuery(query, sql, args);
    if (!query.next()) {
        return QVariant();
    }
    return query.value(0);
}


QVariant DbFunc::dbFetchFirstValue(const QSqlDatabase& db, const QString& sql)
{
    ArgList args;
    return dbFetchFirstValue(db, sql, args);
}


int DbFunc::dbFetchInt(const QSqlDatabase& db, const SqlArgs& sqlargs,
                       int failureDefault)
{
    // Executes the specified SQL/args and returns the integer value of the
    // first field of the first result (or failureDefault).
    QSqlQuery query(db);
    execQuery(query, sqlargs);
    if (!query.next()) {
        return failureDefault;
    }
    return query.value(0).toInt();
}


int DbFunc::dbFetchInt(const QSqlDatabase& db, const QString& sql,
                       int failureDefault)
{
    return dbFetchInt(db, SqlArgs(sql), failureDefault);
}


QString DbFunc::sqlParamHolders(int n)
{
    // String like "?,?,?" for n parameter holders
    QString paramholders;
    for (int i = 0; i < n; ++i) {
        if (i != 0) {
            paramholders += ",";
        }
        paramholders += "?";
    }
    return paramholders;
}


ArgList DbFunc::argListFromIntList(const QList<int>& intlist)
{
    ArgList args;
    for (auto value : intlist) {
        args.append(value);
    }
    return args;
}


QString DbFunc::csvHeader(const QSqlQuery& query, const char sep)
{
    QSqlRecord record = query.record();
    int nfields = record.count();
    QStringList fieldnames;
    for (int i = 0; i < nfields; ++i) {
        fieldnames.append(record.fieldName(i));
    }
    return fieldnames.join(sep);
}


QString DbFunc::csvRow(const QSqlQuery& query, const char sep)
{
    int nfields = query.record().count();
    QStringList values;
    for (int i = 0; i < nfields; ++i) {
        values.append(Convert::toSqlLiteral(query.value(i)));
    }
    return values.join(sep);
}


QString DbFunc::csv(QSqlQuery& query, const char sep, const char linesep)
{
    QStringList rows;
    rows.append(csvHeader(query, sep));
    while (query.next()) {
        rows.append(csvRow(query, sep));
    }
    return rows.join(linesep);
}


int DbFunc::count(const QSqlDatabase& db,
                  const QString& tablename, const WhereConditions& where)
{
    SqlArgs sqlargs("SELECT COUNT(*) FROM " + delimit(tablename));
    addWhereClause(where, sqlargs);
    return dbFetchInt(db, sqlargs, 0);
}


QList<int> DbFunc::getPKs(const QSqlDatabase& db,
                          const QString& tablename,
                          const QString& pkname,
                          const WhereConditions& where)
{
    SqlArgs sqlargs(QString("SELECT %1 FROM %2")
                    .arg(delimit(pkname))
                    .arg(delimit(tablename)));
    addWhereClause(where, sqlargs);
    QSqlQuery query(db);
    QList<int> pks;
    if (!execQuery(query, sqlargs)) {
        return pks;  // empty list on failure
    }
    while (query.next()) {
        pks.append(query.value(0).toInt());
    }
    return pks;
}


QStringList DbFunc::getAllTables(const QSqlDatabase& db)
{
    // System tables begin with sqlite_
    // - https://www.sqlite.org/fileformat.html
    // An underscore is a wildcard for LIKE
    // - https://www.sqlite.org/lang_expr.html
    QString sql = "SELECT name "
                  "FROM sqlite_master "
                  "WHERE sql NOT NULL "
                  "AND type='table' "
                  "AND name NOT LIKE 'sqlite\\_%' ESCAPE '\\' "
                  "ORDER BY name";
    QSqlQuery query(db);
    QStringList tablenames;
    if (!execQuery(query, sql)) {
        return tablenames;  // empty list on failure
    }
    while (query.next()) {
        tablenames.append(query.value(0).toString());
    }
    return tablenames;
}


bool DbFunc::deleteFrom(const QSqlDatabase& db,
                        const QString& tablename,
                        const WhereConditions& where)
{
    SqlArgs sqlargs(QString("DELETE FROM %1").arg(delimit(tablename)));
    addWhereClause(where, sqlargs);
    QSqlQuery query(db);
    return execQuery(query, sqlargs);
}


bool DbFunc::tableExists(const QSqlDatabase& db, const QString& tablename)
{
    SqlArgs sqlargs(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        {tablename}
    );
    return dbFetchInt(db, sqlargs) > 0;
}


QList<SqlitePragmaInfoField> DbFunc::getPragmaInfo(const QSqlDatabase& db,
                                              const QString& tablename)
{
    QString sql = QString("PRAGMA table_info(%1)").arg(delimit(tablename));
    QSqlQuery query(db);
    if (!execQuery(query, sql)) {
        UiFunc::stopApp("DbFunc::getPragmaInfo: PRAGMA table_info failed for "
                        "table " + tablename);
    }
    QList<SqlitePragmaInfoField> infolist;
    while (query.next()) {
        SqlitePragmaInfoField fieldinfo;
        fieldinfo.cid = query.value(0).toInt();  // column ID
        fieldinfo.name = query.value(1).toString();
        fieldinfo.type = query.value(2).toString();
        fieldinfo.notnull = query.value(3).toBool();
        fieldinfo.dflt_value = query.value(4);
        fieldinfo.pk = query.value(5).toBool();
        infolist.append(fieldinfo);
    }
    return infolist;
}


QStringList DbFunc::fieldNamesFromPragmaInfo(
        const QList<SqlitePragmaInfoField>& infolist,
        bool delimited)
{
    QStringList fieldnames;
    const int size = infolist.size();
    for (int i = 0; i < size; ++i) {
        QString name = infolist.at(i).name;
        if (delimited) {
            name = delimit(name);
        }
        fieldnames.append(name);
    }
    return fieldnames;
}


QStringList DbFunc::getFieldNames(const QSqlDatabase& db,
                                 const QString& tablename)
{
    QList<SqlitePragmaInfoField> infolist = getPragmaInfo(db, tablename);
    return fieldNamesFromPragmaInfo(infolist);
}


QString DbFunc::makeCreationSqlFromPragmaInfo(
        const QString& tablename,
        const QList<SqlitePragmaInfoField>& infolist)
{
    QStringList fieldspecs;
    const int size = infolist.size();
    for (int i = 0; i < size; ++i) {
        const SqlitePragmaInfoField& info = infolist.at(i);
        QStringList elements;
        elements.append(delimit(info.name));
        elements.append(info.type);
        if (info.notnull) {
            elements.append("NOT NULL");
        }
        if (!info.dflt_value.isNull()) {
            elements.append("DEFAULT " + info.dflt_value.toString());
            // default value already delimited by SQLite
        }
        if (info.pk) {
            elements.append("PRIMARY KEY");
        }
        fieldspecs.append(elements.join(" "));
    }
    return QString("CREATE TABLE IF NOT EXISTS %1 (%2)").arg(
        delimit(tablename), fieldspecs.join(", "));
}


QString DbFunc::dbTableDefinitionSql(const QSqlDatabase& db,
                                     const QString& tablename)
{
    QString sql = "SELECT sql FROM sqlite_master WHERE tbl_name=?";
    ArgList args({tablename});
    return dbFetchFirstValue(db, sql, args).toString();
}


bool DbFunc::createIndex(const QSqlDatabase& db, const QString& indexname,
                         const QString& tablename, QStringList fieldnames)
{
    if (!tableExists(db, tablename)) {
        qWarning() << "WARNING: ignoring createIndex for non-existent table:"
                   << tablename;
        return false;
    }
    for (int i = 0; i < fieldnames.size(); ++i) {
        fieldnames[i] = delimit(fieldnames[i]);
    }
    QString sql = QString("CREATE INDEX IF NOT EXISTS %1 ON %2 (%3)").arg(
        delimit(indexname), delimit(tablename), fieldnames.join(""));
    return exec(db, sql);
}


void DbFunc::renameColumns(const QSqlDatabase& db, QString tablename,
                           const QList<QPair<QString, QString>>& from_to,
                           const QString& tempsuffix)
{
    if (!tableExists(db, tablename)) {
        qWarning() << "WARNING: ignoring renameColumns for non-existent table:"
                   << tablename;
        return;
    }
    QString creation_sql = dbTableDefinitionSql(db, tablename);
    QStringList old_fieldnames = getFieldNames(db, tablename);
    QStringList new_fieldnames = old_fieldnames;
    QString dummytable = tablename + tempsuffix;
    if (tableExists(db, dummytable)) {
        UiFunc::stopApp("DbFunc::renameColumns: temporary table exists: " +
                        dummytable);
    }
    int n_changes = 0;
    for (int i = 0; i < from_to.size(); ++i) {  // For each rename...
        QString from = from_to.at(i).first;
        QString to = from_to.at(i).second;
        if (from == to) {
            continue;
        }
        // Check the source is valid
        if (!old_fieldnames.contains(from)) {
            UiFunc::stopApp("DbFunc::renameColumns: 'from' field doesn't "
                            "exist: " + tablename + "." + from);
        }
        // Check the destination doesn't exist already
        if (new_fieldnames.contains(to)) {
            UiFunc::stopApp(
                "DbFunc::renameColumns: destination field already exists (or "
                "attempt to rename two columns to the same name): " +
                tablename + "." + to);
        }
        // Rename the fieldname in the new_fieldnames list, and in the SQL
        new_fieldnames[new_fieldnames.indexOf(from)] = to;
        creation_sql.replace(delimit(from), delimit(to));
        ++n_changes;
    }
    if (n_changes == 0) {
        qDebug() << "renameColumns: nothing to do:" << tablename;
        return;
    }
    qDebug() << Q_FUNC_INFO;
    qDebug() << "- table:" << tablename;
    qDebug() << "- from_to:" << from_to;
    qDebug() << "- old_fieldnames:" << old_fieldnames;
    qDebug() << "- new_fieldnames:" << new_fieldnames;
    // Delimit everything
    QString delimited_tablename = delimit(tablename);
    QString delimited_dummytable = delimit(dummytable);
    for (int i = 0; i < old_fieldnames.size(); ++i) {
        old_fieldnames[i] = delimit(old_fieldnames[i]);
        new_fieldnames[i] = delimit(new_fieldnames[i]);
    }
    exec(db, "BEGIN TRANSACTION");
    exec(db, QString("ALTER TABLE %1 RENAME TO %2").arg(delimited_tablename,
                                                        delimited_dummytable));
    // Make a new, clean table:
    exec(db, creation_sql);
    // Copy the data across:
    exec(db, QString("INSERT INTO %1 (%2) SELECT %3 FROM %4").arg(
             delimited_tablename,
             new_fieldnames.join(","),
             old_fieldnames.join(","),
             delimited_dummytable));
    // Drop the temporary table:
    exec(db, QString("DROP TABLE %1").arg(delimited_dummytable));
    commit(db);
}


void DbFunc::renameTable(const QSqlDatabase& db, const QString& from,
                         const QString& to)
{
    if (!tableExists(db, from)) {
        qWarning() << Q_FUNC_INFO
                   << "WARNING: ignoring renameTable for non-existent table:"
                   << from;
        return;
    }
    if (tableExists(db, to)) {
        UiFunc::stopApp("DbFunc::renameTable: destination table already "
                        "exists: " + to);
    }
    // http://stackoverflow.com/questions/426495
    exec(db, QString("ALTER TABLE %1 RENAME TO %2").arg(from, to));
    // don't COMMIT (error: "cannot commit - no transaction is active")
}


void DbFunc::changeColumnTypes(const QSqlDatabase& db,
                               const QString& tablename,
                               const QList<QPair<QString, QString>>& changes,
                               const QString& tempsuffix)
{
    // changes: pairs <fieldname, newtype>
    if (!tableExists(db, tablename)) {
        qWarning() << "WARNING: ignoring changeColumnTypes for non-existent "
                      "table:" << tablename;
        return;
    }
    QString dummytable = tablename + tempsuffix;
    if (tableExists(db, dummytable)) {
        UiFunc::stopApp("DbFunc::changeColumnTypes: temporary table exists: " +
                        dummytable);
    }
    QList<SqlitePragmaInfoField> infolist = getPragmaInfo(db, tablename);
    qDebug() << "changeColumnTypes";
    qDebug() << "- pragma info:" << infolist;
    qDebug() << "- changes:" << changes;
    int n_changes = 0;
    for (int i = 0; i < changes.size(); ++i) {
        QString changefield = changes.at(i).first;
        for (int j = 0; i < infolist.size(); ++j) {
            SqlitePragmaInfoField& info = infolist[j];
            if (changefield.compare(info.name, Qt::CaseInsensitive) == 0) {
                QString newtype = changes.at(i).second;
                info.type = newtype;
                ++n_changes;
            }
        }
    }
    if (n_changes == 0) {
        qDebug() << "... nothing to do";
        return;
    }
    QString creation_sql = makeCreationSqlFromPragmaInfo(tablename, infolist);
    QString fieldnames = fieldNamesFromPragmaInfo(infolist, true).join(",");
    QString delimited_tablename = delimit(tablename);
    QString delimited_dummytable = delimit(dummytable);
    exec(db, "BEGIN TRANSACTION");
    exec(db, QString("ALTER TABLE %1 RENAME TO %2").arg(delimited_tablename,
                                                        delimited_dummytable));
    exec(db, creation_sql);  // make a new clean table
    exec(db, QString("INSERT INTO %1 (%2) SELECT %3 FROM %4").arg(
         delimited_tablename,
         fieldnames,
         fieldnames,
         delimited_dummytable));
    exec(db, QString("DROP TABLE %1").arg(delimited_dummytable));
    commit(db);
}


QString DbFunc::sqlCreateTable(const QString& tablename,
                               const QList<Field>& fieldlist)
{
    QStringList coldefs;
    for (int i = 0; i < fieldlist.size(); ++i) {
        const Field& field = fieldlist.at(i);
        QString coltype = field.sqlColumnDef();
        coldefs << QString("%1 %2").arg(delimit(field.name()), coltype);
    }
    QString sql = QString("CREATE TABLE IF NOT EXISTS %1 (%2)").arg(
        delimit(tablename), coldefs.join(", "));
    return sql;
}


void DbFunc::createTable(const QSqlDatabase& db, const QString& tablename,
                         const QList<Field>& fieldlist,
                         const QString& tempsuffix)
{
    QString creation_sql = sqlCreateTable(tablename, fieldlist);
    if (!tableExists(db, tablename)) {
        // Create table from scratch.
        exec(db, creation_sql);
        return;
    }

    // Otherwise, it's a bit more complex...

    // 1. Create a list of plans. Start with the fields we want, which we
    //    will add (unless later it turns out they exist already).
    QList<FieldCreationPlan> planlist;
    QStringList goodfieldlist;
    for (int i = 0; i < fieldlist.size(); ++i) {
        const Field& field = fieldlist.at(i);
        FieldCreationPlan p;
        p.name = field.name();
        p.intended_field = &field;
        p.add = true;
        planlist.append(p);
        goodfieldlist.append(delimit(p.name));
    }

    // 2. Fetch a list of existing fields.
    // - If any are in our "desired" list, and we didn't know they were in
    //   the database, don't add them (but maybe change them if we want them
    //   to have a different type).
    // - If they're not in our "desired" list, then they're superfluous, so
    //   aim to drop them.
    QList<SqlitePragmaInfoField> infolist = getPragmaInfo(db, tablename);
    for (int i = 0; i < infolist.size(); ++i) {
        const SqlitePragmaInfoField& info = infolist.at(i);
        bool existing_is_superfluous = true;
        for (int j = 0; j < planlist.size(); ++j) {
            FieldCreationPlan& plan = planlist[j];
            const Field* intended_field = plan.intended_field;
            if (!intended_field) {
                // This shouldn't happen!
                continue;
            }
            if (!plan.exists_in_db && intended_field->name() == info.name) {
                plan.exists_in_db = true;
                plan.add = false;
                plan.change = (
                    info.type != intended_field->sqlColumnType() ||
                    info.notnull != intended_field->allowsNull() ||
                    info.pk != intended_field->isPk()
                );
                plan.existing_type = info.type;
                plan.existing_not_null = info.notnull;
                existing_is_superfluous = false;
            }
        }
        if (existing_is_superfluous) {
            FieldCreationPlan plan;
            plan.name = info.name;
            plan.exists_in_db = true;
            plan.existing_type = info.type;
            plan.drop = true;
            planlist.append(plan);
        }
    }

    // 3. For any fields that require adding: add them.
    //    For any that require dropping or altering, make a note for the
    //    complex step.
    bool drop_or_change_mods_required = false;
    for (int i = 0; i < planlist.size(); ++i) {
        const FieldCreationPlan& plan = planlist.at(i);
        if (plan.add && plan.intended_field) {
            if (plan.intended_field->isPk()) {
                UiFunc::stopApp(QString(
                    "DbFunc::createTable: Cannot add a PRIMARY KEY column "
                    "(%s.%s)").arg(tablename, plan.name));
            }
            exec(db, QString("ALTER TABLE %1 ADD COLUMN %2 %3").arg(
                tablename,
                delimit(plan.name),
                plan.intended_field->sqlColumnDef()));
        }
        if (plan.drop || plan.change) {
            drop_or_change_mods_required = true;
        }
    }

    /*
    qDebug() << Q_FUNC_INFO
             << "tablename:" << tablename
             << "goodfieldlist:" << goodfieldlist
             << "infolist:" << infolist
             << "modifications_required:" << drop_or_change_mods_required
             << "plan:" << planlist;
    */

    if (!drop_or_change_mods_required) {
        qDebug() << "Table" << tablename
                 << "OK; no drop/change alteration required";
        return;
    }

    // 4. Implement drop/change modifications (via a temporary table).
    qDebug().nospace() << "Amendment plan for " << tablename
                       << ": " << planlist;
    // Deleting columns: http://www.sqlite.org/faq.html#q11
    // ... also http://stackoverflow.com/questions/8442147/
    // Basically, requires (a) copy data to temporary table; (b) drop original;
    // (c) create new; (d) copy back.
    // Or, another method: (a) rename table; (b) create new; (c) copy data
    // across; (d) drop temporary.
    // We deal with fields of incorrect type similarly (in this case, any
    // conversion occurs as we SELECT back the values into the new, proper
    // fields). Not sure it really is important, though:
    // http://sqlite.org/datatype3.html
    QString dummytable = tablename + tempsuffix;
    if (tableExists(db, dummytable)) {
        UiFunc::stopApp("DbFunc::createTable: temporary table exists: " +
                        dummytable);
    }
    QString delimited_tablename = delimit(tablename);
    QString delimited_dummytable = delimit(dummytable);
    QString goodfieldstring = goodfieldlist.join(",");
    exec(db, "BEGIN TRANSACTION");
    exec(db, QString("ALTER TABLE %1 RENAME TO %2").arg(delimited_tablename,
                                                        delimited_dummytable));
    exec(db, creation_sql);  // make a new clean table
    exec(db, QString("INSERT INTO %1 (%2) SELECT %3 FROM %4").arg(
         delimited_tablename,
         goodfieldstring,
         goodfieldstring,
         delimited_dummytable));
    exec(db, QString("DROP TABLE %1").arg(delimited_dummytable));
    commit(db);
}
