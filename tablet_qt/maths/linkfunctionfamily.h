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
#include <functional>


class LinkFunctionFamily
{
public:
    LinkFunctionFamily(
            std::function<double(double)> link_fn,
            std::function<double(double)> inv_link_fn,
            std::function<double(double)> derivative_inv_link_fn,
            std::function<Eigen::ArrayXXd(const Eigen::ArrayXXd&)> variance_fn);
public:
    // Link function (e.g. logit):
    std::function<double(double)> link_fn;

    // Inverse link function (e.g. logistic):
    std::function<double(double)> inv_link_fn;

    // Derivative of the inverse link function ("mu.eta" in R):
    std::function<double(double)> derivative_inv_link_fn;

    // Variance function: gives the variance as a function of the mean; "the
    // part of the variance that depends on" the mean.
    // https://en.wikipedia.org/wiki/Variance_function
    // If the variance is independent of the mean, then this should return a
    // constant, probably 1.
    std::function<Eigen::ArrayXXd(const Eigen::ArrayXXd&)> variance_fn;
};


extern const LinkFunctionFamily LINK_FN_FAMILY_IDENTITY;
extern const LinkFunctionFamily LINK_FN_FAMILY_LOGIT;
