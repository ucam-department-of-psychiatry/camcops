#include "taskmainrecord.h"

const QString PATIENT_FK_FIELDNAME = "patient_id";


TaskMainRecord::TaskMainRecord(const QString& tablename,
                               const QSqlDatabase db,
                               bool is_anonymous,
                               bool has_clinician,
                               bool has_respondent)
    : DatabaseObject(tablename, db, true, true)
{
    addField("when_created", QVariant::DateTime);
    addField("firstexit_is_finish", QVariant::Bool);
    addField("firstexit_is_abort", QVariant::Bool);
    addField("when_firstexit", QVariant::DateTime);
    Field editing_time_s("editing_time_s", QVariant::Double);
    editing_time_s.setDefaultValue(0.0);
    addField(editing_time_s);

    if (!is_anonymous) {
        addField(PATIENT_FK_FIELDNAME, QVariant::Int);
    }
    if (has_clinician) {
        addField("clinician_specialty", QVariant::String);
        addField("clinician_name", QVariant::String);
        addField("clinician_professional_registration", QVariant::String);
        addField("clinician_post", QVariant::String);
        addField("clinician_service", QVariant::String);
        addField("clinician_contact_details", QVariant::String);
    }
    if (has_respondent) {
        addField("respondent_name", QVariant::String);
        addField("respondent_relationship", QVariant::String);
    }
}
