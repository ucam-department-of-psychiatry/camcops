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
#include <QVector>

#include "questionnairelib/namevaluepair.h"

class NameValueOptions
{
    /*
    Encapsulates a list of name/value pairs.

    We don't allow duplicate values.
    There are some circumstances when intuitively this would be helpful, e.g.
    we are offering several wrong answers, and don't care which one is
    selected; such as

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

    It's fine (although odd) to have duplicate names.

*/

public:
    // Default constructor
    NameValueOptions();

    // Construct with values.
    NameValueOptions(std::initializer_list<NameValuePair> options);

    // Add a new name/value pair, at the end.
    void append(const NameValuePair& nvp);

    // If a name/value pair exists with the same value, replace it with nvp.
    // Otherwise, if append_if_not_found is true, append nvp.
    void replace(const NameValuePair& nvp, bool append_if_not_found = false);

    // How many name/value pairs do we have?
    int size() const;

    // Return the name/value pair at the given (zero-based) position.
    // (The item returned is affected by shuffle() and reverse(); compare
    // atIndex(). Use this, with an incrementing position, when seeking items
    // to display.)
    const NameValuePair& atPosition(int position) const;

    // Return the first index associated with the specified name, or -1 on
    // failure.
    int indexFromName(const QString& name) const;

    // Return the index associated with the specified value, or -1 on failure.
    int indexFromValue(const QVariant& value) const;

    // Return the index of the item at the given position. This will only be
    // different from its input if the options (i.e. the option indexes) have
    // been randomized.
    int indexFromPosition(const int position) const;

    // Return the position of the option with the specified value or -1 on
    // failure.
    int positionFromValue(const QVariant& value) const;

    // Check there are no duplicate values, or crash the app.
    void validateOrDie();

    // Is the index valid, i.e. in the range [0, size() - 1]?
    bool validIndex(int index) const;

    // Randomize the order (in place).
    void shuffle();

    // Reverse the order (in place).
    void reverse();

    // Returns the name for a given index, or "" if the index is invalid.
    QString nameFromIndex(int index) const;

    // Returns the name for a given index, or QVariant() if the index is
    // invalid.
    QVariant valueFromIndex(int index) const;

    // Returns the name for a given position, or "" if the position is invalid.
    QString nameFromPosition(int position) const;

    // Returns the name for a given position, or QVariant() if the position is
    // invalid.
    QVariant valueFromPosition(int position) const;

    // Returns the name for a given value, or a default string if there isn't
    // one.
    QString nameFromValue(
        const QVariant& value, const QString& default_ = QString()
    ) const;

    // Returns the first value for a given name, or a default if there isn't
    // one.
    QVariant valueFromName(
        const QString& name, const QVariant& default_ = QVariant()
    ) const;

    bool valuesMatch(const NameValueOptions& other) const;

protected:
    // Return the name/value pair at the given (zero-based) index.
    // (That is: index within the UNCHANGING INTERNAL ORDERING, which is
    // unaffected by shuffle() or reverse().)
    const NameValuePair& atIndex(int index) const;

public:
    // Returns a NameValueOptions like {{"1", 1}, {"2", 2}, {"3", 3}...}
    // where the number progresses from "first" to "last" in steps of "step".
    static NameValueOptions makeNumbers(int first, int last, int step = 1);

protected:
    // Stores the options.
    QVector<NameValuePair> m_options;

    // Stores the options' indexes.
    // When the options are randomized, this is what we shuffle so we can
    // say "give me the index of the option at position x". This allows us
    // to maintain other vectors separately from namevalueoptions, for example
    // the list of styles associated with multi-choice answers. If the answers
    // are randomized, we still want to style the answers correctly.
    QVector<int> m_indexes;

public:
    // Debugging description.
    friend QDebug operator<<(QDebug debug, const NameValueOptions& gi);
};
