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
#include "maths/glm.h"


class LogisticRegression : public Glm
{
public:
    LogisticRegression(
            SolveMethod solve_method =
#ifdef GLM_OFFER_R_GLM_FIT
                    SolveMethod::IRLS_R_glmfit,
#else
                    SolveMethod::IRLS_SVDNewton_KaneLewis,
#endif
            int max_iterations = GLM_DEFAULT_MAX_ITERATIONS,
            double tolerance = GLM_DEFAULT_TOLERANCE,
            RankDeficiencyMethod rank_deficiency_method = RankDeficiencyMethod::Error);
    void fit(const Eigen::MatrixXd& X,  // predictors, EXCLUDING intercept
             const Eigen::VectorXi& y);  // depvar
    Eigen::MatrixXd designMatrix(const Eigen::MatrixXd& X) const;
    Eigen::VectorXd predictProb() const;  // synonym for predict()
    Eigen::VectorXd predictProb(const Eigen::MatrixXd& X) const;  // with new predictors
    Eigen::VectorXi predictBinary(double threshold = 0.5) const;  // with original predictors
    Eigen::VectorXi predictBinary(const Eigen::MatrixXd& X,
                                  double threshold = 0.5) const;  // with new predictors
    Eigen::VectorXd predictLogit() const;  // synonym for predictEta()
    Eigen::VectorXd predictLogit(const Eigen::MatrixXd& X) const;  // with new predictors
protected:
    Eigen::VectorXi binaryFromP(const Eigen::VectorXd& p,
                                double threshold = 0.5) const;
};
