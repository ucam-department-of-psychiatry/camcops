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

#include "idnumdescription.h"
#include "db/databasemanager.h"

const QString IdNumDescription::IDNUMDESC_TABLENAME("idnum_descriptions");
const QString IdNumDescription::FN_IDNUM("idnum");
const QString FN_IDDESC("iddesc");
const QString FN_IDSHORTDESC("idshortdesc");


IdNumDescription::IdNumDescription(CamcopsApp& app, DatabaseManager& db,
                                   const int which_idnum) :
    DatabaseObject(app, db, IDNUMDESC_TABLENAME,
                   FN_IDNUM,  // pk
                   false, false, false, false)  // internal tables only
{
    addField(FN_IDDESC, QVariant::String);
    addField(FN_IDSHORTDESC, QVariant::String);

    m_exists = load(which_idnum);
    if (!m_exists) {
        // PK will have been nullified, but we want it
        setValue(FN_IDNUM, which_idnum);
    }
}


int IdNumDescription::whichIdNum() const
{
    return valueInt(FN_IDNUM);
}


bool IdNumDescription::exists() const
{
    return m_exists;
}


QString IdNumDescription::description() const
{
    return valueString(FN_IDDESC);
}


QString IdNumDescription::shortDescription() const
{
    return valueString(FN_IDSHORTDESC);
}


bool IdNumDescription::setDescriptions(const QString& desc,
                                       const QString& shortdesc)
{
    bool success = setValue(FN_IDDESC, desc);
    success = setValue(FN_IDSHORTDESC, shortdesc) && success;
    return success;
}


void IdNumDescription::deleteAllDescriptions()
{
    m_db.deleteFrom(IDNUMDESC_TABLENAME);
}


void IdNumDescription::makeIndexes()
{
    m_db.createIndex("_idx_idnumdesc_idnum",
                     IDNUMDESC_TABLENAME,
                     {FN_IDNUM});
}
