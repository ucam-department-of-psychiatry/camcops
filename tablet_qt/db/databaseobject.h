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
#include <QDate>
#include <QDateTime>
#include <QMap>
#include <QString>
#include "common/aliases_camcops.h"
#include "common/aliases_qt.h"
#include "common/dbconst.h"
#include "db/field.h"
#include "db/sqlargs.h"
#include "db/whereconditions.h"

class CamcopsApp;
class NameValueOptions;
class QueryResult;


const QString DBOBJECT_DEFAULT_SEPARATOR = " = ";
const QString DBOBJECT_DEFAULT_SUFFIX = "";


class DatabaseObject : public QObject
{
    // A database object supporting a single integer PK field, and a default
    // modification timestamp field, extensible to add other fields.
    Q_OBJECT  // so our derived classes can be too
public:
    DatabaseObject(CamcopsApp& app,
                   DatabaseManager& db,
                   const QString& tablename,
                   const QString& pk_fieldname = dbconst::PK_FIELDNAME,
                   bool has_modification_timestamp = true,
                   bool has_creation_timestamp = false,
                   bool has_move_off_tablet_field = true,
                   bool triggers_need_upload = true);
    virtual ~DatabaseObject();

    // ========================================================================
    // Adding fields
    // ========================================================================

    void addField(const QString& fieldname,
                  QVariant::Type type,
                  bool mandatory = false,
                  bool unique = false,
                  bool pk = false,
                  const QVariant& default_value = QVariant());
    void addField(const QString& fieldname,
                  const QString& type_name,
                  bool mandatory = false,
                  bool unique = false,
                  bool pk = false,
                  const QVariant& default_value = QVariant());
    void addField(const Field& field);
    void addFields(const QStringList& fieldnames, QVariant::Type type,
                   bool mandatory = false);
    bool hasField(const QString& fieldname) const;
    QStringList fieldnames() const;

    // ========================================================================
    // Field access
    // ========================================================================

    bool setValue(const QString& fieldname, const QVariant& value,
                  bool touch_record = true);  // returns: changed?
    bool setValue(const QString& fieldname, const QVector<int>& value,
                  bool touch_record = true);  // returns: changed?
    bool setValue(const QString& fieldname, const QStringList& value,
                  bool touch_record = true);  // returns: changed?
    void addToValueInt(const QString& fieldname, int increment);

    QVariant value(const QString& fieldname) const;

    QString prettyValue(const QString& fieldname, int dp = -1) const;
    bool valueIsNull(const QString& fieldname) const;
    bool valueIsFalseNotNull(const QString& fieldname) const;
    bool valueIsNullOrEmpty(const QString& fieldname) const;

    bool valueBool(const QString& fieldname) const;
    int valueInt(const QString& fieldname) const;
    qlonglong valueLongLong(const QString& fieldname) const;
    qulonglong valueULongLong(const QString& fieldname) const;
    double valueDouble(const QString& fieldname) const;
    QDateTime valueDateTime(const QString& fieldname) const;
    QDate valueDate(const QString& fieldname) const;
    QByteArray valueByteArray(const QString& fieldname) const;
    QString valueString(const QString& fieldname) const;
    QStringList valueStringList(const QString& fieldname) const;
    QChar valueQChar(const QString& fieldname) const;
    char valueLatin1Char(const QString& fieldname) const;
    QVector<int> valueVectorInt(const QString& fieldname) const;

    QVector<QVariant> values(const QStringList& fieldnames) const;

    FieldRefPtr fieldRef(const QString& fieldname,
                         bool mandatory = true,
                         bool autosave = true,
                         bool blob = false);
    BlobFieldRefPtr blobFieldRef(const QString& fieldname, bool mandatory);

    // Low-level field access (for internal use only)
protected:
    Field& getField(const QString& fieldname);

    // ========================================================================
    // Whole-object summary
    // ========================================================================

public:
    QString fieldSummary(
            const QString& fieldname,
            const QString& altname = "",
            const QString& separator = DBOBJECT_DEFAULT_SEPARATOR,
            const QString& suffix = DBOBJECT_DEFAULT_SUFFIX) const;
    QString fieldSummaryYesNo(
            const QString& fieldname,
            const QString& altname,
            const QString& separator = DBOBJECT_DEFAULT_SEPARATOR,
            const QString& suffix = DBOBJECT_DEFAULT_SUFFIX) const;
    QString fieldSummaryYesNoNull(
            const QString& fieldname,
            const QString& altname,
            const QString& separator = DBOBJECT_DEFAULT_SEPARATOR,
            const QString& suffix = DBOBJECT_DEFAULT_SUFFIX) const;
    QString fieldSummaryYesNoUnknown(
            const QString& fieldname,
            const QString& altname,
            const QString& separator = DBOBJECT_DEFAULT_SEPARATOR,
            const QString& suffix = DBOBJECT_DEFAULT_SUFFIX) const;
    QString fieldSummaryTrueFalseUnknown(
            const QString& fieldname,
            const QString& altname,
            const QString& separator = DBOBJECT_DEFAULT_SEPARATOR,
            const QString& suffix = DBOBJECT_DEFAULT_SUFFIX) const;

    QString fieldSummaryNameValueOptions(
            const QString& fieldname,
            const NameValueOptions& options,
            const QString& altname,
            const QString& separator = DBOBJECT_DEFAULT_SEPARATOR,
            const QString& suffix = DBOBJECT_DEFAULT_SUFFIX) const;
    QStringList recordSummaryLines(
            const QString& separator = DBOBJECT_DEFAULT_SEPARATOR,
            const QString& suffix = DBOBJECT_DEFAULT_SUFFIX) const;
    QString recordSummaryString(
            const QString& separator = DBOBJECT_DEFAULT_SEPARATOR,
            const QString& suffix = DBOBJECT_DEFAULT_SUFFIX) const;
    QString recordSummaryCSVString(
            const QString& equals_separator = DBOBJECT_DEFAULT_SEPARATOR,
            const QString& comma_separator = ", ") const;

    // ========================================================================
    // Loading, saving
    // ========================================================================

    virtual bool load(int pk);
    virtual bool load(const QString& fieldname, const QVariant& where_value);
    virtual bool load(const WhereConditions& where);
    virtual SqlArgs fetchQuerySql(const WhereConditions& where = WhereConditions(),
                                  const OrderBy& order_by = OrderBy());
    virtual void setFromQuery(const QueryResult& query_result,
                              int row,
                              bool order_matches_fetchquery = false);
    virtual bool save();
    void saveWithoutKeepingPk();  // special shortcut for background INSERT
    void nullify();  // set all fields to null values
    bool isPkNull() const;
    void touch(bool only_if_unset = false);
    void setAllDirty();

    // ========================================================================
    // Batch operations
    // ========================================================================

    QVector<int> getAllPKs() const;

    // ========================================================================
    // Deleting
    // ========================================================================

    virtual void deleteFromDatabase();

    // ========================================================================
    // Debugging:
    // ========================================================================

    void requireField(const QString& fieldname) const;

    // ========================================================================
    // Special field access
    // ========================================================================

    bool shouldMoveOffTablet() const;
    void setMoveOffTablet(bool move_off);
    void toggleMoveOffTablet();

    // ========================================================================
    // DDL
    // ========================================================================

    QString sqlCreateTable() const;
    QString tablename() const;
    QString pkname() const;
    QVariant pkvalue() const;
    int pkvalueInt() const;
    void makeTable();

    // For making BLOBs share the same database:
    DatabaseManager& database() const;

    // ========================================================================
    // Internals: ancillary management
    // ========================================================================
protected:
    void loadAllAncillary();
    virtual void loadAllAncillary(int pk);
    virtual QVector<DatabaseObjectPtr> getAllAncillary() const;
    virtual QVector<DatabaseObjectPtr> getAncillarySpecimens() const;

    // ========================================================================
    // Internals: saving, etc.
    // ========================================================================
protected:
    bool saveInsert(bool read_pk_from_database = true);
    bool saveUpdate();
    void clearAllDirty();
    bool anyDirty() const;
    QStringList fieldnamesMapOrder() const;
    QVector<Field> fieldsOrdered() const;

protected:
    CamcopsApp& m_app;
    DatabaseManager& m_db;
    QString m_tablename;  // also used as key for extra strings
    QString m_pk_fieldname;
    bool m_has_modification_timestamp;
    bool m_has_move_off_tablet_field;
    bool m_triggers_need_upload;
    using MapType = QMap<QString, Field>;
    using MapIteratorType = QMapIterator<QString, Field>;
    using MutableMapIteratorType = QMutableMapIterator<QString, Field>;
    MapType m_record;  // Note: no intrinsic ordering to fields from this. So:
    QStringList m_ordered_fieldnames;
    QMap<QString, FieldRefPtr> m_fieldrefs;
    bool m_exists_in_db;

public:
    friend QDebug operator<<(QDebug debug, const DatabaseObject& d);
};
