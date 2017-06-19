/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

#include "ccrandom.h"
#include <float.h>
#include <QDebug>
#include <QMultiMap>
#include "maths/countingcontainer.h"
#include "maths/floatbits.h"

namespace ccrandom {


std::random_device rd;
std::mt19937 rng(rd());


bool coin(qreal p)
{
    std::bernoulli_distribution dist(p);
    return dist(rng);
}


int randomInt(int minimum, int maximum)
{
    // [minimum, maximum] -- i.e. inclusive
    std::uniform_int_distribution<int> dist(minimum, maximum);
    return dist(rng);
}


double randomRealExcUpper(double minimum, double maximum)
{
    // [minimum, maximum) -- i.e. includes lower but not upper bound
    // - http://en.cppreference.com/w/cpp/numeric/random/uniform_real_distribution
    //
    // Make this explicitly "double", not float, given some "float"
    // implemetation bugs, as per
    // - http://en.cppreference.com/w/cpp/numeric/random/uniform_real_distribution
    //
    // Nope - we still get the bug with double (GCC 5.4.0).
    // - https://gcc.gnu.org/bugzilla/show_bug.cgi?id=63176
    // - http://open-std.org/JTC1/SC22/WG21/docs/lwg-active.html#2524
    //
    // So, implement GCC suggestion 2: re-run if you get the maximum.

    std::uniform_real_distribution<double> dist(minimum, maximum);
    double result;
    do {
        result = dist(rng);
    } while (result == maximum);
    return result;

    // Yup, that works.
}


float nextFloatAbove(float x)
{
    // https://stackoverflow.com/questions/16335992/alternative-to-c11s-stdnextafter-and-stdnexttoward-for-c03
    // https://randomascii.wordpress.com/2012/01/23/stupid-float-tricks-2/
    if (std::numeric_limits<float>::is_iec559) {
        // http://en.cppreference.com/w/cpp/types/numeric_limits/is_iec559
        BitRepresentationFloat brf(x);
        if (!brf.isMaximum()) {
            ++brf.i;
        }
        return brf.f;
    } else {
        qFatal("nextFloatAbove: machine/compiler not using IEC559 (IEEE 754) "
               "for float");
    }
}


double nextDoubleAboveManual(double x)
{
    if (std::numeric_limits<double>::is_iec559) {
        BitRepresentationDouble brd(x);
        if (!brd.isMaximum()) {
            ++brd.i;
        }
        return brd.d;
    } else {
        qFatal("nextDoubleAbove: machine/compiler not using IEC559 (IEEE 754) "
               "for double");
    }
}


double nextDoubleAbove(double x)
{
    // Detecting the build type:
    // https://stackoverflow.com/questions/6374523/how-to-detect-compilation-by-android-ndk-in-a-c-c-file
#ifdef __ANDROID__
    return nextDoubleAboveManual(x);
#else
    return std::nextafter(x, std::numeric_limits<double>::max());
#endif
}


double randomRealIncUpper(double minimum, double maximum)
{
    // [minimum, maximum] -- i.e. inclusive
    // http://en.cppreference.com/w/cpp/numeric/random/uniform_real_distribution
    double adjusted_max = nextDoubleAbove(maximum);
    return randomRealExcUpper(minimum, adjusted_max);
}


void testRandom()
{
    // https://stackoverflow.com/questions/16839658/printf-width-specifier-to-maintain-precision-of-floating-point-value
    auto fullFloat = [](float f) -> QString {
        return QString::number(f, 'g', 9);
    };
    auto fullDouble = [](double d) -> QString {
        return QString::number(d, 'g', 17);
    };

    auto testNextFloatAbove = [&fullFloat](float f) -> void {
        float nf = nextFloatAbove(f);
        BitRepresentationFloat brf(f);
        BitRepresentationFloat brnf(nf);
        qDebug().nospace().noquote()
                << "nextFloatAbove(" << fullFloat(f)
                << " [integer representation " << brf.ui
                << "]) -> " << fullFloat(nf)
                << " [integer representation " << brnf.ui << "]";
    };
    auto testNextDoubleAbove = [&fullDouble](double d) -> void {
        double dam = nextDoubleAboveManual(d);
        double da = nextDoubleAbove(d);
        BitRepresentationDouble brd(d);
        BitRepresentationDouble brdam(dam);
        BitRepresentationDouble brda(da);
        qDebug().nospace().noquote()
                << "nextDoubleAboveManual(" << fullDouble(d)
                << " [integer representation " << brd.ui
                << "]) -> " << fullDouble(dam)
                << " [integer representation " << brdam.ui << "]";
        qDebug().nospace().noquote()
                << "nextDoubleAbove(" << fullDouble(d)
                << " [integer representation " << brd.ui
                << "]) -> " << fullDouble(da)
                << " [integer representation " << brda.ui << "]";
    };

    auto testRangeSampling = [&fullDouble](qreal range_min, qreal range_max,
                                           int range_n) -> void {
        qreal exc_min = std::numeric_limits<double>::max();  // start high
        qreal exc_max = -exc_min;  // start low
        qreal inc_min = exc_min;
        qreal inc_max = exc_max;
        CountingContainer<int> exc_centiles;
        CountingContainer<int> inc_centiles;
        for (int i = 0; i < range_n; ++i) {
            qreal draw_exc = randomRealExcUpper(range_min, range_max);
            exc_min = qMin(exc_min, draw_exc);
            exc_max = qMax(exc_max, draw_exc);
            int exc_centile = draw_exc * 100;
            exc_centiles.add(exc_centile);

            qreal draw_inc = randomRealIncUpper(range_min, range_max);
            inc_min = qMin(inc_min, draw_inc);
            inc_max = qMax(inc_max, draw_inc);
            int inc_centile = draw_inc * 100;
            inc_centiles.add(inc_centile);
        }
        qDebug().nospace().noquote()
                << "Draw from upper-exclusive range ["
                << fullDouble(range_min) << "–" << fullDouble(range_max)
                << "): min " << fullDouble(exc_min)
                << ", max " << fullDouble(exc_max)
                << ", centiles " << exc_centiles;
        qDebug().nospace().noquote()
                << "Draw from upper-inclusive range ["
                << fullDouble(range_min) << "–" << fullDouble(range_max)
                << "]: min " << fullDouble(inc_min)
                << ", max " << fullDouble(inc_max)
                << ", centiles " << inc_centiles;
    };

    // ========================================================================

    qDebug() << "Testing std::nextafter() [if available on this platform, via "
                "nextDoubleAbove()], and manual versions: nextFloatAbove(), "
                "nextDoubleAboveManual()";
    const QVector<float>  fv{1.0, 100.0, 1.0e10};
    const QVector<double> dv{1.0, 100.0, 1.0e10, 1.0e100};
    for (float f : fv) {
        testNextFloatAbove(f);
    }
    for (double d : dv) {
        testNextDoubleAbove(d);
    }

    const int coin_n = 2000;
    const qreal coin_p = 0.5;
    CountingContainer<bool> coins;

    for (int i = 0; i < coin_n; ++i) {
        coins.add(coin(coin_p));
    }
    qDebug().nospace() << "Coin flips (n=" << coin_n << ", p=" << coin_p
                       << "): " << coins;

    const int die_n = 6000;
    CountingContainer<int> die;

    for (int i = 0; i < die_n; ++i) {
        die.add(randomInt(1, 6));
    }
    qDebug().nospace() << "Rolls of a fair die (n=" << die_n << "): " << die;

    const int range_n = 100000;
    testRangeSampling(0.0,
                      1.0,
                      range_n);
    testRangeSampling(1.0,
                      nextDoubleAbove(nextDoubleAbove(nextDoubleAbove(1.0))),
                      range_n);
}


}  // namespace ccrandom
