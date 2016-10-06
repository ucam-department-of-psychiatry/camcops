#pragma once
#include <QString>
class Field;


class FieldCreationPlan {
public:
    QString name;
    const Field* intended_field = nullptr;
    bool exists_in_db = false;
    QString existing_type;
    bool existing_not_null = false;
    bool add = false;
    bool drop = false;
    bool change = false;
public:
    friend QDebug operator<<(QDebug debug, const FieldCreationPlan& plan);
};
