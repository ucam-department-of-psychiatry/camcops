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

#include "statsfunc.h"
#include <limits>
#include "maths/eigenfunc.h"
using namespace Eigen;

namespace statsfunc {

// ============================================================================
// Elementary functions
// ============================================================================

double identity(double x)
{
    return x;
}


double one(double x)
{
    // Derivative of the identity function:
    //      y = x
    //      y' = 1
    Q_UNUSED(x);
    return 1.0;
}


Eigen::ArrayXXd one(const Eigen::ArrayXXd& x)
{
    ArrayXXd result(x.rows(), x.cols());
    result.setConstant(1.0);
    return result;
}


double logistic(double x)
{
    // The core logistic function, a sigmoid
    // Transforms logit -> probability; inverse of logit()
    return 1.0 / (1.0 + std::exp(-x));
}


double logisticInterceptSlope(double x, double intercept, double slope)
{
    return logistic(intercept + slope * x);
}


double logisticX0K(double x, double x0, double k)
{
    // Generalized logistic function with k steepness, x0 midpoint
    // https://en.wikipedia.org/wiki/Logistic_function
    return logistic(k * (x - x0));

    // HOWEVER, note that there are other formulations of slope/intercept:
    // see e.g. mathfunc::LogisticDescriptives, and as above.
}


double derivativeOfLogistic(double x)
{
    // https://en.wikipedia.org/wiki/Logistic_function#Derivative
    double lgs = logistic(x);
    return lgs * (1.0 - lgs);
}


double logit(double p)
{
    // Transforms probability -> logit; inverse of logistic()
    // natural logs (std::log)
    return std::log(p / (1.0 - p));
}


ArrayXXd binomialVariance(const ArrayXXd& mu)
{
    // - R: binomial()$variance
    // - https://en.wikipedia.org/wiki/Variance_function#Example_.E2.80.93_Bernoulli
    return mu * (1.0 - mu);
}


// ============================================================================
// Solving
// ============================================================================

VectorXd svdSolve(const MatrixXd& A, const VectorXd& b)
{
    // solves Ax = b [or b = Ax + e], for x, minimizing e (in a least-squares sense)
    // https://eigen.tuxfamily.org/dox/group__LeastSquares.html
    return A.jacobiSvd(ComputeThinU | ComputeThinV).solve(b);
}


}  // namespace statsfunc
