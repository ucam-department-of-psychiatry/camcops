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

#include "khandaker2mojomedicationitem.h"

const QString Khandaker2MojoMedicationItem::KHANDAKER2MOJOMEDICATIONITEM_TABLENAME("khandaker_2_mojomedication_item");

const QString Khandaker2MojoMedicationItem::FN_FK_NAME("medicationtable_id");
const QString Khandaker2MojoMedicationItem::FN_SEQNUM("seqnum");
const QString Khandaker2MojoMedicationItem::FN_MEDICATION_NAME("medication_name");
const QString Khandaker2MojoMedicationItem::FN_CHEMICAL_NAME("chemical_name");
const QString Khandaker2MojoMedicationItem::FN_DOSAGE("dosage");
const QString Khandaker2MojoMedicationItem::FN_FREQUENCY("frequency");
const QString Khandaker2MojoMedicationItem::FN_DURATION("duration");
const QString Khandaker2MojoMedicationItem::FN_INDICATION("indication");
const QString Khandaker2MojoMedicationItem::FN_RESPONSE("response");

const QStringList Khandaker2MojoMedicationItem::TABLE_FIELDNAMES{
    Khandaker2MojoMedicationItem::FN_MEDICATION_NAME,
    Khandaker2MojoMedicationItem::FN_CHEMICAL_NAME,
    Khandaker2MojoMedicationItem::FN_DOSAGE,
    Khandaker2MojoMedicationItem::FN_FREQUENCY,
    Khandaker2MojoMedicationItem::FN_DURATION,
    Khandaker2MojoMedicationItem::FN_INDICATION,
    Khandaker2MojoMedicationItem::FN_RESPONSE,
 };

Khandaker2MojoMedicationItem::Khandaker2MojoMedicationItem(
    CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    DatabaseObject(app, db, KHANDAKER2MOJOMEDICATIONITEM_TABLENAME,
                   dbconst::PK_FIELDNAME,  // pk_fieldname
                   true,  // has_modification_timestamp
                   false,  // has_creation_timestamp
                   true,  // has_move_off_tablet_field
                   true)  // triggers_need_upload
{
    addField(FN_FK_NAME, QVariant::Int);
    addField(FN_SEQNUM, QVariant::Int);
    addField(FN_MEDICATION_NAME, QVariant::String);
    addField(FN_CHEMICAL_NAME, QVariant::String);
    addField(FN_DOSAGE, QVariant::String);
    addField(FN_FREQUENCY, QVariant::String);
    addField(FN_DURATION, QVariant::Int);
    addField(FN_INDICATION, QVariant::String);
    addField(FN_RESPONSE, QVariant::Int);

    load(load_pk);
}


Khandaker2MojoMedicationItem::Khandaker2MojoMedicationItem(
    const int owner_fk, CamcopsApp& app, DatabaseManager& db) :
    Khandaker2MojoMedicationItem(app, db)  // delegating constructor
{
    setValue(FN_FK_NAME, owner_fk);
}


void Khandaker2MojoMedicationItem::setSeqnum(const int seqnum)
{
    setValue(FN_SEQNUM, seqnum);
}


void Khandaker2MojoMedicationItem::setChemicalName(
    const QString chemical_name)
{
    setValue(FN_CHEMICAL_NAME, chemical_name);
}

bool Khandaker2MojoMedicationItem::isComplete() const
{
    return noValuesNull(TABLE_FIELDNAMES);
}

bool Khandaker2MojoMedicationItem::isEmpty() const
{
    for (const QString& fieldname : TABLE_FIELDNAMES) {
        if (!valueIsNullOrEmpty(fieldname)) {
            return false;
        }
    }

    return true;
}
