..  docs/source/tasks/edeq.rst

..  Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).
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


.. _edeq:

Eating Disorder Examination Questionnaire (EDE-Q 6.0)
-----------------------------------------------------

.. include:: include_data_collection_plus_local_upgrade.rst

The EDE-Q is the self-report questionnaire version of the Eating Disorder
Examination (EDE) interview. There are 28 questions, and four subscales. To
calculate a subscale score, calculate the arithmetic mean of the relevant rated
items in the scale (listed below). The overall 'global' score is the arithmetic
mean of the four subscales.

In our implementation all applicable questions are mandatory so all items will
have been rated.

.. todo:: EDE-Q: no longer all mandatory? Mark which aren't, if so.


Subscale items (the numbers are the item number on the EDE-Q):
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Restraint:

- 1. Restraint over eating
- 2. Avoidance of eating
- 3. Food avoidance
- 4. Dietary rules
- 5. Empty stomach

Eating concern:

- 7. Preoccupation with food, eating or calories
- 9. Fear of losing control over eating
- 19. Eating in secret
- 20. Guilt about eating
- 21. Social eating

Shape concern:

- 6. Flat stomach
- 8. Preoccupation with shape or weight
- 10. Fear of weight gain
- 11. Feelings of fatness
- 23. Importance of shape
- 26. Dissatisfaction with shape
- 27. Discomfort seeing body
- 28. Avoidance of exposure

Weight concern:

- 8. Preoccupation with shape or weight
- 12. Desire to lose weight
- 22. Importance of weight
- 24. Reaction to prescribed weighing
- 25. Dissatisfaction with weight

Note: questions 13-18, which ask for specific event counts, are not included in
these four subscales.


Intellectual property rights
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- EDE-Q 6.0: Copyright 2008 Christopher G. Fairburn and Sarah J. Beglin.

  - https://www.corc.uk.net/media/1273/ede-q_quesionnaire.pdf
  - https://web.archive.org/web/20111124145321/https://www.rcpsych.ac.uk/pdf/EDE-Q.pdf

  - "The EDE-Q (and its items) is under copyright. It is freely available for
    non-commercial research use only and no permission need to be sought. For
    commercial use of the EDE-Q contact: credo@medsci.ox.ac.uk"
    (https://web.archive.org/web/20220211220229/https://www.corc.uk.net/outcome-experience-measures/eating-disorder-examination-questionnaire-ede-q/)


History
~~~~~~~

- EDE: e.g.

  - Fairburn CG, Cooper Z (1993). The Eating Disorder Examination (twelfth
    edition). In: Fairburn CG, Wilson GT (eds.).
    *Binge Eating: Nature, Assessment and Treatment* (pp. 317-360).
    New York: Guilford Press.

- The EDE-Q is a self-report version of the EDE:

  - Fairburn CG, Beglin SJ (1994). Assessment of eating disorder
    psychopathology: interview or self-report questionnaire?
    *International Journal of Eating Disorders* 16: 363-370.
    https://pubmed.ncbi.nlm.nih.gov/7866415/


Source
~~~~~~

- https://doi.apa.org/doiLanding?doi=10.1037%2Ft03974-000
- https://web.archive.org/web/20111124145321/https://www.rcpsych.ac.uk/pdf/EDE-Q.pdf
- https://www.corc.uk.net/media/1273/ede-q_quesionnaire.pdf
- https://www.corc.uk.net/media/1274/ede_rcpsychinformation.pdf (scoring)
- https://www.semanticscholar.org/paper/Eating-Disorder-Examination-Questionnaire-Fairburn-Beglin/627948c2fba5c7f6d5241aaec7e308875ab026a5?p2df
- Fairburn CG, Beglin SJ (1994). Eating Disorder Examination Questionnaire
  (EDE-Q) [Database record]. APA PsycTests. https://doi.org/10.1037/t03974-000
- https://www.corc.uk.net/outcome-experience-measures/eating-disorder-examination-questionnaire-ede-q/
- Rand-Giovannetti et al. (2020), https://pubmed.ncbi.nlm.nih.gov/29094603/
