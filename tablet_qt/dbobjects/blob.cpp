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

#include "blob.h"
#include "db/dbfunc.h"

const QString Blob::TABLENAME("blobs");  // as per DBCONSTANTS.js

const QString Blob::SRC_TABLE_FIELDNAME("tablename");  // as per Blob.js
const QString Blob::SRC_PK_FIELDNAME("tablepk");  // as per Blob.js
const QString SRC_FIELD_FIELDNAME("fieldname");  // as per Blob.js
const QString FILENAME_FIELDNAME("filename");  // as per Blob.js
const QString BLOB_FIELDNAME("theblob"); // as per dbupload.js
// ... was a "virtual" field under Titanium and file-based BLOBs.


Blob::Blob(CamcopsApp& app,
           const QSqlDatabase& db,
           const QString& src_table,
           int src_pk,
           const QString& src_field) :
    DatabaseObject(app,
                   db,
                   TABLENAME,
                   dbconst::PK_FIELDNAME,
                   true,  // modification timestamp
                   false)  // creation timestamp
{
    // ------------------------------------------------------------------------
    // Define fields
    // ------------------------------------------------------------------------
    addField(SRC_TABLE_FIELDNAME, QVariant::String, true);
    addField(SRC_PK_FIELDNAME, QVariant::Int, true);
    addField(SRC_FIELD_FIELDNAME, QVariant::String, true);
    addField(FILENAME_FIELDNAME, QVariant::String, false);
    addField(BLOB_FIELDNAME, QVariant::ByteArray, false);

    // ------------------------------------------------------------------------
    // Load from database (or create/save), unless this is a specimen
    // ------------------------------------------------------------------------
    if (!src_table.isEmpty() && !src_field.isEmpty() && src_pk >= 0) {
        // Not a specimen; load, or set defaults and save
        WhereConditions where;
        where[SRC_TABLE_FIELDNAME] = src_table;
        where[SRC_PK_FIELDNAME] = src_pk;
        where[SRC_FIELD_FIELDNAME] = src_field;
        bool success = load(where);  // will load the BLOB, if present
        if (!success) {
            setValue(SRC_TABLE_FIELDNAME, src_table);
            setValue(SRC_PK_FIELDNAME, src_pk);
            setValue(SRC_FIELD_FIELDNAME, src_field);
            save();
        }
    }

    // We could extend DatabaseObject::makeTable to call subclasses for extra
    // index/constraint requirements. Specifically, they need to go into the
    // CREATE TABLE syntax for SQLite:
    //      http://www.sqlite.org/syntaxdiagrams.html#table-constraint
    // However, we can equally implement the constraint by not screwing up the
    // C++ code, which is perhaps simpler (because: if the database implements
    // the code, then duff C++ code has its bacon partly saved by the database,
    // but leaving a potentially ambiguous state from the C++ perspective when
    // insertion overwrites rather than creatng.

    m_filename_stem = QString("blob_%1_%2_%3").arg(src_table)
                                              .arg(src_pk)
                                              .arg(src_field);
    // ... as per Blob.js
}


Blob::~Blob()
{
}


bool Blob::setBlob(const QVariant& value, bool save_to_db,
                   const QString& extension_without_dot)
{
    bool changed_contents = setValue(BLOB_FIELDNAME, value);
    bool changed_filename = setValue(FILENAME_FIELDNAME,
             QString("%1.%2").arg(m_filename_stem).arg(extension_without_dot));
    if (save_to_db) {
        save();
    }
    return changed_contents || changed_filename;
}


QVariant Blob::blobVariant() const
{
    return value(BLOB_FIELDNAME);
}


QByteArray Blob::blobByteArray() const
{
    return valueByteArray(BLOB_FIELDNAME);
}


void Blob::makeIndexes()
{
    dbfunc::createIndex(m_db, "_idx_src_table_pk_field", TABLENAME, {
                            SRC_TABLE_FIELDNAME,
                            SRC_PK_FIELDNAME,
                            SRC_FIELD_FIELDNAME});
}
