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

#pragma once
#include <QString>

extern const QString KIRBY_DEFAULT_CURRENCY;
extern const bool KIRBY_DEFAULT_CURRENCY_SYMBOL_FIRST;


class KirbyRewardPair
{
public:
    KirbyRewardPair(
            int sir, int ldr, int delay_days,
            const QString& currency = KIRBY_DEFAULT_CURRENCY,
            bool currency_symbol_first = KIRBY_DEFAULT_CURRENCY_SYMBOL_FIRST);

    // Implied value of k if indifferent, according to V = A(1 + kD)
    // where A is amount and D is delay. The units of k are days ^ -1.
    double kIndifference() const;

    // Return the question.
    QString question() const;

    // Return a currency amount, formatted.
    QString money(int amount) const;

    int sir;  // small immediate reward
    int ldr;  // large delayed reward
    int delay_days;  // delay to large delayed reward
    QString currency;  // currency symbol
    bool currency_symbol_first;  // true as in £10, or false as in 3€?
};
