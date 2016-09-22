#pragma once
#include <QString>


struct TaskMenuItem
{
    // Exists only to improve polymorphic constructor of MenuItem
public:
    TaskMenuItem(const QString& tablename) :
        tablename(tablename)
    {}
public:
    QString tablename;
};
