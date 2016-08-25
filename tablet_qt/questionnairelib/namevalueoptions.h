#pragma once
#include "namevaluepair.h"


class NameValueOptions
{
public:
    NameValueOptions();
    NameValueOptions(std::initializer_list<NameValuePair> options);
    void addItem(const NameValuePair& nvp);
    int size() const;
    const NameValuePair& at(int index) const;
    int indexFromName(const QString& name) const;
    int indexFromValue(const QVariant& value) const;
    void validateOrDie();
    bool validIndex(int index) const;
    void shuffle();
    QString name(int index) const;
    QVariant value(int index) const;
protected:
    QList<NameValuePair> m_options;
};
