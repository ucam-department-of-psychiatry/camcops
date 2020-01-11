..  docs/source/tasks/kirby.rst

..  Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).
    .
    This file is part of CamCOPS.
    .
    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    .
    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    .
    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

.. _kirby_mcq:

Kirby Monetary Choice Questionnaire (MCQ)
-----------------------------------------

Series of hypothetical choices pitting an immediate amount of money against a
delayed amount of money, to measure delay discounting.


History
~~~~~~~

- Kirby et al. (1999) [27-item version].

- Based on the earlier 21-item version: Kirby & Maraković (1996).

Source
~~~~~~

- From Kirby et al. (1999) as above.


Calculations
~~~~~~~~~~~~

.. math markup: see ftp://ftp.ams.org/ams/doc/amsmath/short-math-guide.pdf

**Hyperbolic delay discounting.** The principle is to judge the value :math:`V`
of two options, :math:`V_1` and :math:`V_2`. Each has an amount :math:`A_1`,
:math:`A_2` and a delay :math:`D_1`, :math:`D_2`. Hyperbolic delay discounting
is assumed, according to the discounting parameter :math:`k`:

.. math::

    V = \frac{A}{1 + k D}

In the case of the Kirby MCQ, one option has zero delay (the small immediate
reward or SIR -- call it option 1): :math:`D_1 = 0`. One has a delay (the large
delayed reward or LDR -- call it option 2).

The values are therefore:

.. math::

    V_1 = \frac{A_1}{1 + k D_1} = A_1

    V_2 = \frac{A_2}{1 + k D_2}

At indifference:

.. math::

    V_1 = V_2

so at indifference:

.. math::

    A_1 = \frac{A_2}{1 + k D_2}

    \frac{A_2}{A_1} = 1 + k D_2

    k = \frac{\frac{A_2}{A_1} - 1}{D_2} = \frac{A_2 - A_1}{A_1 D_2}

Given a set of trials, a subject's indifference point :math:`k` can be
calculated in various ways.

**Kirby’s method (Kirby et al. 1999; Kirby, 2000).** For each question, at
indifference, :math:`k_{\text{indiff}}` can be calculated from the equations
above via :math:`k_{\text{indiff}} = \frac{A_2 - A_1}{A_1 D_2}`. Kirby’s method
compares subject’s choices against these indifference :math:`k` values: if the
subject chooses the delayed option, then :math:`k < k_{\text{indiff}}`, and if
the subject chooses the immediate option, then :math:`k > k_{\text{indiff}}`.
For a consistent series of choices, the geometric mean of the tested :math:`k`
values straddling the subject’s indifference point is taken as the subject’s
:math:`k` value. If the subject’s :math:`k` value falls outside the tested
range (i.e. all choices were for the immediate, or all for the delayed,
option), then the most extreme assessed :math:`k` is used. Where choices are
not consistent, then the subject’s value of :math:`k` is taken as the :math:`k`
value with which the subject’s choices were most consistent (i.e. the most
choices were as predicted by that value of :math:`k`) or, if there is no clear
winner, the geometric mean of multiple possible tested :math:`k` values that
were equally and maximally consistent with the subject’s choice. This geometric
mean approach reduces to the simple ‘consistent’ approach for consistent
choices, and thus may be used throughout.

**Wileyto et al.’s method (Wileyto et al., 2004).** This method defines the
reward ratio :math:`R = \frac{A_1}{A_2}`, and then predicts the probability
:math:`p` of choosing the delayed response using a logistic regression,
:math:`p = \frac{e^y}{1 + e^y} = \frac{1}{1 + e^{–y}}` where :math:`y =
\beta_1(1 – \frac{1}{R}) + \beta_2 D_2`. That is, :math:`1 – \frac{A_2}{A_1}`
and :math:`D_2` are used as predictors, obtaining the coefficients
:math:`\beta_1` and :math:`\beta_2`. At indifference, where :math:`y = 0`, this
gives :math:`R = \frac{1}{1 + \frac{\beta_2}{\beta_1} D_2}`, and hence :math:`k`
is estimated by :math:`\frac{\beta_2}{\beta_1}`. However, it is possible for
such estimates to be negative under conditions of inconsistent choice.

.. todo:: Reference RNC new method when published.

:math:`\frac{1}{k}` is the delay at which a prospective reward has decayed to
half its original value.


Intellectual property rights
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Believed to contain no significant intellectual property, aside from the code,
which is part of CamCOPS.


References
~~~~~~~~~~

Kirby KN, Petry NM, Bickel WK (1999).
Heroin addicts have higher discount rates for delayed rewards than
non-drug-using controls.
*Journal of Experimental Psychology: General* 128: 78-87.
https://www.ncbi.nlm.nih.gov/pubmed/10100392

Kirby KN, Maraković NN (1996).
Delay-discounting probabilistic rewards: Rates decrease as amounts increase.
*Psychon. Bull. Rev.* 3: 100-104.
https://www.ncbi.nlm.nih.gov/pubmed/24214810;
https://doi.org/10.3758/BF03210748.

Kirby KN (2000) Instructions for inferring discount rates from choices between
immediate and delayed rewards. Unpublished, Williams College.

Wileyto EP, Audrain-McGovern J, Epstein LH, Lerman C (2004).
Using logistic regression to estimate delay-discounting functions.
*Behav Res Methods Instrum Comput J Psychon Soc Inc* 36: 41–51.
https://www.ncbi.nlm.nih.gov/pubmed/15190698.
