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

#include "linkfunctionfamily.h"
#include "maths/statsfunc.h"


LinkFunctionFamily::LinkFunctionFamily(
        const QString& family_name,
        const LinkFnType& link_fn,
        const InvLinkFnType& inv_link_fn,
        const DerivativeInvLinkFnType& derivative_inv_link_fn,
        const VarianceFnType& variance_fn,
        const DevResidsFnType& dev_resids_fn,
        const ValidEtaFnType& valid_eta_fn,
        const ValidMuFnType& valid_mu_fn,
        const InitializeFnType& initialize_fn
#ifdef LINK_FUNCTION_FAMILY_USE_AIC
        , const AICFnType& aic_fn
#endif
        ) :
    family_name(family_name),
    link_fn(link_fn),
    inv_link_fn(inv_link_fn),
    derivative_inv_link_fn(derivative_inv_link_fn),
    variance_fn(variance_fn),
    dev_resids_fn(dev_resids_fn),
    valid_eta_fn(valid_eta_fn),
    valid_mu_fn(valid_mu_fn),
    initialize_fn(initialize_fn)
#ifdef LINK_FUNCTION_FAMILY_USE_AIC
    , aic_fn(aic_fn)
#endif
{
}


const QString LINK_FAMILY_NAME_GAUSSIAN("gaussian");
const QString LINK_FAMILY_NAME_BINOMIAL("binomial");
const QString LINK_FAMILY_NAME_POISSON("poisson");


// Disambiguating overloaded functions:
// - https://stackoverflow.com/questions/10111042/wrap-overloaded-function-via-stdfunction

const LinkFunctionFamily LINK_FN_FAMILY_LOGIT(
        LINK_FAMILY_NAME_BINOMIAL,  // family_name
        statsfunc::logitArray,  // link
        statsfunc::logisticArray,  // inverse link
        statsfunc::derivativeOfLogisticArray,  // derivative of inverse link
        statsfunc::binomialVariance,  // variance function
        statsfunc::binomialDevResids,  // dev_resids_fn
        statsfunc::alwaysTrue,  // valid_eta_fn
        statsfunc::binomialValidMu,  // valid_mu_fn
        statsfunc::binomialInitialize  // initialize_fn
#ifdef LINK_FUNCTION_FAMILY_USE_AIC
        , statsfunc::binomialAIC  // aic_fn
#endif
);


const LinkFunctionFamily LINK_FN_FAMILY_GAUSSIAN(
        LINK_FAMILY_NAME_GAUSSIAN,  // family_name
        statsfunc::identityArray,  // link
        statsfunc::identityArray,  // inverse link
        statsfunc::oneArray,  // derivative of inverse link (y = x => y' = 1)
        statsfunc::oneArray,  // variance function
            // ... ?assumes normality; variance is independent of the mean
            // ... https://en.wikipedia.org/wiki/Variance_function#Example_.E2.80.93_normal
        statsfunc::gaussianDevResids,  // dev_resids_fn
        statsfunc::alwaysTrue,  // valid_eta_fn
        statsfunc::alwaysTrue,  // valid_mu_fn
        statsfunc::gaussianInitialize  // initialize_fn
#ifdef LINK_FUNCTION_FAMILY_USE_AIC
        , statsfunc::gaussianAIC  // aic_fn
#endif
);

// For link function families, see also:
// - https://stats.stackexchange.com/questions/212430/what-are-the-error-distribution-and-link-functions-of-a-model-family-in-r
// - https://en.wikipedia.org/wiki/Generalized_linear_model#Link_function
// - R: ?family
