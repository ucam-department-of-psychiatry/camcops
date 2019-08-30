/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

#include "khandaker2mojotherapyitem.h"

const QString Khandaker2MojoTherapyItem::KHANDAKER2MOJOTHERAPYITEM_TABLENAME("khandaker_2_mojotherapy_item");

const QString Khandaker2MojoTherapyItem::FN_FK_NAME("medicationtable_id");
const QString Khandaker2MojoTherapyItem::FN_SEQNUM("seqnum");
const QString Khandaker2MojoTherapyItem::FN_THERAPY("therapy");
const QString Khandaker2MojoTherapyItem::FN_FREQUENCY("frequency");
const QString Khandaker2MojoTherapyItem::FN_DURATION("duration");
const QString Khandaker2MojoTherapyItem::FN_INDICATION("indication");
const QString Khandaker2MojoTherapyItem::FN_RESPONSE("response");

const QStringList Khandaker2MojoTherapyItem::TABLE_FIELDNAMES{
    Khandaker2MojoTherapyItem::FN_THERAPY,
    Khandaker2MojoTherapyItem::FN_FREQUENCY,
    Khandaker2MojoTherapyItem::FN_DURATION,
    Khandaker2MojoTherapyItem::FN_INDICATION,
    Khandaker2MojoTherapyItem::FN_RESPONSE,
};


Khandaker2MojoTherapyItem::Khandaker2MojoTherapyItem(
    CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    DatabaseObject(app, db, KHANDAKER2MOJOTHERAPYITEM_TABLENAME,
                   dbconst::PK_FIELDNAME,  // pk_fieldname
                   true,  // has_modification_timestamp
                   false,  // has_creation_timestamp
                   true,  // has_move_off_tablet_field
                   true)  // triggers_need_upload
{
    addField(FN_FK_NAME, QVariant::Int);
    addField(FN_SEQNUM, QVariant::Int);
    addField(FN_THERAPY, QVariant::String);
    addField(FN_FREQUENCY, QVariant::Int);
    addField(FN_DURATION, QVariant::Int);
    addField(FN_INDICATION, QVariant::String);
    addField(FN_RESPONSE, QVariant::Int);

    load(load_pk);
}


Khandaker2MojoTherapyItem::Khandaker2MojoTherapyItem(
    const int owner_fk, CamcopsApp& app, DatabaseManager& db) :
    Khandaker2MojoTherapyItem(app, db)  // delegating constructor
{
    setValue(FN_FK_NAME, owner_fk);
}


void Khandaker2MojoTherapyItem::setSeqnum(const int seqnum)
{
    setValue(FN_SEQNUM, seqnum);
}


int Khandaker2MojoTherapyItem::seqnum() const
{
    return valueInt(FN_SEQNUM);
}


QString Khandaker2MojoTherapyItem::therapy() const
{
    return valueString(FN_THERAPY);
}

int Khandaker2MojoTherapyItem::frequency() const
{
    return valueInt(FN_FREQUENCY);

}

int Khandaker2MojoTherapyItem::duration() const
{
    return valueInt(FN_DURATION);
}

QString Khandaker2MojoTherapyItem::indication() const
{
    return valueString(FN_INDICATION);
}

int Khandaker2MojoTherapyItem::response() const
{
    return valueInt(FN_RESPONSE);
}

bool Khandaker2MojoTherapyItem::isComplete() const
{
    return noValuesNull(TABLE_FIELDNAMES);
}
