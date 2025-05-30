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
#include "maths/glm.h"

// Implements logistic regression, via a GLM.

class LogisticRegression : public Glm
{
public:
    // Construct
    LogisticRegression(
        SolveMethod solve_method = SolveMethod::IRLS_R_glmfit,
        int max_iterations = GLM_DEFAULT_MAX_ITERATIONS,
        double tolerance = GLM_DEFAULT_TOLERANCE,
        RankDeficiencyMethod rank_deficiency_method
        = RankDeficiencyMethod::Error
    );

    // Fit
    // - X: predictors, EXCLUDING intercept;
    //      dimensions: n_observations x (n_predictors - 1)
    // - y: depvar; n_observations x 1
    void
        fitAddingIntercept(const Eigen::MatrixXd& X, const Eigen::VectorXi& y);

    // Fit
    // - X: predictors, INCLUDING intercept; n_observations x n_predictors
    // - y: depvar; n_observations x 1
    void fitDirectly(const Eigen::MatrixXd& X, const Eigen::VectorXi& y);

    // Predict probabilities:
    // - With original predictors:
    Eigen::VectorXd predictProb() const;  // synonym for predict()
    // - With new predictors:
    Eigen::VectorXd
        predictProb(const Eigen::MatrixXd& X, bool add_intercept = true) const;

    // Predict binary outcomes:
    // - With original predictors:
    Eigen::VectorXi predictBinary(double threshold = 0.5) const;
    // - With new predictors:
    Eigen::VectorXi predictBinary(
        const Eigen::MatrixXd& X,
        double threshold = 0.5,
        bool add_intercept = true
    ) const;

    // Predict logit:
    // - With original predictors:
    Eigen::VectorXd predictLogit() const;  // synonym for predictEta()
    // - With new predictors:
    Eigen::VectorXd predictLogit(
        const Eigen::MatrixXd& X, bool add_intercept = true
    ) const;

protected:
    // Convert probabilities to binary using a threshold:
    Eigen::VectorXi
        binaryFromP(const Eigen::VectorXd& p, double threshold = 0.5) const;
};
