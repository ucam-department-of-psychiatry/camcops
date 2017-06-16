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

#pragma once
#include <Eigen/Dense>


namespace statsfunc {

// ============================================================================
// Eigen statistical calculations
// ============================================================================

template<typename Derived>
double variance(const Eigen::ArrayBase<Derived>& a)
{
    double n = a.size();
    double mean = a.mean();
    double ss = (a - mean).square().sum();
    // ... sum of squared deviations from the mean
    return ss / (n - 1);
}


template<typename Derived>
double variance(const Eigen::MatrixBase<Derived>& m)
{
    // For elementwise operations, we need an Array, not a Matrix.
    return variance(m.array());
}


// ============================================================================
// Elementary functions
// ============================================================================

double identity(double x);
double one(double x);
Eigen::ArrayXXd one(const Eigen::ArrayXXd& x);
double logistic(double x);
double logisticInterceptSlope(double x, double intercept, double slope);
double logisticX0K(double x, double x0, double k);  // k steepness, x0 midpoint
double derivativeOfLogistic(double x);  // derivative of logistic function
double logit(double p);  // inverse of logistic function
Eigen::ArrayXXd binomialVariance(const Eigen::ArrayXXd& x);


// ============================================================================
// Solving
// ============================================================================

Eigen::VectorXd svdSolve(const Eigen::MatrixXd& A,
                         const Eigen::VectorXd& b);  // solves Ax = b [or b = Ax + e], for x, minimizing e

// ============================================================================
// GLM support
// ============================================================================

Eigen::Array<Eigen::Index, Eigen::Dynamic, 1> svdsubsel(
        const Eigen::MatrixXd& A, int k = -1);


}  // namespace statsfunc
