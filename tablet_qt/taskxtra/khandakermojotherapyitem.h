/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#pragma once
#include <QString>

#include "db/databaseobject.h"

class KhandakerMojoTherapyItem : public DatabaseObject
{
    Q_OBJECT

public:
    KhandakerMojoTherapyItem(
        CamcopsApp& app,
        DatabaseManager& db,
        int load_pk = dbconst::NONEXISTENT_PK
    );
    KhandakerMojoTherapyItem(
        int owner_fk, CamcopsApp& app, DatabaseManager& db
    );
    void setSeqnum(int seqnum);
    bool isComplete() const;
    bool isEmpty() const;

public:
    static const QString KHANDAKER2MOJOTHERAPYITEM_TABLENAME;
    static const QString FN_FK_NAME;
    static const QString FN_SEQNUM;
    static const QString FN_THERAPY;
    static const QString FN_FREQUENCY;
    static const QString FN_SESSIONS_COMPLETED;
    static const QString FN_SESSIONS_PLANNED;
    static const QString FN_INDICATION;
    static const QString FN_RESPONSE;
    static const QStringList TABLE_FIELDNAMES;

protected:
};
