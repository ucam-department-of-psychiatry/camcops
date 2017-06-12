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

#include "mathfunc.h"

#include <QtMath>  // for e.g. qSqrt()
#include <QObject>
#include "common/textconst.h"
#include "lib/convert.h"
#include "maths/eigenfunc.h"
#include "maths/mlpackfunc.h"

namespace mathfunc {


// ============================================================================
// Basic sums
// ============================================================================

bool rangesOverlap(qreal a0, qreal a1, qreal b0, qreal b1)
{
    // There are two ranges: (a0, a1) and (b0, b1). Is there overlap?
    if (a0 > a1) {
        std::swap(a0, a1);
    }
    if (b0 > b1) {
        std::swap(b0, b1);
    }
    if (a1 < b0 || b1 < a0) {
        // A is entirely less than B, or B is entirely less than A.
        return false;
    }
    // Otherwise, there's overlap.
    return true;
}


bool nearlyEqual(qreal x, qreal y)
{
    return qFuzzyIsNull(x - y);
}


QVariant mean(const QVector<QVariant>& values, bool ignore_null)
{
    // ignore_null true: return the mean of the values, ignoring any NULLs.
    // ignore_null false: return the mean, or NULL if any are NULL.
    double total = 0;
    int n = 0;
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.isNull()) {
            if (ignore_null) {
                continue;
            } else {
                return QVariant();  // mean of something including null is null
            }
        }
        n += 1;
        total += v.toDouble();
    }
    if (n == 0) {
        return QVariant();
    }
    return total / n;
}


qreal mean(qreal a, qreal b)
{
    return (a + b) / 2;
}


// ============================================================================
// QVariant operations, and QVariant collections
// ============================================================================

int sumInt(const QVector<QVariant>& values)
{
    int total = 0;
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        total += v.toInt();  // gives 0 if it is NULL
    }
    return total;
}


double sumDouble(const QVector<QVariant>& values)
{
    double total = 0;
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        total += v.toDouble();  // gives 0 if it is NULL
    }
    return total;
}


bool falseNotNull(const QVariant& value)
{
    if (value.isNull() || value.toBool()) {  // null or true
        return false;
    }
    return true;
}


bool allTrue(const QVector<QVariant>& values)
{
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (!v.toBool()) {
            return false;
        }
    }
    return true;
}


bool anyTrue(const QVector<QVariant>& values)
{
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.toBool()) {
            return true;
        }
    }
    return false;
}


bool allFalseOrNull(const QVector<QVariant>& values)
{
    return !anyTrue(values);
}


bool allFalse(const QVector<QVariant>& values)
{
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.isNull() || v.toBool()) {  // null or true
            return false;
        }
    }
    return true;
}


bool anyFalse(const QVector<QVariant> &values)
{
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (!v.isNull() && !v.toBool()) {  // not null and not true
            return true;
        }
    }
    return false;
}


bool anyNull(const QVector<QVariant>& values)
{
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.isNull()) {
            return true;
        }
    }
    return false;
}


bool noneNull(const QVector<QVariant>& values)
{
    return !anyNull(values);
}


bool anyNullOrEmpty(const QVector<QVariant>& values)
{
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.isNull() || v.toString().isEmpty()) {
            return true;
        }
    }
    return false;
}


bool noneNullOrEmpty(const QVector<QVariant>& values)
{
    return !anyNullOrEmpty(values);
}


int countTrue(const QVector<QVariant>& values)
{
    int n = 0;
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.toBool()) {
            n += 1;
        }
    }
    return n;
}


int countFalse(const QVector<QVariant>& values)
{
    int n = 0;
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (falseNotNull(v)) {
            n += 1;
        }
    }
    return n;
}


int countNull(const QVector<QVariant>& values)
{
    int n = 0;
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (v.isNull()) {
            n += 1;
        }
    }
    return n;
}


int countNotNull(const QVector<QVariant>& values)
{
    int n = 0;
    int length = values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = values.at(i);
        if (!v.isNull()) {
            n += 1;
        }
    }
    return n;
}


bool eq(const QVariant& x, int test)
{
    // SQL principle: NULL is not equal to anything
    return !x.isNull() && x.toInt() == test;
}


bool eq(const QVariant& x, bool test)
{
    return !x.isNull() && x.toBool() == test;
}


bool eqOrNull(const QVariant& x, int test)
{
    return x.isNull() || x.toInt() != test;
}


bool eqOrNull(const QVariant& x, bool test)
{
    return x.isNull() || x.toBool() != test;
}



int countWhere(const QVector<QVariant>& test_values,
               const QVector<QVariant>& where_values)
{
    int n = 0;
    int length = test_values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = test_values.at(i);
        if (where_values.contains(v)) {
            n += 1;
        }
    }
    return n;
}


int countWhereNot(const QVector<QVariant>& test_values,
                  const QVector<QVariant>& where_not_values)
{
    int n = 0;
    int length = test_values.length();
    for (int i = 0; i < length; ++i) {
        const QVariant& v = test_values.at(i);
        if (!where_not_values.contains(v)) {
            n += 1;
        }
    }
    return n;
}


// ============================================================================
// Functions for scoring
// ============================================================================

QString percent(double numerator, double denominator, int dp)
{
    double pct = 100 * numerator / denominator;
    return convert::toDp(pct, dp) + "%";
}


QString scoreString(int numerator, int denominator, bool show_percent, int dp)
{
    QString result = QString("<b>%1</b>/%2").arg(numerator).arg(denominator);
    if (show_percent) {
        result += " (" + percent(numerator, denominator, dp) + ")";
    }
    return result;
}


QString scoreString(double numerator, int denominator, bool show_percent, int dp)
{
    QString result = QString("<b>%1</b>/%2")
            .arg(convert::toDp(numerator, dp))
            .arg(denominator);
    if (show_percent) {
        result += " (" + percent(numerator, denominator, dp) + ")";
    }
    return result;
}


QString scoreStringVariant(const QVariant& numerator, int denominator,
                           bool show_percent, int dp)
{
    QString result = QString("<b>%1</b>/%2")
            .arg(convert::prettyValue(numerator, dp))
            .arg(denominator);
    if (show_percent) {
        result += " (" + percent(numerator.toDouble(), denominator, dp) + ")";
    }
    return result;
}


QString scoreStringWithPercent(int numerator, int denominator, int dp)
{
    return scoreString(numerator, denominator, true, dp);
}


QString scorePhrase(const QString& description, int numerator, int denominator,
                    const QString& separator, const QString& suffix)
{
    return QString("%1%2%3%4")
            .arg(description,
                 separator,
                 scoreString(numerator, denominator, false),
                 suffix);
}


QString scorePhrase(const QString& description, double numerator, int denominator,
                    const QString& separator, const QString& suffix, int dp)
{
    return QString("%1%2%3%4")
            .arg(description,
                 separator,
                 scoreString(numerator, denominator, false, dp),
                 suffix);
}


QString scorePhraseVariant(const QString& description,
                           const QVariant& numerator, int denominator,
                           const QString& separator, const QString& suffix,
                           int dp)
{
    return QString("%1%2%3%4")
            .arg(description,
                 separator,
                 scoreStringVariant(numerator, denominator, false, dp),
                 suffix);
}


QString totalScorePhrase(int numerator, int denominator,
                         const QString& separator, const QString& suffix)
{
    return scorePhrase(textconst::TOTAL_SCORE, numerator, denominator,
                       separator, suffix);
}


QString totalScorePhrase(double numerator, int denominator,
                         const QString& separator, const QString& suffix,
                         int dp)
{
    return scorePhrase(textconst::TOTAL_SCORE, numerator, denominator,
                       separator, suffix, dp);
}


// ============================================================================
// Sequence and range generation
// ============================================================================

QVector<int> range(int start, int end)
{
    return seq(start, end - 1, 1);
}


QVector<int> range(int n)
{
    // returns 0 to n-1 inclusive
    return range(0, n);
}


// ============================================================================
// Spacing things out
// ============================================================================

QVector<qreal> distribute(int n, qreal minimum, qreal maximum)
{
    // Fence/fence-post problem; return centre of fence segments.
    QVector<qreal> posts;
    if (n <= 0) {
        return posts;  // or we'll have division by zero shortly
    }
    if (maximum < minimum) {
        std::swap(minimum, maximum);
    }
    qreal extent = maximum - minimum;
    qreal each = extent / n;
    // ... (double / int) gives double
    // https://stackoverflow.com/questions/5563000/implicit-type-conversion-rules-in-c-operators
    qreal centre_offset = each / 2;
    for (int i = 0; i < n; ++i) {
        posts.append(minimum + i * each + centre_offset);
    }
    return posts;
}


QPair<int, int> gridDimensions(int n, qreal aspect)
{
    // Solve the equations:
    //      x * y >= n
    //      aspect ~= x / y
    // ... for smallest x, y. Thus:
    //      x = aspect * y
    //      aspect * y * y >= n
    int y = qCeil(qSqrt(n / aspect));
    int x = qCeil(n / y);
    return QPair<int, int>(x, y);
}


// ============================================================================
// Numerical conversions
// ============================================================================

int proportionToByte(qreal proportion)
{
    // convert 0.0-1.0 to 0-255
    int a = std::round(qBound(0.0, proportion, 1.0) * 255);
    return qBound(0, a, 255);
}


qreal byteToProportion(int byte)
{
    // convert 0-255 to 0.0-1.0
    return qBound(0, byte, 255) / 255.0;
}


int proportionToIntPercent(qreal proportion)
{
    // convert 0.0-1.0 to 0-100
    int a = std::round(qBound(0.0, proportion, 1.0) * 100);
    return qBound(0, a, 100);
}


qreal intPercentToProportion(int percent)
{
    // convert 0-100 to 0.0-1.0
    return qBound(0, percent, 100) / 100.0;
}


// ============================================================================
// Logistic regression
// ============================================================================


/*

-------------------------------------------------------------------------------
For logistic regression: Choosing a library (or roll our own?)
-------------------------------------------------------------------------------
The Javascript implementation was based on
- http://statpages.info/logistic.html

Theory:
- http://people.csail.mit.edu/jrennie/writing/lr.pdf

Relevant C libraries include
- GSL
  https://lists.gnu.org/archive/html/help-gsl/2010-04/msg00021.html
  https://www.gnu.org/software/gsl/manual/html_node/Linear-regression-with-a-constant-term.html

A few C++ implementations:
- https://stackoverflow.com/questions/33976729/logistic-regression-for-fault-detection-in-an-image
- https://github.com/bluekingsong/logistic-regression-cpp/blob/master/code/logistic_regression.cpp
- https://github.com/liyanghua/logistic-regression-in-c--/blob/master/lr.cpp
- OpenCV
  http://docs.opencv.org/3.0-beta/modules/ml/doc/logistic_regression.html
- mlpack [OF INTEREST]
  http://mlpack.org/
  http://mlpack.org/docs/mlpack-2.2.3/doxygen.php?doc=namespacemlpack_1_1regression.html
  ... uses Armadillo
      http://www.mlpack.org/docs/mlpack-1.0.0/doxygen.php?doc=build.html
      http://arma.sourceforge.net/docs.html
      ... needs cross-compilation and tries to use system LAPACK/BLAS
          see output of "cmake ." in Armadillo base directory
          https://stackoverflow.com/questions/21263427/cross-compiling-armadillo-linear-algebra-library
- Dlib [OF INTEREST]
  http://dlib.net/ml.html
  https://sourceforge.net/p/dclib/discussion/442518/thread/8f16e2e2/
- Overview of libraries
  https://en.wikipedia.org/wiki/List_of_numerical_libraries#C.2B.2B
- ALGLIB
  http://www.alglib.net/dataanalysis/logit.php
- Eigen
  see below

-------------------------------------------------------------------------------
DLib notes
-------------------------------------------------------------------------------

http://dlib.net/matrix_ex.cpp.html

type is:    dlib::matrix<type, nrows, ncols>
    ... but specify 0 for "don't know yet"

e.g.
            dlib::matrix<double, 0, 1> m(n);  // creates column vector, size n

element-access shorthand m(i) is available for column vectors

-------------------------------------------------------------------------------
DLib example code
-------------------------------------------------------------------------------

#include <dlib/matrix.h>


template<typename T>
dlib::matrix<double, 0, 1> dlibColumnVectorFromQVector(const QVector<T>& v)
{
    int n = v.size();
    dlib::matrix<double, 0, 1> m(n);
    for (int i = 0; i < n; ++i) {
        m(i) = v.at(i);
    }
    return m;
}


template<typename T>
dlib::matrix<double, 1, 0> dlibRowVectorFromQVector(const QVector<T>& v)
{
    int n = v.size();
    dlib::matrix<double, 1, 0> m(n);
    for (int i = 0; i < n; ++i) {
        m(1, i) = v.at(i);
    }
    return m;
}


For logistic regression in DLib:
    see https://sourceforge.net/p/dclib/discussion/442518/thread/8f16e2e2/

-------------------------------------------------------------------------------
MLPACK notes
-------------------------------------------------------------------------------

arma::mat is shorthand for arma::Mat<double>
    constructor: mat(n_rows, n_cols)

arma::vec is shorthand for arma::Col<double>, equiv. to mat(n, 1)

http://arma.sourceforge.net/docs.html#element_access

BUT it uses BLAS and lots of other compiled things...

    https://en.m.wikipedia.org/wiki/Basic_Linear_Algebra_Subprograms

-------------------------------------------------------------------------------
Eigen notes
-------------------------------------------------------------------------------

- http://eigen.tuxfamily.org
- https://codereview.stackexchange.com/questions/112750/logistic-regression-with-eigen
- https://github.com/wepe/MachineLearning/tree/master/logistic%20regression/use_cpp_and_eigen
- https://forum.kde.org/viewtopic.php?f=74&t=129644

Note also that Douglas Bates's lme4 is implemented using Eigen (Bates et al.
2015, J Stat Soft 67:1), which is a fair endorsement!

*/

QVector<qreal> logisticFitSinglePredictor(const QVector<qreal>& x,
                                          const QVector<int>& y)
{
    // Returns vector of length 2 containing the parameters (intercept, slope)

#if 0  // code for MLPACK
    using namespace mlpackfunc;
    arma::vec predictors = armaColumnVectorFromQVector<double>(x);
    arma::Row<size_t> responses = armaRowVectorFromQVector<size_t>(y);
    arma::vec parameters = getParamsLogisticFitSinglePredictor(
                predictors, responses);
    return qVectorFromArmaVector<qreal>(parameters);
#endif
    using namespace eigenfunc;
    ColumnVector<qreal> predictors = eigenColumnVectorFromQVector<qreal>(x);
    RowVector<int> responses = eigenColumnVectorFromQVector<int>(y);
    ColumnVector<double> parameters = getParamsLogisticFitSinglePredictor(
                predictors, responses);
    return qVectorFromEigenVector<qreal>(parameters);
}


LogisticDescriptives logisticDescriptives(const QVector<qreal>& parameters)
{
    LogisticDescriptives desc;
    if (parameters.size() == 2) {
        desc.ok = true;
        desc.intercept = parameters.at(0);
        desc.slope = parameters.at(1);
        desc.k = desc.slope;
        desc.theta = -desc.intercept / desc.slope;  // also the x50 value
    }
    return desc;
}


qreal logisticFindXWhereP(qreal p, qreal slope, qreal intercept)
{
    return (qLn(p / (1 - p)) - intercept) / slope;
}


}  // namespace mathfunc
