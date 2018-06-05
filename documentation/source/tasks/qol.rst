..  documentation/source/tasks/qol.rst

..  Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).
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

.. _qol:

Quality of Life
---------------

.. include:: include_under_development.rst

(Standard Gamble version under development.)

Tasks
~~~~~

- The QOL-Basic task provides a rating scale and a time trade-off measure.

- The QOL-SG task provides a standard gamble.

History and guide
~~~~~~~~~~~~~~~~~

Review articles:

- Torrance (1986), http://www.ncbi.nlm.nih.gov/pubmed/10311607 — includes
  references to validation of TTO method (against standard gamble, for states
  preferred to death).

- Torrance (1987), http://www.ncbi.nlm.nih.gov/pubmed/3298297; reviews
  SG/TTO/RS methods; RS is valid only after power-curve correction.

- Torrance & Feeny (1989), http://www.ncbi.nlm.nih.gov/pubmed/2634630, on QALYs
  and the use of utilities as the weight for them (defining cost–utility
  analysis, a subset of cost-effectiveness analysis).

- Guyatt et al. (1989), http://www.ncbi.nlm.nih.gov/pubmed/2655856.

Source
~~~~~~

- Time trade-off and rating scale methods: Burström et al. 2006,
  http://www.ncbi.nlm.nih.gov/pubmed/16214258.

- Standard gamble: primarily from Torrance (1986, 1989), as above.

Some other relevant papers:

- Buitinga et al. (2012), http://www.ncbi.nlm.nih.gov/pubmed/22730908.

Note also the standard gamble method (Torrance 1986):

- *Utility 0–1.* Standard gamble method for chronic states preferred to death:
  alternative 1 is {probability |p| → health for the rest of one’s life (|t|
  years), probability 1 – |p| → instant death}; alternative 2 is the chronic
  state |i| for the rest of one’s life (|t| years). The probability p is varied
  until the subject is indifferent, at which point the utility is |p|, i.e.
  h\ :subscript:`i` = |p|.

.. subscript: see http://docutils.sourceforge.net/docs/ref/rst/roles.html#subscript
.. subscript + italic... ?
.. Might be possible to create a recursive parser (see my efforts in that
   direction in conf.py), but not pursued for now.

- Standard gamble usually implemented with a visual aid for probabilities (e.g.
  proportions of a coloured wheel).

- Alternatives other than health/death possible, as long as one of the
  “alternative 1” options is preferred to the current state, and one is
  dispreferred to it.

- *Utility < 0.* For chronic states considered worse than death, the technique
  is modified: Alternative 1 is {|p| → health, 1 – |p| → current state},
  alternative 2 is death; |h| = –|p| / (1 – |p|).

- For temporary health states, intermediate states are measured relative to the
  best state (healthy) and a worse/worst temporary state.

- *Extension for utility > 1 (RNC addition).* For chronic states considered
  better than normal health (potentially: mania), a logical extension is as
  follows. alternative 1 is {|p| → current state, 1 – |p| → dead}, alternative
  2 is normal full health. If indifferent, |p| × |h| + (1 – |p|) × 0 = 1 × 1 ⇒
  |h| = 1 / |p|.

- Internal consistency of SG versus modifications for prospect theory: Oliver
  (2003), http://www.ncbi.nlm.nih.gov/pubmed/12842320.

- What the SG measures, inc. the importance of the (typically ignored) time
  dimension: Gafni (1994), http://www.ncbi.nlm.nih.gov/pubmed/8005790.

Note regarding comparison between utilities/QALYs:

- Is a change in utility from 0.2–0.4 equal to a change from 0.6–0.8? Yes,
  under *uncertainty*: see http://www.ncbi.nlm.nih.gov/pubmed/17067192.

Intellectual property rights
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Believed to contain no significant intellectual property, aside from the code,
which is part of CamCOPS.

.. |h| replace:: *h*

.. |i| replace:: *i*

.. |p| replace:: *p*

.. |q| replace:: *q*

.. |t| replace:: *t*
