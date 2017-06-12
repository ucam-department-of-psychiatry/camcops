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

#define DEBUG_DESIGN_MATRIX
#include "logisticregression.h"
#include <QDebug>
#include "maths/eigenfunc.h"
#include "maths/linkfunctionfamily.h"
using namespace Eigen;


LogisticRegression::LogisticRegression(
        SolveMethod solve_method,
        int max_iterations,
        double tolerance,
        RankDeficiencyMethod rank_deficiency_method) :
    Glm(LINK_FN_FAMILY_LOGIT, solve_method, max_iterations, tolerance,
        rank_deficiency_method)
{
}


void LogisticRegression::fit(const MatrixXd& X,  // predictors, EXCLUDING intercept
                             const VectorXi& y)  // depvar
{
    const MatrixXd predictors = designMatrix(X);
    const VectorXd dependent_variable = y.cast<double>();
    Glm::fit(predictors, dependent_variable);
}


MatrixXd LogisticRegression::designMatrix(const MatrixXd& X) const
{
    MatrixXd X_design(X.rows(), X.cols() + 1);
    X_design << MatrixXd::Ones(X.rows(), 1), X;  // first column is 1.0
#ifdef DEBUG_DESIGN_MATRIX
    addInfo("Design matrix: " +
            eigenfunc::qStringFromEigenMatrixOrArray(X_design));
#endif
    return X_design;
}


VectorXd LogisticRegression::predictProb() const
{
    return predict();
}


VectorXd LogisticRegression::predictProb(const MatrixXd& X) const
{
    return predict(designMatrix(X));
}


VectorXi LogisticRegression::binaryFromP(const VectorXd& p,
                                         double threshold) const
{
    ArrayXXd a = p.array();
    Array<bool, Dynamic, Dynamic> b = a >= threshold;
    // Boundary conditions: if p == 0, should always return 0;
    // if p == 1, should always return 1
    return b.cast<int>().matrix();
}


VectorXi LogisticRegression::predictBinary(double threshold) const
{
    return binaryFromP(predict(), threshold);
}


VectorXi LogisticRegression::predictBinary(const MatrixXd& X,
                                           double threshold) const
{
    return binaryFromP(predictProb(X), threshold);
}


VectorXd LogisticRegression::predictLogit() const
{
    return predictEta().matrix();
}


VectorXd LogisticRegression::predictLogit(const MatrixXd& X) const
{
    return predictEta(designMatrix(X)).matrix();
}
