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

#include "linkfunctionfamily.h"
#include "maths/statsfunc.h"


LinkFunctionFamily::LinkFunctionFamily(
        std::function<double(double)> link_fn,
        std::function<double(double)> inv_link_fn,
        std::function<double(double)> derivative_inv_link_fn,
        std::function<Eigen::ArrayXXd(const Eigen::ArrayXXd&)> variance_fn) :
    link_fn(link_fn),
    inv_link_fn(inv_link_fn),
    derivative_inv_link_fn(derivative_inv_link_fn),
    variance_fn(variance_fn)
{
}


const LinkFunctionFamily LINK_FN_FAMILY_LOGIT(
        statsfunc::logit,  // link
        static_cast<double (&)(double)>(statsfunc::logistic),  // inverse link
            // ... disambiguating overloaded function
            // ... https://stackoverflow.com/questions/10111042/wrap-overloaded-function-via-stdfunction
        statsfunc::derivativeOfLogistic,  // derivative of inverse link
        statsfunc::binomialVariance);  // variance function
