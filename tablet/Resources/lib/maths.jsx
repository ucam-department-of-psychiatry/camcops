// maths.jsx

/*
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
*/

/*jslint node: true, plusplus: true */
"use strict";

var pi = 3.141592653589793,
    piD2 = pi / 2;

// Logistic regression fitting by maximum likelihood estimation: adapted from
// http://statpages.org/logistic.html

function abs(x) {
    return Math.abs(x);
}

function sqrt(x) {
    return Math.sqrt(x);
}

function exp(x) {
    return Math.exp(x);
}

function ln(x) {
    return Math.log(x);
}

/*
function power(x, n) {
    return Math.pow(x, n);
}

function chiSq(x, n) {
    var q,
        p,
        k,
        t,
        a;
    // Returns a p value for chisq > x with n df.
    // R equivalent: 1 - pchisq(x, n)
    if (x > 1000 | n > 1000) {
        // normal approximation (Wilson-Hilferty transformation): http://en.wikipedia.org/wiki/Chi-squared_distribution
        q = Norm((power(x / n, 1 / 3) + 2 / (9 * n) - 1) / sqrt(2 / (9 * n))) / 2;
        if (x > n) {
            return q;
        } else {
            return 1 - q;
        }
    }
    p = Math.exp(-0.5 * x);
    if ((n % 2) == 1) {
        p = p * Math.sqrt(2 * x / pi)
    }
    k = n;
    while (k >= 2) {
        p = p * x / k;
        k = k - 2;
    }
    t = p;
    a = n;
    while (t > 1e-15 * p) {
        a = a + 2;
        t = t * x / a;
        p = p + t;
    }
    return 1 - p;
}

function Norm(z) {
    // Not sure exactly what this calculates. Norm(0) gives 0.61...
    var q = z * z;
    if (abs(z) > 7) {
        return (1 - 1 / q + 3 / (q * q)) * exp(-q / 2) / (abs(z) * sqrt(piD2));
    } else {
        return chiSq(q, 1);
    }
}
*/

function ArrayInitiallyZero(n) {
    var i;
    this.length = n;
    for (i = 0; i < this.length; i++) {
        this[i] = 0;
    }
}

function ix(j, k, nCols) {
    // for using an array as a matrix: obtain the index of a given location
    return j * nCols + k;
}

function logisticFitSinglePredictor(xvalues, yvalues) {
    if (xvalues.length !== yvalues.length) {
        // sanity check
        return null;
    }
    var x, // original code polluted the global namespace
        i = 0,
        j = 0,
        k = 0,
        // l = 0,
        nC = xvalues.length, // number of data points
        nR = 1, // number of predictor variables
        nP = nR + 1,
        nP1 = nP + 1,
        sY0 = 0,
        sY1 = 0,
        sC = 0,
        X = new ArrayInitiallyZero(nC * (nR + 1)),
        Y0 = new ArrayInitiallyZero(nC),
        Y1 = new ArrayInitiallyZero(nC),
        xM = new ArrayInitiallyZero(nR + 1),
        xSD = new ArrayInitiallyZero(nR + 1),
        Par = new ArrayInitiallyZero(nP),
        SEP = new ArrayInitiallyZero(nP),
        Arr = new ArrayInitiallyZero(nP * nP1),
        lnV = 0,
        ln1mV = 0,
        LLp = 2e+10, // previous model's log-likelihood
        LL = 1e+10, // current model's log-likelihood
        v,
        q,
        xij,
        s;

    // RNC data entry for a single predictor:
    for (i = 0; i < nC; ++i) {
        X[ix(i, 0, nR + 1)] = 1;
        X[ix(i, 1, nR + 1)] = xvalues[i];
        if (yvalues[i] === 0) {
            Y0[i] = 1;
            sY0 = sY0 + 1;
        } else {
            Y1[i] = 1;
            sY1 = sY1 + 1;
        }
        sC = sC + (Y0[i] + Y1[i]);
        x = X[ix(i, 1, nR + 1)];
        xM[1] = xM[1] + (Y0[i] + Y1[i]) * x;
        xSD[1] = xSD[1] + (Y0[i] + Y1[i]) * x * x;
    }

    /*
    var da = Xlate(form.data.value, Tb, ",");
    form.data.value = da;
    if (da.indexOf(NL) == -1) {
        if (da.indexOf(CR) > -1) {
            NL = CR
        } else {
            NL = LF
        }
    }
    for ( i = 0; i < nC; i++) {
        X[ix(i, 0, nR + 1)] = 1;
        l = da.indexOf(NL);
        if (l == -1) {
            l = da.length
        };
        var v = da.substring(0, l);
        da = da.substring(l + NL.length, da.length);
        for ( j = 1; j <= nR; j++) {
            l = v.indexOf(",");
            if (l == -1) {
                l = v.length
            };
            x = eval(v.substring(0, l))
            X[ix(i, j, nR + 1)] = x;
            v = v.substring(l + 1, v.length);
        }
        if (form.Grouped.checked == "1") {
            l = v.indexOf(",");
            if (l == -1) {
                l = v.length
            };
            x = eval(v.substring(0, l))
            Y0[i] = x;
            sY0 = sY0 + x;
            v = v.substring(l + 1, v.length);
            l = v.indexOf(",");
            if (l == -1) {
                l = v.length
            };
            x = eval(v.substring(0, l))
            Y1[i] = x;
            sY1 = sY1 + x;
            v = v.substring(l + 1, v.length);
        } else {
            x = eval(v.substring(0, l));
            if (x == 0) {
                Y0[i] = 1;
                sY0 = sY0 + 1
            } else {
                Y1[i] = 1;
                sY1 = sY1 + 1
            }
        }
        sC = sC + (Y0[i] + Y1[i]);
        for ( j = 1; j <= nR; j++) {
            x = X[ix(i, j, nR + 1)];
            xM[j] = xM[j] + (Y0[i] + Y1[i]) * x;
            xSD[j] = xSD[j] + (Y0[i] + Y1[i]) * x * x;
        }
    }
    */

    /*
    var o = "Descriptives..." + NL;

    o = o + (NL + sY0 + " cases have Y=0; " + sY1 + " cases have Y=1." + NL );

    o = o + (NL + " Variable     Avg       SD    " + NL );
    */

    // Calculate means and standard deviations for each predictor
    // (including predictor 0, the intercept)
    for (j = 1; j <= nR; j++) {
        xM[j] = xM[j] / sC;
        xSD[j] = xSD[j] / sC;
        xSD[j] = sqrt(abs(xSD[j] - xM[j] * xM[j]));
        /*
        o = o + ("   " + Fmt3(j) + "    " + Fmt(xM[j]) + Fmt(xSD[j]) + NL );
        */
    }
    xM[0] = 0;
    xSD[0] = 1;

    // Normalize observations
    for (i = 0; i < nC; i++) {
        for (j = 1; j <= nR; j++) {
            X[ix(i, j, nR + 1)] = (X[ix(i, j, nR + 1)] - xM[j]) / xSD[j];
        }
    }

    /*
    o = o + (NL + "Iteration History..." );
    form.output.value = o;
    */

    Par[0] = ln(sY1 / sY0);
    for (j = 1; j <= nR; j++) {
        Par[j] = 0;
    }

    // Iterate:
    while (abs(LLp - LL) > 0.0000001) {
        LLp = LL;
        LL = 0;
        for (j = 0; j <= nR; j++) {
            for (k = j; k <= nR + 1; k++) {
                Arr[ix(j, k, nR + 2)] = 0;
            }
        }

        for (i = 0; i < nC; i++) {
            v = Par[0];
            for (j = 1; j <= nR; j++) {
                v = v + Par[j] * X[ix(i, j, nR + 1)];
            }
            if (v > 15) {
                lnV = -exp(-v);
                ln1mV = -v;
                q = exp(-v);
                v = exp(lnV);
            } else {
                if (v < -15) {
                    lnV = v;
                    ln1mV = -exp(v);
                    q = exp(v);
                    v = exp(lnV);
                } else {
                    v = 1 / (1 + exp(-v));
                    lnV = ln(v);
                    ln1mV = ln(1 - v);
                    q = v * (1 - v);
                }
            }
            LL = LL - 2 * Y1[i] * lnV - 2 * Y0[i] * ln1mV;
            for (j = 0; j <= nR; j++) {
                xij = X[ix(i, j, nR + 1)];
                Arr[ix(j, nR + 1, nR + 2)] = Arr[ix(j, nR + 1, nR + 2)] + xij * (Y1[i] * (1 - v) + Y0[i] * (-v));
                for (k = j; k <= nR; k++) {
                    Arr[ix(j, k, nR + 2)] = Arr[ix(j, k, nR + 2)] + xij * X[ix(i, k, nR + 1)] * q * (Y0[i] + Y1[i]);
                }
            }
        }

        /*
        o = o + (NL + "-2 Log Likelihood = " + Fmt(LL) );
        if (LLp == 1e+10) {
            Lln = LL;
            o = o + " (Null Model)"
        }
        form.output.value = o;
        */

        for (j = 1; j <= nR; j++) {
            for (k = 0; k < j; k++) {
                Arr[ix(j, k, nR + 2)] = Arr[ix(k, j, nR + 2)];
            }
        }

        for (i = 0; i <= nR; i++) {
            s = Arr[ix(i, i, nR + 2)];
            Arr[ix(i, i, nR + 2)] = 1;
            for (k = 0; k <= nR + 1; k++) {
                Arr[ix(i, k, nR + 2)] = Arr[ix(i, k, nR + 2)] / s;
            }
            for (j = 0; j <= nR; j++) {
                if (i !== j) {
                    s = Arr[ix(j, i, nR + 2)];
                    Arr[ix(j, i, nR + 2)] = 0;
                    for (k = 0; k <= nR + 1; k++) {
                        Arr[ix(j, k, nR + 2)] = Arr[ix(j, k, nR + 2)] - s * Arr[ix(i, k, nR + 2)];
                    }
                }
            }
        }

        for (j = 0; j <= nR; j++) {
            Par[j] = Par[j] + Arr[ix(j, nR + 1, nR + 2)];
        }

    }

    /*
    o = o + (" (Converged)" + NL );
    var CSq = Lln - LL;
    o = o + (NL + "Overall Model Fit..." + NL + "  Chi Square=" + Fmt(CSq) + ";  df=" + nR + ";  p=" + Fmt(chiSq(CSq, nR)) + NL );

    o = o + (NL + "Coefficients and Standard Errors..." + NL );
    o = o + (" Variable     Coeff.    StdErr       p" + NL );
    */
    for (j = 1; j <= nR; j++) {
        Par[j] = Par[j] / xSD[j];
        SEP[j] = sqrt(Arr[ix(j, j, nP + 1)]) / xSD[j];
        Par[0] = Par[0] - Par[j] * xM[j];
        // o = o + ("   " + Fmt3(j) + "    " + Fmt(Par[j]) + Fmt(SEP[j]) + Fmt(Norm(abs(Par[j] / SEP[j]))) + NL );
    }
    /*
    o = o + ("Intercept " + Fmt(Par[0]) + NL );

    o = o + (NL + "Odds Ratios and 95% Confidence Intervals..." + NL );
    o = o + (" Variable      O.R.      Low  --  High" + NL );
    for ( j = 1; j <= nR; j++) {
        var ORc = exp(Par[j]);
        var ORl = exp(Par[j] - 1.96 * SEP[j]);
        var ORh = exp(Par[j] + 1.96 * SEP[j]);
        o = o + ("   " + Fmt3(j) + "    " + Fmt(ORc) + Fmt(ORl) + Fmt(ORh) + NL + NL );
    }

    for (j = 1; j <= nR; j++) {
        v = "          X" + j;
        o = o + v.substring(v.length - 10, v.length);
    }
    if (form.Grouped.checked == "1") {
        o = o + ("           n0           n1 Calc Prob" + NL )
    } else {
        o = o + ("            Y Calc Prob" + NL )
    }
    for (i = 0; i < nC; i++) {
        v = Par[0];
        for (j = 1; j <= nR; j++) {
            x = xM[j] + xSD[j] * X[ix(i, j, nR + 1)];
            v = v + Par[j] * x;
            o = o + Fmt(x);
        }
        v = 1 / (1 + exp(-v) );
        if (form.Grouped.checked == "1") {
            o = o + ("    " + Fmt9(Y0[i]) + "    " + Fmt9(Y1[i]) + Fmt(v) + NL )
        } else {
            o = o + ("    " + Fmt9(Y1[i]) + Fmt(v) + NL )
        }
    }

    form.output.value = o;
    */

    return Par;
    // array of parameters: Par[0] is intercept, Par[1] is first
    // predictor's coefficient (slope)
}

// RNC
function logisticDescriptives(par) {
    /*
        These parameters define a linear equation in logits,
            L(X) = intercept + slope * X
        The logistic function itself is
            P = plogis(L) = 0.5 * (1 + tanh(L/2)) = 1 / (1 + exp(-L))
        So that's
            P = 1 / (1 + exp(-intercept - slope * X))
        Comparing to Lecluyse & Meddis (2009)'s function,
            p = 1 / (1 + exp(-k(X - theta))) = 1 / (1 + exp(-k*X + k*theta))),
        we have
            k = slope
        and
            theta = -intercept/k = -intercept/slope
    */
    var intercept = par[0],
        slope = par[1],
        k = slope,
        theta = -intercept / slope; // also the x50 value
    return {
        intercept: intercept,
        slope: slope,
        k: k,
        theta: theta
    };
}

function logisticFindXWhereP(p, slope, intercept) {
    /*
        P = 1 / (1 + exp(-intercept - slope * X))
        1 = P + P * exp(-intercept - slope * X)
        -intercept - slope*X = ln((1 - P) / P)
        intercept + slope * X = ln(P / (1 - P))
        X = (ln(P / (1 - P)) - intercept) / slope
    */
    return (ln(p / (1 - p)) - intercept) / slope;
}
