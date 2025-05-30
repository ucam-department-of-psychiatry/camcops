..  docs/source/user_client/include_tabletdefs.rst

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

.. role:: tabletcurrentpatient
.. role:: tabletnopatientselected
.. .. role:: tabletmenu
.. role:: missingtext
.. role:: unselectedtext
.. role:: selectedtext

.. The "tabletmenu" role is registered in conf.py, so we can use substitutions
   inside it.

.. https://stackoverflow.com/questions/4669689/how-to-use-color-in-text-with-restructured-text-rst2html-py-or-how-to-insert-h
.. https://stackoverflow.com/questions/3702865/sphinx-restructuredtext-set-color-for-a-single-word/9753677
.. then see conf.py for the CSS


.. |addiction| image:: ../_app_icons/addiction.png
   :align: middle
   :height: 48px
   :width: 48px

.. |add| image:: ../_app_icons/add.png
   :align: middle
   :height: 24px
   :width: 24px

.. |affective| image:: ../_app_icons/affective.png
   :align: middle
   :height: 48px
   :width: 48px

.. |alltasks_big| image:: ../_app_icons/alltasks.png
   :align: middle
   :height: 48px
   :width: 48px

.. |alltasks_small| image:: ../_app_icons/alltasks.png
   :align: middle
   :height: 24px
   :width: 24px

.. |anonymous| image:: ../_app_icons/anonymous.png
   :align: middle
   :height: 48px
   :width: 48px

.. |back| image:: ../_app_icons/back.png
   :align: middle
   :height: 24px
   :width: 24px

.. |camcops| image:: ../_app_icons/camcops.png
   :align: middle
   :height: 24px
   :width: 24px

.. |camera| image:: ../_app_icons/camera.png
   :align: middle
   :height: 24px
   :width: 24px

.. |cancel| image:: ../_app_icons/cancel.png
   :align: middle
   :height: 24px
   :width: 24px

.. |catatonia| image:: ../_app_icons/catatonia.png
   :align: middle
   :height: 48px
   :width: 48px

.. |chain| image:: ../_app_icons/chain.png
   :align: middle
   :height: 24px
   :width: 24px

.. |check_disabled| image:: ../_app_icons/check_disabled.png
   :align: middle
   :height: 24px
   :width: 24px

.. |check_false_black| image:: ../_app_icons/check_false_black.png
   :align: middle
   :height: 24px
   :width: 24px

.. |check_false_red| image:: ../_app_icons/check_false_red.png
   :align: middle
   :height: 24px
   :width: 24px

.. |check_true_black| image:: ../_app_icons/check_true_black.png
   :align: middle
   :height: 24px
   :width: 24px

.. |check_true_red| image:: ../_app_icons/check_true_red.png
   :align: middle
   :height: 24px
   :width: 24px

.. |check_unselected| image:: ../_app_icons/check_unselected.png
   :align: middle
   :height: 24px
   :width: 24px

.. |check_unselected_required| image:: ../_app_icons/check_unselected_required.png
   :align: middle
   :height: 24px
   :width: 24px

.. |choose_page| image:: ../_app_icons/choose_page.png
   :align: middle
   :height: 24px
   :width: 24px

.. |choose_patient| image:: ../_app_icons/choose_patient.png
   :align: middle
   :height: 24px
   :width: 24px

.. |clinical| image:: ../_app_icons/clinical.png
   :align: middle
   :height: 48px
   :width: 48px

.. |cognitive| image:: ../_app_icons/cognitive.png
   :align: middle
   :height: 48px
   :width: 48px

.. |delete| image:: ../_app_icons/delete.png
   :align: middle
   :height: 24px
   :width: 24px

.. |dolphin| image:: ../_app_icons/dolphin.png
   :align: middle
   :height: 48px
   :width: 48px

.. |edit| image:: ../_app_icons/edit.png
   :align: middle
   :height: 24px
   :width: 24px

.. |executive| image:: ../_app_icons/executive.png
   :align: middle
   :height: 48px
   :width: 48px

.. |fast_forward| image:: ../_app_icons/fast_forward.png
   :align: middle
   :height: 24px
   :width: 24px

.. |field_incomplete_mandatory| image:: ../_app_icons/field_incomplete_mandatory.png
   :align: middle
   :height: 24px
   :width: 24px

.. |field_incomplete_optional| image:: ../_app_icons/field_incomplete_optional.png
   :align: middle
   :height: 24px
   :width: 24px

.. |field_problem| image:: ../_app_icons/field_problem.png
   :align: middle
   :height: 24px
   :width: 24px

.. |finishflag| image:: ../_app_icons/finishflag.png
   :align: middle
   :height: 24px
   :width: 24px

.. |finish| image:: ../_app_icons/finish.png
   :align: middle
   :height: 24px
   :width: 24px

.. |global| image:: ../_app_icons/global.png
   :align: middle
   :height: 48px
   :width: 48px

.. |hasChild| image:: ../_app_icons/hasChild.png
   :align: middle
   :height: 24px
   :width: 24px

.. |hasParent| image:: ../_app_icons/hasParent.png
   :align: middle
   :height: 24px
   :width: 24px

.. |info_big| image:: ../_app_icons/info.png
   :align: middle
   :height: 48px
   :width: 48px

.. |info_small| image:: ../_app_icons/info.png
   :align: middle
   :height: 24px
   :width: 24px

.. |language| image:: ../_app_icons/language.png
   :align: middle
   :height: 24px
   :width: 24px

.. |locked| image:: ../_app_icons/locked.png
   :align: middle
   :height: 24px
   :width: 24px

.. |magnify| image:: ../_app_icons/magnify.png
   :align: middle
   :height: 24px
   :width: 24px

.. |neurodiversity| image:: ../_app_icons/neurodiversity.png
   :align: middle
   :height: 24px
   :width: 24px

.. |next| image:: ../_app_icons/next.png
   :align: middle
   :height: 24px
   :width: 24px

.. |ok| image:: ../_app_icons/ok.png
   :align: middle
   :height: 24px
   :width: 24px

.. |patient_summary| image:: ../_app_icons/patient_summary.png
   :align: middle
   :height: 24px
   :width: 24px

.. |personality| image:: ../_app_icons/personality.png
   :align: middle
   :height: 48px
   :width: 48px

.. |physical| image:: ../_app_icons/physical.png
   :align: middle
   :height: 48px
   :width: 48px

.. |privileged| image:: ../_app_icons/privileged.png
   :align: middle
   :height: 24px
   :width: 24px

.. |psychosis| image:: ../_app_icons/psychosis.png
   :align: middle
   :height: 48px
   :width: 48px

.. |radio_disabled| image:: ../_app_icons/radio_disabled.png
   :align: middle
   :height: 24px
   :width: 24px

.. |radio_selected| image:: ../_app_icons/radio_selected.png
   :align: middle
   :height: 24px
   :width: 24px

.. |radio_unselected| image:: ../_app_icons/radio_unselected.png
   :align: middle
   :height: 24px
   :width: 24px

.. |radio_unselected_required| image:: ../_app_icons/radio_unselected_required.png
   :align: middle
   :height: 24px
   :width: 24px

.. |read_only| image:: ../_app_icons/read_only.png
   :align: middle
   :height: 24px
   :width: 24px

.. |reload| image:: ../_app_icons/reload.png
   :align: middle
   :height: 24px
   :width: 24px

.. |research| image:: ../_app_icons/research.png
   :align: middle
   :height: 48px
   :width: 48px

.. |rotate_anticlockwise| image:: ../_app_icons/rotate_anticlockwise.png
   :align: middle
   :height: 24px
   :width: 24px

.. |rotate_clockwise| image:: ../_app_icons/rotate_clockwise.png
   :align: middle
   :height: 24px
   :width: 24px

.. |service_evaluation| image:: ../_app_icons/service_evaluation.png
   :align: middle
   :height: 48px
   :width: 48px

.. |sets_clinical| image:: ../_app_icons/sets_clinical.png
   :align: middle
   :height: 48px
   :width: 48px

.. |sets_research| image:: ../_app_icons/sets_research.png
   :align: middle
   :height: 48px
   :width: 48px

.. |settings| image:: ../_app_icons/settings.png
   :align: middle
   :height: 24px
   :width: 24px

.. |spanner| image:: ../_app_icons/spanner.png
   :align: middle
   :height: 24px
   :width: 24px

.. |speaker_playing| image:: ../_app_icons/speaker_playing.png
   :align: middle
   :height: 24px
   :width: 24px

.. |speaker| image:: ../_app_icons/speaker.png
   :align: middle
   :height: 24px
   :width: 24px

.. |stop_big| image:: ../_app_icons/stop.png
   :align: middle
   :height: 48px
   :width: 48px

.. |stop_small| image:: ../_app_icons/stop.png
   :align: middle
   :height: 24px
   :width: 24px

.. |time_now| image:: ../_app_icons/time_now.png
   :align: middle
   :height: 24px
   :width: 24px

.. |treeview| image:: ../_app_icons/treeview.png
   :align: middle
   :height: 24px
   :width: 24px

.. |unlocked| image:: ../_app_icons/unlocked.png
   :align: middle
   :height: 24px
   :width: 24px

.. |upload| image:: ../_app_icons/upload.png
   :align: middle
   :height: 24px
   :width: 24px

.. |warning| image:: ../_app_icons/warning.png
   :align: middle
   :height: 24px
   :width: 24px

.. |whisker| image:: ../_app_icons/whisker.png
   :align: middle
   :height: 24px
   :width: 24px

.. |zoom| image:: ../_app_icons/zoom.png
   :align: middle
   :height: 24px
   :width: 24px
