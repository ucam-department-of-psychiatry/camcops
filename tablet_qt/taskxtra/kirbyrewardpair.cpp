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

#include "kirbyrewardpair.h"
#include <QObject>

const QString KIRBY_DEFAULT_CURRENCY("£");  // Make configurable? Read local currency?
const bool KIRBY_DEFAULT_CURRENCY_SYMBOL_FIRST = true;  // Make configurable? Read local currency?


KirbyRewardPair::KirbyRewardPair(const int sir, const int ldr,
                                 const int delay_days, const QString& currency,
                                 const bool currency_symbol_first) :
    sir(sir),
    ldr(ldr),
    delay_days(delay_days),
    currency(currency),
    currency_symbol_first(currency_symbol_first)
{
}


double KirbyRewardPair::kIndifference() const
{
    const double a1 = sir;  // amount A1, which is immediate i.e. delay D1 = 0
    const double a2 = ldr;  // amount A2; A2 > A1
    const double d2 = delay_days;  // delay D2
    // Values:
    //           V1 = A1/(1 + kD1) = A1
    //           V2 = A2/(1 + kD2)
    // At indifference,
    //           V1 = V2
    // so
    //      A1      = A2/(1 + kD2)
    //      A2 / A1 = 1 + kD2
    //            k = ((A2 / A1) - 1) / D2
    return ((a2 / a1) - 1) / d2;
}


QString KirbyRewardPair::money(const int amount) const
{
    if (currency_symbol_first) {
        return QString("%1%2").arg(currency, QString::number(amount));
    }
    return QString("%1%2").arg(QString::number(amount), currency);
}


QString KirbyRewardPair::question() const
{
    return QString(QObject::tr("Would you prefer %1 today, or %2 in %3 days?"))
            .arg(money(sir), money(ldr), QString::number(delay_days));
}
