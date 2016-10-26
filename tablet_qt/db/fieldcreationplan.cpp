#include "db/fieldcreationplan.h"
#include "db/field.h"


QDebug operator<<(QDebug debug, const FieldCreationPlan& plan)
{
    debug.nospace()
        << "FieldCreationPlan(name=" << plan.name
        << ", intended base type=";
    if (plan.intended_field) {
        debug.nospace() << plan.intended_field->sqlColumnType();
    } else {
        debug.nospace() << "<none>";
    }
    debug.nospace()
        << ", intended full def=";
    if (plan.intended_field) {
        debug.nospace() << plan.intended_field->sqlColumnDef();
    } else {
        debug.nospace() << "<none>";
    }
    debug.nospace()
        << ", exists_in_db=" << plan.exists_in_db
        << ", existing_type=" << plan.existing_type
        << ", existing_not_null=" << plan.existing_not_null
        << ", add=" << plan.add
        << ", drop=" << plan.drop
        << ", change=" << plan.change << ")";
    return debug;
}


