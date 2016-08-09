#define DEBUG_SQL_QUERY
#define DEBUG_SQL_RESULT

#include "dbfunc.h"
#include <QDebug>
#include <QDir>
#include <QSqlError>
#include <QSqlQuery>
#include <QSqlRecord>
#include <QStandardPaths>
#include "lib/uifunc.h"


QDebug operator<<(QDebug debug, const SqlitePragmaInfo& info)
{
    debug.nospace()
        << "SqlitePragmaInfo(cid=" << info.cid
        << ", name=" << info.name
        << ", type=" << info.type
        << ", notnull=" << info.notnull
        << ", dflt_value=" << info.dflt_value
        << ", pk=" << info.pk << ")";
    return debug;
}


QDebug operator<<(QDebug debug, const FieldCreationPlan& plan)
{
    debug.nospace()
        << "FieldCreationPlan(name=" << plan.name
        << ", intended=";
    if (plan.intended_field) {
        debug.nospace() << plan.intended_field->sqlColumnDef();
    } else {
        debug.nospace() << "<none>";
    }
    debug.nospace()
        << ", existsInDb=" << plan.exists_in_db
        << ", existingType=" << plan.existing_type
        << ", add=" << plan.add
        << ", drop=" << plan.drop
        << ", change=" << plan.change << ")";
    return debug;
}


void openDatabaseOrDie(QSqlDatabase& db, const QString& filename)
{
    // Opens a database.
    QString dir = QStandardPaths::standardLocations(
        QStandardPaths::AppDataLocation).first();
    if (!QDir(dir).exists()) {
        if (QDir().mkdir(dir)) {
            qDebug() << "Made directory:" << dir;
        } else {
            stopApp("Failed to make directory: " + dir);
        }
    }
    // http://stackoverflow.com/questions/3541529/is-there-qpathcombine-in-qt4
    QString fullpath = QDir::cleanPath(dir + "/" + filename);
    db.setDatabaseName(fullpath);
    if (db.open()) {
        qDebug() << "Opened database:" << fullpath;
    } else {
        QSqlError error = db.lastError();
        qDebug() << "Last database error:" << error;
        qDebug() << "Database:" << db;
        QString errmsg = QString(
            "Error: connection to database failed. Database = %1; "
            "error number = %2; error text = %3"
        ).arg(fullpath, QString::number(error.number()), error.text());
        stopApp(errmsg);
    }
}


QString delimit(const QString& fieldname)
{
    // Delimts a table or fieldname, by ANSI SQL standards.

    // http://www.sqlite.org/lang_keywords.html
    // http://stackoverflow.com/questions/2901453/sql-standard-to-escape-column-names
    // You must delimit anything with funny characters or any keyword,
    // and the list of potential keywords is long, so just delimit everything.
    return "\"" + fieldname + "\"";
}


void addArgs(QSqlQuery& query, const QList<QVariant>& args)
{
    // Adds arguments to a query from a QList.
    const int size = args.size();
    for (int i = 0; i < size; ++i) {
        query.addBindValue(args.at(i), QSql::In);
    }
}


bool execQuery(QSqlQuery& query, const QString& sql,
                const QList<QVariant>& args)
{
    // Executes an existing query (in place) with the supplied SQL/args.
    query.prepare(sql);
    addArgs(query, args);

#ifdef DEBUG_SQL_QUERY
    qDebug() << "Executing:" << qPrintable(sql);
    qDebug() << "... args:" << args;
#endif

#ifdef DEBUG_SQL_RESULT
    bool success = query.exec();
    if (query.isSelect() && !query.isForwardOnly()) {
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
                debug << rec.fieldName(col) << "=" << query.value(col);
            }
            ++row;
        }
        query.seek(QSql::BeforeFirstRow);  // the original starting position
    }
    return success;
#else
    return query.exec();
#endif
    // The return value is boolean (success?).
    // Use query.next() to iterate through a result set; see
    // http://doc.qt.io/qt-4.8/sql-sqlstatements.html
}


bool execQuery(QSqlQuery& query, const QString& sql)
{
    QList<QVariant> args;
    return execQuery(query, sql, args);
}


bool exec(QSqlDatabase& db, const QString& sql, const QList<QVariant>& args)
{
    // Executes a new query and returns success.
    QSqlQuery query(db);
    return execQuery(query, sql, args);
}


// http://stackoverflow.com/questions/2816293/passing-optional-parameter-by-reference-in-c
bool exec(QSqlDatabase& db, const QString& sql)
{
    QList<QVariant> args;
    return exec(db, sql, args);
}


QVariant dbFetchFirstValue(QSqlDatabase& db, const QString& sql,
                              const QList<QVariant>& args)
{
    QSqlQuery query(db);
    execQuery(query, sql, args);
    if (!query.next()) {
        return QVariant();
    }
    return query.value(0);
}


QVariant dbFetchFirstValue(QSqlDatabase& db, const QString& sql)
{
    QList<QVariant> args;
    return dbFetchFirstValue(db, sql, args);
}


int dbFetchInt(QSqlDatabase& db, const QString& sql,
                 const QList<QVariant>& args,
                 int failureDefault)
{
    // Executes the specified SQL/args and returns the integer value of the
    // first field of the first result (or failureDefault).
    QSqlQuery query(db);
    execQuery(query, sql, args);
    if (!query.next()) {
        return failureDefault;
    }
    return query.value(0).toInt();
}


int dbFetchInt(QSqlDatabase& db, const QString& sql,
                 int failureDefault)
{
    QList<QVariant> args;
    return dbFetchInt(db, sql, args, failureDefault);
}


bool tableExists(QSqlDatabase& db, const QString& tablename)
{
    QString sql = "SELECT COUNT(*) FROM sqlite_master "
                  "WHERE type='table' AND name=?";
    QList<QVariant> args({tablename});
    return dbFetchInt(db, sql, args) > 0;
}


QList<SqlitePragmaInfo> getPragmaInfo(QSqlDatabase& db,
                                      const QString& tablename)
{
    QString sql = QString("PRAGMA table_info(%1)").arg(delimit(tablename));
    QSqlQuery query(db);
    if (!execQuery(query, sql)) {
        stopApp("PRAGMA table_info failed for table " + tablename);
    }
    QList<SqlitePragmaInfo> infolist;
    while (query.next()) {
        SqlitePragmaInfo fieldinfo;
        fieldinfo.cid = query.value(0).toInt();
        fieldinfo.name = query.value(1).toString();
        fieldinfo.type = query.value(2).toString();
        fieldinfo.notnull = query.value(3).toBool();
        fieldinfo.dflt_value = query.value(4);
        fieldinfo.pk = query.value(5).toBool();
        infolist.append(fieldinfo);
    }
    return infolist;
}


QStringList fieldNamesFromPragmaInfo(const QList<SqlitePragmaInfo>& infolist,
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


QStringList dbFieldNames(QSqlDatabase& db, const QString& tablename)
{
    QList<SqlitePragmaInfo> infolist = getPragmaInfo(db, tablename);
    return fieldNamesFromPragmaInfo(infolist);
}


QString makeCreationSqlFromPragmaInfo(const QString& tablename,
                                      const QList<SqlitePragmaInfo>& infolist)
{
    QStringList fieldspecs;
    const int size = infolist.size();
    for (int i = 0; i < size; ++i) {
        const SqlitePragmaInfo& info = infolist.at(i);
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


QString dbTableDefinitionSql(QSqlDatabase& db, const QString& tablename)
{
    QString sql = "SELECT sql FROM sqlite_master WHERE tbl_name=?";
    QList<QVariant> args({tablename});
    return dbFetchFirstValue(db, sql, args).toString();
}


bool createIndex(QSqlDatabase& db, const QString& indexname,
                 const QString& tablename, QStringList fieldnames)
{
    if (!tableExists(db, tablename)) {
        qDebug() << "WARNING: ignoring createIndex for non-existent table:"
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


void renameColumns(QSqlDatabase& db, QString tablename,
                   const QList<QPair<QString, QString>>& from_to,
                   QString tempsuffix)
{
    if (!tableExists(db, tablename)) {
        qDebug() << "WARNING: ignoring renameColumns for non-existent table:"
                 << tablename;
        return;
    }
    QString creation_sql = dbTableDefinitionSql(db, tablename);
    QStringList old_fieldnames = dbFieldNames(db, tablename);
    QStringList new_fieldnames = old_fieldnames;
    QString dummytable = tablename + tempsuffix;
    if (tableExists(db, dummytable)) {
        stopApp("renameColumns: temporary table exists: " + dummytable);
    }
    int n_changes = 0;
    for (int i; i < from_to.size(); ++i) {  // For each rename...
        QString from = from_to.at(i).first;
        QString to = from_to.at(i).second;
        if (from == to) {
            continue;
        }
        // Check the source is valid
        if (!old_fieldnames.contains(from)) {
            stopApp("renameColumns: 'from' field doesn't exist: " +
                    tablename + "." + from);
        }
        // Check the destination doesn't exist already
        if (new_fieldnames.contains(to)) {
            stopApp("renameColumns: destination field already exists (or "
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
    qDebug() << "renameColumns";
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
    exec(db, "COMMIT");
}


void renameTable(QSqlDatabase& db, const QString& from, const QString& to)
{
    if (!tableExists(db, from)) {
        qDebug() << "WARNING: ignoring renameTable for non-existent table:"
                 << from;
        return;
    }
    if (tableExists(db, to)) {
        stopApp("renameTable: destination table already exists: " + to);
    }
    // http://stackoverflow.com/questions/426495
    exec(db, QString("ALTER TABLE %1 RENAME TO %2").arg(from, to));
    // don't COMMIT (error: "cannot commit - no transaction is active")
}


void changeColumnTypes(QSqlDatabase& db, const QString& tablename,
                       const QList<QPair<QString, QString>>& changes,
                       QString tempsuffix)
{
    // changes: pairs <fieldname, newtype>
    if (!tableExists(db, tablename)) {
        qDebug() << "WARNING: ignoring changeColumnTypes for "
                    "non-existent table:" << tablename;
        return;
    }
    QString dummytable = tablename + tempsuffix;
    if (tableExists(db, dummytable)) {
        stopApp("renameColumns: temporary table exists: " + dummytable);
    }
    QList<SqlitePragmaInfo> infolist = getPragmaInfo(db, tablename);
    qDebug() << "changeColumnTypes";
    qDebug() << "- pragma info:" << infolist;
    qDebug() << "- changes:" << changes;
    int n_changes = 0;
    for (int i = 0; i < changes.size(); ++i) {
        QString changefield = changes.at(i).first;
        for (int j = 0; i < infolist.size(); ++j) {
            SqlitePragmaInfo& info = infolist[j];
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
    exec(db, "COMMIT");
}


QString sqlCreateTable(const QString& tablename, const QList<Field>& fieldlist)
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


void createTable(QSqlDatabase& db, const QString& tablename,
                 const QList<Field>& fieldlist, QString tempsuffix)
{
    QString creation_sql = sqlCreateTable(tablename, fieldlist);
    if (!tableExists(db, tablename)) {
        // Create table from scratch.
        exec(db, creation_sql);
        return;
    }
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
    QList<SqlitePragmaInfo> infolist = getPragmaInfo(db, tablename);
    // Otherwise, it's a bit more complex.
    for (int i = 0; i < infolist.size(); ++i) {
        const SqlitePragmaInfo& info = infolist.at(i);
        bool existing_is_superfluous = true;
        for (int j = 0; j < planlist.size(); ++j) {
            FieldCreationPlan& plan = planlist[j];
            if (!plan.exists_in_db && plan.intended_field->name() == info.name) {
                plan.exists_in_db = true;
                plan.add = false;
                plan.change = info.type != plan.intended_field->sqlColumnType();
                plan.existing_type = info.type;
                existing_is_superfluous = false;
            }
        }
        if (existing_is_superfluous) {
            FieldCreationPlan plan;
            plan.name = info.name;
            plan.exists_in_db = true;
            plan.existing_type = info.type;
            plan.drop = true;
        }
    }
    bool modifications_required = false;
    for (int i = 0; i < planlist.size(); ++i) {
        const FieldCreationPlan& plan = planlist.at(i);
        if (plan.add && plan.intended_field) {
            if (plan.intended_field->isPk()) {
                stopApp(QString("Cannot add a PRIMARY KEY column (%s.%s)").arg(
                    tablename, plan.name));
            }
            exec(db, QString("ALTER TABLE %1 ADD COLUMN %2 %3").arg(
                tablename,
                delimit(plan.name),
                plan.intended_field->sqlColumnDef()));
        }
        if (plan.drop || plan.change) {
            modifications_required = true;
        }
    }
    if (!modifications_required) {
        return;
    }
    qDebug().nospace() << "createTable amendment plan for" << tablename
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
        stopApp("renameColumns: temporary table exists: " + dummytable);
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
    exec(db, "COMMIT");
}
