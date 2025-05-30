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

#include <QDateTime>
#include <QStringList>

#include "maths/include_eigen_dense.h"  // IWYU pragma: keep
#include "maths/linkfunctionfamily.h"

const int GLM_DEFAULT_MAX_ITERATIONS = 25;
// As per both:
// - https://bwlewis.github.io/GLM/
// - R: ?glm.control [from ?glm]
// ... DON'T just increase it arbitrarily; it impacts the results substantially
// when the GLM does not converge. See the logistic regression test menu.

const double GLM_DEFAULT_TOLERANCE = 1e-8;

// As per both:
// - https://bwlewis.github.io/GLM/
// - R: ?glm.control


class Glm
{
    // Generalized linear model (GLM), using Eigen

public:
    // How to solve
    enum class SolveMethod {
        IRLS_KaneLewis,
        IRLS_SVDNewton_KaneLewis,  // second best?
        IRLS_R_glmfit,  // as per R's glm.fit() function; best?
    };

    // How to deal with rank-deficient matrices
    enum class RankDeficiencyMethod {
        SelectColumns,
        MinimumNorm,
        Error,
    };

    // Constructor:
    Glm(const LinkFunctionFamily& link_fn_family,
        SolveMethod solve_method = SolveMethod::IRLS_R_glmfit,
        int max_iterations = GLM_DEFAULT_MAX_ITERATIONS,
        double tolerance = GLM_DEFAULT_TOLERANCE,
        RankDeficiencyMethod rank_deficiency_method
        = RankDeficiencyMethod::SelectColumns);

    // Construct and quick fit (without weights option):
    // - predictors: model matrix (predictors), n_observations x n_predictors
    // - dependent_variable: n_observations x 1
    Glm(const Eigen::MatrixXd& predictors,
        const Eigen::VectorXd& dependent_variable,
        const LinkFunctionFamily& link_fn_family,
        bool add_intercept = true,  // More common to want this than not
        SolveMethod solve_method = SolveMethod::IRLS_R_glmfit,
        int max_iterations = GLM_DEFAULT_MAX_ITERATIONS,
        double tolerance = GLM_DEFAULT_TOLERANCE,
        RankDeficiencyMethod rank_deficiency_method
        = RankDeficiencyMethod::SelectColumns);

    // Set options:
    void setVerbose(bool verbose);

    // Re-retrieve config:
    LinkFunctionFamily getLinkFunctionFamily() const;
    SolveMethod getSolveMethod() const;
    int getMaxIterations() const;
    double getTolerance() const;
    RankDeficiencyMethod getRankDeficiencyMethod() const;

    // Creates a design matrix by adding an initial column containing ones
    // as the intercept term.
    // (Resembles a Python classmethod; sort-of static function.)
    Eigen::MatrixXd addInterceptToPredictors(const Eigen::MatrixXd& x) const;

    // Re-retrieve input:
    Eigen::VectorXd getDependentVariable() const;
    Eigen::MatrixXd getPredictors() const;
    Eigen::VectorXd* getWeightsPointer() const;
    Eigen::Index nObservations() const;
    Eigen::Index nPredictors() const;

    // Fit
    // - predictors: model matrix (predictors), n_observations x n_predictors
    // - dependent_variable: n_observations x 1
    // - p_weights: n_predictors x 1
    void
        fit(const Eigen::MatrixXd& predictors,
            const Eigen::VectorXd& dependent_variable,
            Eigen::VectorXd* p_weights = nullptr);
    // Adds an initial intercept column (all ones), then fits (without weights
    // option):
    // - predictors_excluding_intercept:
    //   model matrix (predictors), n_observations x (n_predictors - 1)
    // - predictors_excluding_intercept: n_observations x 1
    void fitAddingIntercept(
        const Eigen::MatrixXd& predictors_excluding_intercept,
        const Eigen::VectorXd& dependent_variable
    );

    // Get output:
    bool fitted() const;
    bool converged() const;
    int nIterations() const;
    Eigen::VectorXd coefficients() const;

    // Predict output:
    // - With original predictors:
    Eigen::VectorXd predict() const;
    // - With new predictors:
    Eigen::VectorXd predict(const Eigen::MatrixXd& predictors) const;

    // Synonyms:
    Eigen::VectorXd predictMu() const
    {
        return predict();
    }

    Eigen::VectorXd predictMu(const Eigen::MatrixXd& predictors) const
    {
        return predict(predictors);
    }

    Eigen::VectorXd predictResponse() const
    {
        return predict();
    }

    Eigen::VectorXd predictResponse(const Eigen::MatrixXd& predictors) const
    {
        return predict(predictors);
    }

    // Residuals:
    // - With original predictors:
    Eigen::VectorXd residuals() const;
    // - With new predictors:
    Eigen::VectorXd residuals(const Eigen::MatrixXd& predictors) const;

    // The linear predictor (intermediate variable), NOT the "output" value:
    // - With original predictors:
    Eigen::ArrayXXd predictEta() const;
    // - With new predictors:
    Eigen::ArrayXXd predictEta(const Eigen::MatrixXd& predictors) const;

    // Synonyms:
    Eigen::ArrayXXd predictLink() const
    {
        return predictEta();
    }

    Eigen::ArrayXXd predictLink(const Eigen::MatrixXd& predictors) const
    {
        return predictEta(predictors);
    }

    // Dumb stuff (see code):
    Eigen::VectorXd retrodictUnivariatePredictor(const Eigen::VectorXd& depvar
    ) const;

    // Get debugging info:
    QStringList calculationErrors() const;
    QStringList getInfo() const;
    qint64 timeToFitMs() const;

protected:
    // Internals:
    void reset();
    void addInfo(const QString& msg) const;
    void addError(const QString& msg) const;
    void warnReturningGarbage() const;
    // The interesting stuff:
    void fitIRLSKaneLewis();
    void fitIRLSSVDNewtonKaneLewis();
    void fitIRLSRglmfit();
    Eigen::Array<Eigen::Index, Eigen::Dynamic, 1>
        svdsubsel(const Eigen::MatrixXd& A, Eigen::Index k);

protected:
    // Config:
    LinkFunctionFamily m_link_fn_family;
    SolveMethod m_solve_method;
    int m_max_iterations;
    double m_tolerance;
    RankDeficiencyMethod m_rank_deficiency_method;
    bool m_verbose;

    // In (size shown as rows,cols where n = #observations, k = #predictors):
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
    QDateTime m_fit_start_time;
    QDateTime m_fit_end_time;
};
