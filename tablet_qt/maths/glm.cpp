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

/*

[1] https://github.com/wepe/MachineLearning/tree/master/logistic%20regression/use_cpp_and_eigen
    ... gives WRONG ANSWERS
[2] https://en.wikipedia.org/wiki/Cross_entropy#Cross-entropy_error_function_and_logistic_regression
[3] https://eigen.tuxfamily.org/dox/group__QuickRefPage.html#title2
[4] https://stackoverflow.com/questions/19824293/regularized-logistic-regression-code-in-matlab
[5] http://www.cs.cmu.edu/~ggordon/IRLS-example/
[6] https://stats.stackexchange.com/questions/166958/multinomial-logistic-loss-vs-cross-entropy-vs-square-error
[7] http://eli.thegreenplace.net/2016/logistic-regression/
[8] http://blog.smellthedata.com/2009/06/python-logistic-regression-with-l2.html
[9] https://github.com/PatWie/CppNumericalSolvers
[10] https://bwlewis.github.io/GLM/  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    - Best algorithmic introduction to GLMs
[11] https://en.wikipedia.org/wiki/Generalized_linear_model#Model_components
[12] http://web.as.uky.edu/statistics/users/pbreheny/760/S13/notes/2-19.pdf

-------------------------------------------------------------------------------
First, a general linear model
-------------------------------------------------------------------------------
- Cardinal & Aitken 2006, p379 onwards.

Matrix notation: as per standard:
    - define matrix(nrows, ncols)
    - address element as m(row, col)

For a single dependent variable:
    n   number of observations
    k   number of predictors (including intercept)

    Y   dependent variable(s), vector (n * 1)
    X   design matrix (predictors), matrix (n * k)
    b   coefficients/parameters, vector (k * 1)
    e   error, vector (n * 1)
        ... expected to be normally distributed: e ~ N(mean, SD)

Then a general linear model is

    Y = Xb + e

... for which we solve for b.

A generalized linear model extends this with a link function [11]:
    eta = Xb                        // linear predictor
    E(Y) = mu = invlink(eta)        // Y = invlink(eta) or eta = link(y), ignoring error etc.

i.e.

    Y = invlink(Xb + e)             // or Y = invlink(Xb) + e?  In any case, Y_predicted = invlink(Xb)
    link(Y) = Xb + e
    g(Y) = Xb + e                   // the link function is called g()

... so in Wikipedia notation,

    Xb = g(mu) = g(Y)

For logistic regression, then:

    Y = logistic(Xb + e)            // logistic is the INVERSE link function
    logit(Y) = Xb + e               // logit (= inverse logistic) is the link fn

*/

#include "glm.h"
#include <algorithm>
#include <QDebug>
#include "maths/dqrls.h"
#include "maths/eigenfunc.h"
#include "maths/mathfunc.h"
#include "maths/statsfunc.h"
using namespace Eigen;

// Eigen's cross() requires specific dimensions, that must be known at
// compile-time, or you get THIS_METHOD_IS_ONLY_FOR_VECTORS_OF_A_SPECIFIC_SIZE.
// - https://stackoverflow.com/questions/43283444/row-wise-cross-product-eigen
// - http://eigen.tuxfamily.org/bz/show_bug.cgi?id=1037
// A more general cross-product (after R's ?crossprod) is t(x) %*% y.
// However, this doesn't work as a template because Eigen produces objects of
// intermediate type, like Eigen::Product<...>, so let's just use the
// preprocessor, being careful with brackets:
#define CROSSPROD(x, y) ((x).matrix().transpose() * (y).matrix())

// Also helpful to have an svd() macro to match R's.
#define svd(x) ((x).jacobiSvd(ComputeThinU | ComputeThinV))


const double NA = std::numeric_limits<double>::quiet_NaN();
const double INF = std::numeric_limits<double>::infinity();


// ============================================================================
// Constructor
// ============================================================================

Glm::Glm(const LinkFunctionFamily& link_fn_family,
         const SolveMethod solve_method,
         const int max_iterations,
         const double tolerance,
         const RankDeficiencyMethod rank_deficiency_method) :
    m_link_fn_family(link_fn_family),
    m_solve_method(solve_method),
    m_max_iterations(max_iterations),
    m_tolerance(tolerance),
    m_rank_deficiency_method(rank_deficiency_method),
    m_verbose(false)
{
    reset();
}


// ============================================================================
// Set options
// ============================================================================

void Glm::setVerbose(bool verbose)
{
    m_verbose = verbose;
}


// ============================================================================
// Fit method
// ============================================================================

void Glm::fit(const MatrixXd& predictors,
              const VectorXd& depvar,
              VectorXd* p_weights)
{
    if (m_verbose) {
        qInfo() << "Glm::fit() starting";
    }
    reset();
    m_fit_start_time = QDateTime::currentDateTime();

    // Set up data
    m_predictors = predictors;
    m_dependent_variable = depvar;
    m_p_weights = p_weights;

    // Validate input
    bool ok = true;
    const int n_predictors = nPredictors();
    const int n_observations = nObservations();
    addInfo(QString("Number of observations: %1").arg(n_observations));
    addInfo(QString("Number of predictors: %1").arg(n_predictors));
    if (m_predictors.rows() != n_observations) {  // n
        addError(QString(
                "Mismatch: 'predictors' has %1 rows but 'dependent_variable' "
                "has %2 rows; should match (and be: number of observations)!"
            ).arg(m_predictors.rows()).arg(n_observations));
        ok = false;
    }
    if (m_p_weights && m_p_weights->rows() != n_predictors) {
        addError(QString(
                "Mismatch: '*p_weights' has %1 rows but 'predictors' "
                "has %2 columns; should match (and be: number of predictors)!"
            ).arg(m_p_weights->rows()).arg(n_predictors));
        ok = false;
    }

    // Perform fit
    if (ok) {
        switch (m_solve_method) {
        case SolveMethod::IRLS_KaneLewis:
            fitIRLSKaneLewis();
            break;
        case SolveMethod::IRLS_SVDNewton_KaneLewis:
            fitIRLSSVDNewtonKaneLewis();
            break;
#ifdef GLM_OFFER_R_GLM_FIT
        case SolveMethod::IRLS_R_glmfit:
            fitIRLSRglmfit();
            break;
#endif
        default:
            addError("Unknown solve method!");
            break;
        }
    }

    m_fit_end_time = QDateTime::currentDateTime();

    // Report any errors
    if (m_verbose && !m_info.isEmpty()) {
        qInfo() << "Info from GLM fit:";
        for (const QString& info : m_info) {
            qInfo().noquote() << "-" << info;
        }
    }
    if (!m_calculation_errors.isEmpty()) {
        qWarning() << "Errors occurred during GLM fit:";
        for (const QString& error : m_calculation_errors) {
            qWarning().noquote() << "-" << error;
        }
    }
    if (!m_fitted) {
        qWarning() << "GLM could not be fitted";
    } else if (!m_converged) {
        qWarning() << "GLM did not converge";
    }
    if (m_verbose) {
        qInfo() << "Glm::fit() finishing";
    }
}


// ============================================================================
// Re-retrieve config
// ============================================================================

LinkFunctionFamily Glm::getLinkFunctionFamily() const
{
    return m_link_fn_family;
}


Glm::SolveMethod Glm::getSolveMethod() const
{
    return m_solve_method;
}


int Glm::getMaxIterations() const
{
    return m_max_iterations;
}


double Glm::getTolerance() const
{
    return m_tolerance;
}


Glm::RankDeficiencyMethod Glm::getRankDeficiencyMethod() const
{
    return m_rank_deficiency_method;
}


// ============================================================================
// Re-retrieve input
// ============================================================================

VectorXd Glm::getDependentVariable() const
{
    return m_dependent_variable;
}


MatrixXd Glm::getPredictors() const
{
    return m_predictors;
}


Eigen::VectorXd* Glm::getWeightsPointer() const
{
    return m_p_weights;
}


int Glm::nObservations() const
{
    return m_dependent_variable.rows();
}


int Glm::nPredictors() const
{
    return m_predictors.cols();
}


// ============================================================================
// Get output
// ============================================================================

bool Glm::fitted() const
{
    return m_fitted;
}


bool Glm::converged() const
{
    return m_converged;
}


int Glm::nIterations() const
{
    return m_n_iterations;
}


VectorXd Glm::coefficients() const
{
    return m_coefficients;
}


VectorXd Glm::predict(const MatrixXd& predictors) const
{
    // As per: Y_predicted = invlink(Xb)
    if (!m_fitted || predictors.cols() != nPredictors()) {
        warnReturningGarbage();
        return VectorXd();
    }
    const ArrayXXd eta = predictEta(predictors);
    // y = invlink(eta)
    const ArrayXXd predicted = m_link_fn_family.inv_link_fn(eta);
    return predicted.matrix();
}


VectorXd Glm::predict() const
{
    return predict(m_predictors);
}


Eigen::VectorXd Glm::residuals(const Eigen::MatrixXd& predictors) const
{
    if (!m_fitted || predictors.cols() != nPredictors()) {
        warnReturningGarbage();
        return VectorXd();
    }
    return predict(predictors) - m_dependent_variable;
}


VectorXd Glm::residuals() const
{
    return residuals(m_predictors);
}


Eigen::ArrayXXd Glm::predictEta(const Eigen::MatrixXd& predictors) const
{
    if (!m_fitted || predictors.cols() != nPredictors()) {
        warnReturningGarbage();
        return VectorXd();
    }
    // eta = Xb
    return (predictors * m_coefficients).array();
}


Eigen::ArrayXXd Glm::predictEta() const
{
    return predictEta(m_predictors);
}


// ============================================================================
// Dumb stuff
// ============================================================================

VectorXd Glm::retrodictUnivariatePredictor(const VectorXd& y) const
{
    // If there is >1 predictor, this is utterly meaningless.
    if (!m_fitted || m_coefficients.size() != 2) {
        warnReturningGarbage();
        return VectorXd();
    }
    // But on the assumption that the first column of the predictors is an
    // intercept, and the second is a univariate predictor, there is some
    // meaning:
    const double b0 = m_coefficients(0);  // intercept
    const double b1 = m_coefficients(1);  // slope
    // In these circumstances, the GLM is
    //      y = invlink(xb [+ error somewhere]) = invlink(b0 + x * b1)
    //      link(y) = b0 + x * b1
    //      x = (link(y) - b0) / b1
    //      x = (eta - b0) / b1
    const ArrayXd eta = m_link_fn_family.link_fn(y.array());
    return (eta - b0) / b1;
}


// ============================================================================
// Get debugging info
// ============================================================================

QStringList Glm::calculationErrors() const
{
    return m_calculation_errors;
}


QStringList Glm::getInfo() const
{
    return m_info;
}


qint64 Glm::timeToFitMs() const
{
    return m_fit_start_time.msecsTo(m_fit_end_time);
}


// ============================================================================
// Internals
// ============================================================================

void Glm::reset()
{
    m_dependent_variable = VectorXd();
    m_predictors = MatrixXd();
    m_p_weights = nullptr;

    m_fitted = false;
    m_converged = false;
    m_n_iterations = 0;
    m_coefficients = VectorXd();

    m_calculation_errors.clear();
    m_info.clear();
    m_fit_start_time = m_fit_end_time = QDateTime();
}


void Glm::warnReturningGarbage() const
{
    QString not_fitted("Not fitted! Returning garbage.");
    qWarning() << not_fitted;
    addError(not_fitted);
}


void Glm::addInfo(const QString &msg) const
{
    m_info.append(msg);
}


void Glm::addError(const QString &msg) const
{
    m_calculation_errors.append(msg);
}


// ============================================================================
// The interesting parts
// ============================================================================

void Glm::fitIRLSKaneLewis()
{
    addInfo("Fitting GLM using iteratively reweighted least squares (IRLS) "
            "estimation");
    // https://bwlewis.github.io/GLM/

    // Renaming:
    // Everyone uses a different notation!
    // Translation table:
    //      Thing   Conventional notation       https://bwlewis.github.io/GLM/
    //      ------------------------------------------------------------------
    //      depvar      Y                               b
    //      predictors  X                               A
    //      coeffs      b                               x
    const MatrixXd& A = m_predictors;   // n,k
    const ArrayXXd& b = m_dependent_variable.array();  // n,1
    const LinkFunctionFamily& family = m_link_fn_family;
    const int n_predictors = nPredictors();
    using statsfunc::svdSolve;

    VectorXd x = VectorXd::Zero(n_predictors);  // k,1
    VectorXd xold = VectorXd::Zero(n_predictors);  // k,1
    for (m_n_iterations = 1;
            m_n_iterations <= m_max_iterations;
            ++m_n_iterations) {
        // Note also, for debugging, that you can inspect matrices, but not
        // arrays, in the Qt debugger.
        const ArrayXXd eta = (A   * x).array();
                           // n,k * k,1  -> n,1
        const ArrayXXd g = family.inv_link_fn(eta);  // apply invlink to eta -> n,1
        const ArrayXXd gprime = family.derivative_inv_link_fn(eta);  // -> n,1
        const ArrayXXd gprime_squared = gprime.square();  // -> n,1
        const VectorXd z = (eta + (b - g) / gprime).matrix();  // n,1
        const ArrayXXd var_g = family.variance_fn(g);
        const MatrixXd W = (gprime_squared / var_g).matrix().asDiagonal();  // n,n
        xold = x;

        // Now the tricky bit.
        // The source has:
        //      Let x[j+1] = (A_T W A)^−1 A_T W z
        // In R, it uses:
        //      x = solve(crossprod(A,W*A), crossprod(A,W*z), tol=2*.Machine$double.eps)
        // R says "solve" solves "a %*% x = b" for x
        // ... i.e.
        //              a * x = b
        //              a_INV * a * x = a_INV * b
        //              x = a_INV * b
        // Therefore, we translate to:
        //      "A" = A_T W A = A.cross(W * A) ?
        //      "b" = A_T W z = A.cross(W * z) ?
        // ... yes, except that we can't use Eigen's "cross" like that; see
        //     instead the preprocessor macro CROSSPROD to create some
        //     shorthand while still allowing compiler optimization for Eigen
        //     code.
        // In Eigen, we solve Ax = b using
        //      x = A.jacobiSvd(options).solve(b)
        // So we end up with:

        x = svdSolve(CROSSPROD(A,     W   * A),
                            // n,k ; (n,n * n,k) -> n,k        --> k,k
                     CROSSPROD(A,     W   * z));
                            // n,k ; (n,n * n,1) -> n,1        --> k,1
        // -> k,1

        double euclidean_norm_of_change = (x - xold).norm();
        // = sqrt(sum of squared values of (x - xold))
        if (euclidean_norm_of_change < m_tolerance) {
            m_converged = true;
            break;
        }
    }

    m_fitted = true;
    m_coefficients = x;  // k,1
}


void Glm::fitIRLSSVDNewtonKaneLewis()
{
    addInfo("Fitting GLM using iteratively reweighted least squares (IRLS) "
            "estimation, SVD (singular value decomposition) Newton variant");
    // https://bwlewis.github.io/GLM/
    // Because of the variability in variable names, for dimensional analysis
    // we'll use nobs, npred.

    // Renaming, as above
    MatrixXd A = m_predictors;  // nobs,npred
    const ArrayXXd& b = m_dependent_variable.array();  // nobs,1
    const LinkFunctionFamily& family = m_link_fn_family;
    const int n_predictors = nPredictors();  // = npred
    const int m = nObservations();  // n (sigh...) = nobs
    const int& n = n_predictors;  // = npred
    using namespace eigenfunc;

    ArrayXd weights(m);  // nobs,1
    // Below, can't use "weights = m_p_weights ? ... : ...", because the
    // resulting template types are not identical. But this works fine:
    if (m_p_weights) {
        weights = m_p_weights->array();
    } else {
        weights = ArrayXd::Ones(m);
    }
    if (weights.rows() != m) {
        addError(QString(
                     "'weights' is of length %1, but should match number of "
                     "observations, %2").arg(weights.rows(), m));
        return;
    }

    // If any weights are zero, set corresponding A row to zero
    for (int i = 0; i < m; ++i) {
        if (weights(i) == 0) {
            A.row(i).setConstant(0);
        }
    }

    JacobiSVD<MatrixXd> S = svd(A);
    // In R, the "d" part of an SVD is the vector of singular values; "u" is
    // the matrix of left singular values vectors; "v" is the matrix of right
    // singular values vectors. The original here used S$d.
    // In Eigen, singular values are given by singularValues(), and are always
    // in descending order (I presume they're also in descending order in R!).
    // https://eigen.tuxfamily.org/dox/classEigen_1_1SVDBase.html
    ArrayXd S_d = S.singularValues().array();
    if (S_d.size() == 0) {
        // Before we address d(0)... check it exists!
        addError("Singular values: empty!");
        return;
    }
    IndexArray select_pred_indices = indexSeq(0, n_predictors - 1);
    ArrayXb tiny_singular_values = S_d / S_d(0) < m_tolerance;
    int k = tiny_singular_values.cast<int>().sum();  // number of tiny singular values; ntiny
    if (k > 0) {
        addInfo("Numerically rank-deficient model matrix");
        switch (m_rank_deficiency_method) {
        case RankDeficiencyMethod::SelectColumns:
            addInfo("RankDeficiencyMethod::SelectColumns");
            select_pred_indices = svdsubsel(A, n - k);
            S = svd(subsetByColumnIndex(A, select_pred_indices));
            S_d = S.singularValues().array();  // Since we change S, rewrite S_d
            break;
        case RankDeficiencyMethod::MinimumNorm:
            addInfo("RankDeficiencyMethod::MinimiumNorm");
            // Dealt with at the end; see below
            break;
        case RankDeficiencyMethod::Error:
            addError("Near rank-deficient model matrix");
            return;
        default:
            addError("Unknown rank deficiency method!");
            return;
        }
    }

    ArrayXd t = ArrayXd::Zero(m);  // nobs,1  // NB confusing name choice, cf. R's t() for transpose
    MatrixXd s = VectorXd::Zero(select_pred_indices.size());  // npred_unless_subselected,1
    MatrixXd s_old = s;  // npred_unless_subselected,1
    ArrayXb select_pred_bool = selectBoolFromIndices(select_pred_indices, n_predictors);
    ArrayXb good = weights > 0;  // nobs,1
    double two_epsilon = 2.0 * std::numeric_limits<double>::epsilon();

    for (m_n_iterations = 1;
            m_n_iterations <= m_max_iterations;
            ++m_n_iterations) {
        const ArrayXd t_good = subsetByElementBoolean(t, good);  // nobs_where_good,1
        const ArrayXd b_good = subsetByElementBoolean(b, good);  // nobs_where_good,1
        const ArrayXd weights_good = subsetByElementBoolean(weights, good);  // nobs_where_good,1

        const ArrayXd g = family.inv_link_fn(t_good);  // nobs_where_good,1

        const ArrayXd varg = family.variance_fn(g);  // nobs_where_good,1
        if (varg.isNaN().any()) {
            // As per original...
            addError(QString("NAs in variance of the inverse link function "
                             "(iteration %1)").arg(m_n_iterations));
            return;
        }
        // But also (RNC):
        if (varg.isInf().any()) {
            // As per original...
            addError(QString("Infinities in variance of the inverse link "
                             "function (iteration %1)").arg(m_n_iterations));
            return;
        }
        if ((varg == 0).any()) {
            addError(QString("Zero value in variance of the inverse link "
                             "function (iteration %1)").arg(m_n_iterations));
            return;
        }

        const ArrayXd gprime = family.derivative_inv_link_fn(t_good);  // nobs_where_good,1
        if (gprime.isNaN().any()) {
            // As per original...
            addError(QString("NAs in the inverse link function derivative "
                             "(iteration %1)").arg(m_n_iterations));
            return;
        }
        // But also (RNC):
        if (gprime.isInf().any()) {
            // As per original...
            addError(QString("Infinities in the inverse link function "
                             "derivative (iteration %1)").arg(m_n_iterations));
            return;
        }

        ArrayXd z = ArrayXd::Zero(m);  // nobs,1
        ArrayXd W = ArrayXd::Zero(m);  // nobs,1
        ArrayXd to_z_good = t_good + (b_good - g) / gprime;  // nobs_where_ngood,1
        assignByBooleanSequentially(z, good, to_z_good);
        ArrayXd W_new_good = weights_good * (gprime.square() / varg);  // nobs_where_ngood,1
        assignByBooleanSequentially(W, good, W_new_good);
        good = W > two_epsilon;
        // --------------------------------------------------------------------
        // NB good changes here; cached versions invalidated
        // --------------------------------------------------------------------
        int n_good = good.cast<int>().sum();
        if (n_good < m) {
            addInfo(QString("Warning: tiny weights encountered (iteration "
                            "%1)").arg(m_n_iterations));
        }
        s_old = s;

        const MatrixXd S_u = S.matrixU();  // nobs,npred
        const ArrayXXd S_u_good = subsetByRowBoolean(S_u, good);  // nobs_where_ngood,npred
        // Note that mat[boolvec] gives a 1-d result, whereas
        // mat[boolvec,] gives a 2-d result.
        const ArrayXd W_good = subsetByElementBoolean(W, good);  // nobs_where_ngood,1
        const ArrayXd z_good = subsetByElementBoolean(z, good);  // nobs_where_ngood,1
        // Now, about W_good * S_u_good, where S_u_good is e.g. 20x2:
        // In R, if W_good is 20x1, you get a "non-conformable arrays" error,
        // but if W_good is a 20-length vector, it works, applying it across
        // all columns of S_u_good.
        // Let's create a new multiplication function:
        MatrixXd tmp_matrix_to_chol = CROSSPROD(
                    S_u_good,  // nobs_where_ngood,npred
                    multiply(W_good, S_u_good)  // nobs_where_ngood,npred
        );  // npred,npred
        MatrixXd C = chol(tmp_matrix_to_chol);  // npred,npred
        MatrixXd tmp_matrix_rhs = CROSSPROD(
                    S_u_good,  // nobs_where_ngood,npred
                    W_good * z_good  // nobs_where_ngood,1
        );  // npred,1
        s = forwardsolve(C.transpose(), tmp_matrix_rhs);  // npred,1
        s = backsolve(C, s);  // npred,1

        t = ArrayXd::Zero(m);  // nobs,1
        MatrixXd t_new_good = S_u_good.matrix() * s;  // nobs_where_ngood,1
        assignByBooleanSequentially(t, good, t_new_good);  // nobs,1

        // Converged?
        double euclidean_norm_of_change = (s - s_old).matrix().norm();
        // = sqrt(sum of squared values of (s - s_old))
        if (euclidean_norm_of_change < m_tolerance) {
            m_converged = true;
            break;
        }
    }

    VectorXd& x = m_coefficients;
    x = VectorXd(n).setConstant(NA);
    if (m_rank_deficiency_method == RankDeficiencyMethod::MinimumNorm) {
        S_d = tiny_singular_values.select(INF, S_d);
    }

    const ArrayXd t_good = subsetByElementBoolean(t, good);  // nobs_where_good,1
    const MatrixXd S_u = S.matrixU();  // nobs,npred
    const MatrixXd S_u_good = subsetByRowBoolean(S_u, good);  // nobs_where_good,npred
    const MatrixXd S_v = S.matrixV();
    const MatrixXd x_possible = S_v * ((1 / S_d) * CROSSPROD(
                                           S_u_good,
                                           t_good).array()).matrix();  // npred,1
    x = select_pred_bool.select(x_possible, x);

    m_fitted = true;
}


eigenfunc::IndexArray Glm::svdsubsel(const MatrixXd& A, int k)
{
    // As per http://bwlewis.github.io/GLM/svdss.html
    // Input:
    //      A: m*p matrix, m >= p
    //      k: number of output columns, k <= p
    // Returns a column array containing the COLUMN INDICES of the columns of A
    // that *estimates* the k most linearly independent columns of A.
    //
    // Note the differences from the original relating to Eigen being 0-based
    // versus R being 1-based in its indexing.

    using namespace eigenfunc;

    // Input validation as per requirements above:
    Q_ASSERT(A.rows() >= A.cols());
    // ... we will force k, as below

    int index_k = k - 1;
    if (index_k < 0 || index_k >= A.cols()) {
        index_k = A.cols() - 1;
    }
    JacobiSVD<MatrixXd> S = svd(scale(A, false, true));
    ArrayXd d = svd(A).singularValues().array();
    double epsilon = std::numeric_limits<double>::epsilon();
    IndexArray small_sv_indices = which(d < 2.0 * epsilon);
    if (small_sv_indices.size() > 0) {
        Index n = small_sv_indices(0);  // index of first small singular value
        if (index_k >= n) {
            index_k = n - 1;
            addInfo("k was reduced to match the rank of A");
        }
    }
    MatrixXd subsetted = subsetByColumnIndex(S.matrixV(), indexSeq(0, index_k)).transpose();  // k,?
    // The original uses qr(..., LAPACK=TRUE), and R's ?qr says "Using
    // LAPACK... uses column pivoting..." so the Eigen equivalent is probably:
    ColPivHouseholderQR<MatrixXd> Q = subsetted.colPivHouseholderQr();
    // Then, the original uses Q$pivot, which is a list of column indices in
    // R. Thanks to
    // https://stackoverflow.com/questions/26385561/how-to-get-matrix-pivot-index-in-c-eigen
    // we have:

    ArrayXi column_indices_int = Q.colsPermutation().indices();
    IndexArray column_indices = column_indices_int.cast<Index>();
    sort(column_indices);
    return column_indices;
}


#ifdef GLM_OFFER_R_GLM_FIT
void Glm::fitIRLSRglmfit()
{
    addInfo("Fitting GLM using IRLS as implemented by R's glm.fit");

    /*
    In R:
    - ?glm
    - ?glm.control  -- gives default epsilon, maxit
    - ?glm.fit -- default "method" to glm(), and the main fitting function
    */

    using namespace eigenfunc;

    // Input parameters and naming
    const int nobs = nObservations();
    const int nvars = nPredictors();
    const MatrixXd& x = m_predictors;  // nobs,nvars
    ArrayXd y = m_dependent_variable.array();  // nobs,1
    ArrayXd weights(nobs);  // nobs,1
    if (m_p_weights) {
        weights = m_p_weights->array();
    } else {
        weights = ArrayXd::Ones(nobs);
    }
    ArrayXd start;  // not implemented as a parameter
    ArrayXd etastart;  // not implemented as a parameter
    ArrayXd mustart;  // not implemented as a parameter
    ArrayXd offset = ArrayXd::Zero(nobs);  // specifying it not yet supported
    const LinkFunctionFamily& family = m_link_fn_family;
    // const bool intercept = true;  // specifying it not yet supported
    bool& conv = m_converged;
    const bool empty = nvars == 0;
    const LinkFunctionFamily::LinkFnType linkfun = family.link_fn;
    const LinkFunctionFamily::VarianceFnType& variance = family.variance_fn;
    const LinkFunctionFamily::InvLinkFnType& linkinv = family.inv_link_fn;
    const LinkFunctionFamily::ValidEtaFnType valideta = family.valid_eta_fn;
    const LinkFunctionFamily::ValidMuFnType validmu = family.valid_mu_fn;
    const LinkFunctionFamily::DerivativeInvLinkFnType mu_eta = family.derivative_inv_link_fn;
    const LinkFunctionFamily::InitializeFnType initialize = family.initialize_fn;
    const LinkFunctionFamily::DevResidsFnType dev_resids = family.dev_resids_fn;
    const double& epsilon = m_tolerance;
#ifdef LINK_FUNCTION_FAMILY_USE_AIC
    const LinkFunctionFamily::AICFnType& aic = family.aic_fn;
#endif
    int& iter = m_n_iterations;
    VectorXd& coef = m_coefficients;
    const int& maxit = m_max_iterations;
    const bool& trace = m_verbose;

    const double qr_tol = std::min(1e-07, epsilon / 1000);

    ArrayXd residuals;  // nobs,1
    ArrayXd eta;  // nobs,1
    ArrayXd mu;  // nobs,1
    double dev = 0.0;
    ArrayXd w;  // nobs,1
    ArrayXd z;  // nobs,1
    ArrayXb good;  // nobs,1
    ArrayXd n;  // nobs,1
    ArrayXd m;  // nobs,1
    bool boundary = false;

    // Initialize as the link family dictates
    if (mustart.size() == 0) {
        initialize(m_calculation_errors, family,
                   y, n, m, weights,
                   start, etastart, mustart);
    } else {
        ArrayXd mukeep(mustart);
        initialize(m_calculation_errors, family,
                   y, n, m, weights,
                   start, etastart, mustart);
        mustart = mukeep;
    }

    // Main bit
    if (empty) {
        eta = offset;
        if (!valideta(eta)) {
            addError("invalid linear predictor values in empty model");
            return;
        }
        mu = linkinv(eta);
        if (!validmu(mu)) {
            addError("invalid fitted means in empty model");
            return;
        }
        dev = dev_resids(y, mu, weights).sum();
        ArrayXd mu_eta_of_eta = mu_eta(eta);
        w = (
                    (weights * mu_eta_of_eta.square()) /
                    variance(mu)
            ).sqrt();
        residuals = (y - mu) / mu_eta_of_eta;
        good = ArrayXb(residuals.size());
        good.setConstant(true);
        boundary = true;
        conv = true;
        coef = VectorXd();
        iter = 0;
    } else {

        ArrayXd coefold;
        double devold;
        dqrls::DqrlsResult fit;

        // No prizes for code clarity in R...
        // Set eta.
        if (etastart.size() > 0) {
            eta = etastart;
        } else {
            if (start.size() > 0) {
                if (start.size() != nvars) {
                    addError(QString(
                                 "length of 'start' should equal %1 and "
                                 "correspond to initial coefs...").arg(nvars));
                    return;
                } else {
                    coefold = start;
                    eta = offset + (x * start.matrix()).array();
                }
            } else {
                eta = linkfun(mustart);
            }
        }

        mu = linkinv(eta);
        if (!validmu(mu) && valideta(eta)) {
            addError("cannot find valid starting values: please specify some");
            return;
        }

        devold = dev_resids(y, mu, weights).sum();
        boundary = false;
        conv = false;

        // --------------------------------------------------------------------
        // MAIN CALCULATION LOOP
        // --------------------------------------------------------------------
        for (iter = 1; iter <= maxit; ++iter) {

            // Checks
            good = weights > 0;
            ArrayXd varmu = subsetByElementBoolean(variance(mu), good);
            if (varmu.isNaN().any()) {
                addError("NAs in V(mu)");
                return;
            }
            if ((varmu == 0).any()) {
                addError("0s in V(mu)");
                return;
            }
            ArrayXd mu_eta_val = mu_eta(eta);
            if (subsetByElementBoolean(mu_eta_val.isNaN(), good).any()) {
                addError("NAs in d(mu)/d(eta)");
                return;
            }

            // ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            // "good" is reset here; don't rely on cached info
            // ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            good = (weights > 0) && (mu_eta_val != 0);
            if (!good.any()) {
                conv = false;
                addError(QString("no observations informative at iteration "
                                 "%1").arg(iter));
                break;
            }

            ArrayXd mu_eta_val_good = subsetByElementBoolean(mu_eta_val, good);
            z = subsetByElementBoolean(eta - offset, good) +
                    subsetByElementBoolean(y - mu, good) /
                    mu_eta_val_good;  // n_good,1
            w = (
                    (subsetByElementBoolean(weights, good) *
                        mu_eta_val_good.square()) /
                    subsetByElementBoolean(variance(mu), good)
                ).sqrt();  // n_good,1

            // ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            // Main moment of fitting
            // ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            ArrayXXd x_good = subsetByRowBoolean(x, good).array();
            ArrayXXd x_good_times_w = multiply(x_good, w);
            // ... in R, multiplication of a matrix(n_good, nvar) by a vector
            // of length (n_good)
            fit = dqrls::Cdqrls(x_good_times_w.matrix(),  // x
                                (z * w).matrix(),  // y
                                qr_tol,
                                false);  // check

            if (!fit.coefficients.array().isFinite().all()) {
                conv = false;
                addError(QString("non-finite coefficients at iteration "
                                 "%1").arg(iter));
                break;
            }
            if (nobs < fit.rank) {
                addError(QString("X matrix has rank %1, but only %2 "
                                 "observation(s)").arg(fit.rank).arg(nobs));
                return;
            }

            // start[fit$pivot] <- fit$coefficients
            // ... fit$pivot contained indices of pivoted columns
            // ... but we're using Eigen::FullPivHouseholderQR to do full
            //     pivoting, i.e. all
            start = fit.coefficients.array();

            // eta <- drop(x %*% start)
            // ... the drop() bit takes a one-dimensional matrix and makes a vector
            eta = (x * start.matrix()).array();

            // mu <- linkinv(eta <- eta + offset)
            // http://blog.revolutionanalytics.com/2008/12/use-equals-or-arrow-for-assignment.html
            eta = eta + offset;
            mu = linkinv(eta);

            dev = dev_resids(y, mu, weights).sum();
            if (trace) {
                addInfo(QString("Deviance = %1 Iterations - %2")
                        .arg(dev).arg(iter));
            }
            boundary = false;
            if (!std::isfinite(dev)) {
                if (coefold.size() == 0) {
                    addError("no valid set of coefficients has been found: "
                             "please supply starting values");
                    return;
                }
                addInfo("step size truncated due to divergence");
                int ii = 1;
                while (!std::isfinite(dev)) {
                    if (ii > maxit) {
                        addError("inner loop 1; cannot correct step size");
                        return;
                    }
                    ii += 1;
                    start = (start + coefold) / 2;
                    eta = (x * start.matrix()).array();
                    eta = eta + offset;
                    mu = linkinv(eta);
                    dev = dev_resids(y, mu, weights).sum();
                }
                boundary = true;
                if (trace) {
                    addInfo(QString("Step halved: new deviance = %1").arg(dev));
                }
            }
            if (!(valideta(eta) && validmu(mu))) {
                if (coefold.size() == 0) {
                    addError("no valid set of coefficients has been found: "
                             "please supply starting values");
                    return;
                }
                addInfo("step size truncated: out of bounds");
                int ii = 1;
                while (!(valideta(eta) && validmu(mu))) {
                    if (ii > maxit) {
                        addError("inner loop 2; cannot correct step size");
                        return;
                    }
                    ii += 1;
                    start = (start + coefold) / 2;
                    eta = (x * start.matrix()).array();
                    eta = eta + offset;
                    mu = linkinv(eta);
                }
                boundary = true;
                dev = dev_resids(y, mu, weights).sum();
                if (trace) {
                    addInfo(QString("Step halved: new deviance = %1").arg(dev));
                }
            }

            // ----------------------------------------------------------------
            // Converged?
            // ----------------------------------------------------------------
            if (std::abs(dev - devold) / (0.1 + std::abs(dev)) < epsilon) {
                conv = true;
                coef = start;
                break;
            } else {
                devold = dev;
                coef = start;
                coefold = start;
            }

        }

        if (!conv) {
            addError("algorithm did not converge");
        }
        if (boundary) {
            addError("algorithm stopped at boundary value");
        }
        const double eps = 10 * std::numeric_limits<double>::epsilon();
        if (family.family_name == LINK_FAMILY_NAME_BINOMIAL) {
            if ((mu > 1 - eps).any() || (mu < eps).any()) {
                addError("warning: fitted probabilities numerically 0 or 1 occurred");
            }
        }
        if (family.family_name == LINK_FAMILY_NAME_POISSON) {
            if ((mu < eps).any()) {
                addError("warning: fitted rates numerically 0 occurred");
            }
        }

        if (fit.rank < nvars) {
            // coef[fit$pivot][seq.int(fit$rank + 1, nvars)] <- NA
            addError("Not sure how to wipe out duff coefficients with full "
                     "pivoting; may be discrepancy with R");
        }

#if 0
        xxnames <- xnames[fit$pivot]
        residuals <- (y - mu)/mu.eta(eta)
        fit$qr <- as.matrix(fit$qr)
        nr <- min(sum(good), nvars)
        if (nr < nvars) {
            Rmat <- diag(nvars)
            Rmat[1L:nr, 1L:nvars] <- fit$qr[1L:nr, 1L:nvars]
        }
        else Rmat <- fit$qr[1L:nvars, 1L:nvars]
        Rmat <- as.matrix(Rmat)
        Rmat[row(Rmat) > col(Rmat)] <- 0
        names(coef) <- xnames
        colnames(fit$qr) <- xxnames
        dimnames(Rmat) <- list(xxnames, xxnames)
#endif

    }

#if 0
    ArrayXd wt = good.select(w.square(), 0);
    double wtdmu = intercept
            ? (weights * y).sum() / weights.sum()
            : linkinv(offset);
    double nulldev = dev_resids(y, wtdmu, weights);
    int n_ok = nobs - (weights == 0).cast<int>().sum();
    int nulldf = n_ok - static_cast<int>(intercept);
    int rank = empty ? 0 : fit.rank;
    int resdef = n_ok - rank;
    double aic_model = aic(y, n, mu, weights, dev) + 2 * rank;
    // skipped: return all the extra results
#endif

    m_fitted = true;
}
#endif
