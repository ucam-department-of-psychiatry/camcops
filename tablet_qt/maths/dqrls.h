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
#include <Eigen/Dense>
#include <QStringList>

// See:
// - http://adv-r.had.co.nz/C-interface.html
// - R's lm.c

namespace dqrls {


struct DqrlsResult {
    bool success = false;
    Eigen::FullPivHouseholderQR<Eigen::MatrixXd> qr;
    Eigen::MatrixXd coefficients;
    // Eigen::ArrayXXd residuals;
    // Eigen::ArrayXXd effects;
    int rank;
    // Eigen::ArrayXi pivot;  // INDICES, 0-based here, 1-based in R
    // Eigen::ArrayXd qraux;
    double tol;
    bool pivoted;
    QStringList errors;
};


DqrlsResult Cdqrls(const Eigen::MatrixXd& x,
                   const Eigen::MatrixXd& y,
                   double tol,
                   bool check = true);


}  // namespace dqrls
