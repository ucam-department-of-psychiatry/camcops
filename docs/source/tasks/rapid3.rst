..  docs/source/tasks/rapid3.rst

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


.. _rapid3:

Routine Assessment of Patient Index Data (RAPID3)
-------------------------------------------------

.. include:: include_data_collection_plus_local_upgrade.rst

An index to assess and monitor patients with rheumatoid arthritis, without
formal joint counts.

RAPID3 includes an assessment of physical function, a patient global assessment
(PGA) for pain, and a PGA for global health.

To calculate RAPID3, the raw 0–3 scores for physical function from 10 questions
of the multidimensional Health Assessment Questionnaire (MDHAQ) are summed
(totalling 0–30) and converted to 0–10 by dividing by 3. Pain and global health
are assessed according to 10 cm "patient global assessment (PGA)" visual
analogue scales (VAS), both scoring 0–10. The three 0–10 scores (for physical
function, pain VAS and global VAS) are added together for a raw score of 0–30
(the "RAPID3 cumulative score"). This is sometimes divided by 3 to give an
adjusted 0–10 score for comparison with other RAPID indices.


Intellectual property rights
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Email from Amanda Rosett at RWS to Joel Parkinson on 7th December 2020:

https://www.the-rheumatologist.org/article/remote-use-of-the-multidimensional-health-assessment-questionnaire-mdhaq/4/
states "Dr. Theodore Pincus is president of Medical History Services LLC and
holds a copyright and trademark on MDHAQ and RAPID3, for which he receives
royalties and license fees, all of which are used to support further development
of quantitative questionnaire measurements for patients and doctors in clinical
rheumatology care."

https://www.corptransinc.com/sites/mdhaq-rapid3/instrument-information/permissions-licenses
states "The MDHAQ/RAPID3 is available to academic researchers without fees." and
"Implementation of the MDHAQ/RAPID3 in an electronic medical record (EMR) is
subject to a royalty or license fee, which goes for support of further
development of the MDHAQ/RAPID3."

.. code-block:: none

    [...]

    With respect to integration into CamCOPS - individual users must obtain a
    license for use of the RAPID-3 for their projects. Therefore, we can't
    allow the RAPID-3 to be hosted and made publicly available at no cost. The
    RAPID-3 can be integrated and administered via tablet device for any user
    who has a license to use the scale in their individual project/clinic.

    [... Licensing Solutions Lead for RWS Life Sciences (rws.com) to Joel
    Parkinson, 7 Dec 2020]


History
~~~~~~~

MDHAQ:

- Pincus T, Swearingen C, Wolfe F (1999).
  Toward a multidimensional health assessment questionnaire (MDHAQ): Assessment
  of advanced activities of daily living and psychological status in the
  patient‐friendly health assessment questionnaire format.
  *Arthritis Rheum.* 42(10):2220-30.
  https://pubmed.ncbi.nlm.nih.gov/10524697/

  [RAPID3 includes a subset of the core variables found in the MDHAQ (Q1a-h, k,
  n-o, q-r) and the PGA for pain (Q2)]

RAPID3:

- Pincus T, Swearingen CJ, Bergman M, Yazici Y (2008).
  RAPID3 (routine assessment of patient index data 3), a rheumatoid arthritis
  index without formal joint counts for routine care: proposed severity
  categories compared to DAS and CDAI categories.
  J Rheumatol 2008;35:2136–47.
  https://pubmed.ncbi.nlm.nih.gov/18793006/

- Pincus T, Yazici Y, Bergman MJ (2009).
  RAPID3, an index to assess and monitor patients with rheumatoid arthritis,
  without formal joint counts: similar results to DAS28 and CDAI in clinical
  trials and clinical care.
  *Rheum Dis Clin North Am.* 35(4):773-8, viii.
  https://pubmed.ncbi.nlm.nih.gov/19962621/


Source
~~~~~~

- https://www.rheumatology.org/Portals/0/Files/RAPID3%20Form.pdf
