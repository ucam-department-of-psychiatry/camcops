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

#pragma once
#include <QVector>
#include "questionnairelib/namevaluepair.h"


class NameValueOptions
{
/*
    Encapsulates a list of name/value pairs.

    Generally, we don't allow duplicate values.
    However, there are some circumstances when it's helpful, e.g. we are
    offering several wrong answers, and don't care which one is selected;
    such as

    Q. What is 2 + 2?
    a) One [-> score 0]
    b) Two [-> score 0]
    c) Three [-> score 0]
    d) Four [-> score 1]
    e) Five [-> score 0]

    You might think it'd be OK to support that situation. HOWEVER, it's not.
    It would mean that the user's choice would be irrecoverable from the
    data, which is not acceptable. In this situation, store a value for the
    choice, and calculate the score separately, e.g. with

        One -> 'A'
        Two -> 'B'
        Three -> 'C'
        Four -> 'D'
        Five -> 'E'

        int score(char value)
        {
            switch (value) {
                // ...
            }
        }
*/

public:
    NameValueOptions();
    NameValueOptions(std::initializer_list<NameValuePair> options);
    void append(const NameValuePair& nvp);
    int size() const;
    const NameValuePair& at(int index) const;
    int indexFromName(const QString& name) const;
    int indexFromValue(const QVariant& value) const;
    void validateOrDie();
    bool validIndex(int index) const;
    void shuffle();
    void reverse();
    QString name(int index) const;
    QVariant value(int index) const;
    QString nameFromValue(const QVariant& value) const;
    QVariant valueFromName(const QString& name) const;
public:
    static NameValueOptions makeNumbers(int first, int last, int step = 1);
protected:
    QVector<NameValuePair> m_options;
public:
    friend QDebug operator<<(QDebug debug, const NameValueOptions& gi);
};
