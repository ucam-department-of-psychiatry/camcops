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
#include <QStringList>
#include "maths/linkfunctionfamily.h"

const int GLM_DEFAULT_MAX_ITERATIONS = 500;
const double GLM_DEFAULT_TOLERANCE = 1e-8;


class Glm
{
    // Generalized linear model (GLM), using Eigen

public:
    enum SolveMethod {
        IRLS,
        IRLS_SVD_Newton,
    };
    enum RankDeficiencyMethod {
        SelectColumns,
        MinimumNorm,
        Error,
    };

    // Constructor:
    Glm(LinkFunctionFamily link_fn_family,
        SolveMethod solve_method = SolveMethod::IRLS_SVD_Newton,
        int max_iterations = GLM_DEFAULT_MAX_ITERATIONS,
        double tolerance = GLM_DEFAULT_TOLERANCE,
        RankDeficiencyMethod rank_deficiency_method = RankDeficiencyMethod::SelectColumns);

    // Re-retrieve config:
    LinkFunctionFamily getLinkFunctionFamily() const;
    SolveMethod getSolveMethod() const;
    int getMaxIterations() const;
    double getTolerance() const;
    RankDeficiencyMethod getRankDeficiencyMethod() const;

    // Re-retrieve input:
    Eigen::VectorXd getDependentVariable() const;
    Eigen::MatrixXd getPredictors() const;
    Eigen::VectorXd* getWeightsPointer() const;
    int nObservations() const;
    int nPredictors() const;

    // Fit
    void fit(const Eigen::MatrixXd& predictors,  // model matrix (predictors), n_observations x n_predictors
             const Eigen::VectorXd& dependent_variable,  // n_observations x 1
             Eigen::VectorXd* p_weights = nullptr);  // for IRLS_SVD_Newton; n_predictors x 1

    // Get output:
    bool fitted() const;
    bool converged() const;
    int nIterations() const;
    Eigen::VectorXd coefficients() const;
    Eigen::VectorXd predict() const;  // ... by original predictors
    Eigen::VectorXd predict(const Eigen::MatrixXd& predictors) const;  // use new predictors
    Eigen::VectorXd residuals() const;  // ... with original predictors
    Eigen::ArrayXXd predictEta(const Eigen::MatrixXd& predictors) const;  // the intermediate variable, BEFORE the inverse link function has been applied (e.g.: logit units)
    Eigen::ArrayXXd predictEta() const;  // ... with original predictors

    // Get debugging info:
    QStringList calculationErrors() const;
    QStringList getInfo() const;

protected:
    void reset();
    void addInfo(const QString& msg) const;
    void addError(const QString& msg) const;
    void warnReturningGarbage() const;
    void fitIRLS();
    void fitIRLSSVDNewton();
    Eigen::Array<Eigen::Index, Eigen::Dynamic, 1> svdsubsel(
            const Eigen::MatrixXd& A, int k);

protected:
    // Config:
    LinkFunctionFamily m_link_fn_family;
    SolveMethod m_solve_method;
    int m_max_iterations;
    double m_tolerance;
    RankDeficiencyMethod m_rank_deficiency_method;

    // In (rows,cols where n = #observations, k = #predictors):
    Eigen::VectorXd m_dependent_variable;  // n,1
    Eigen::MatrixXd m_predictors;  // n,k
    Eigen::VectorXd* m_p_weights;  // k,1

    // Out:
    bool m_fitted = false;  // some attempt made?
    bool m_converged = false;  // satisfactory?
    int m_n_iterations;
    Eigen::VectorXd m_coefficients;  // k,1

    // Debugging info:
    mutable QStringList m_calculation_errors;
    mutable QStringList m_info;
};
