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

#include "textconst.h"
#include <QObject>

// using tr = QObject::tr;  // nope, duff syntax
#define TR(stringname, text) const QString stringname(QObject::tr(text))

namespace textconst {


// ============================================================================
// Common text
// ============================================================================

TR(ABNORMAL, "Abnormal");
TR(ABORT, "Abort");
TR(ADD, "Add");
TR(AND, "and");

TR(BACK, "Back");

TR(CANCEL, "Cancel");
TR(CATEGORY, "Category");
TR(CLINICIAN, "Clinician");
TR(CLINICIAN_AND_RESPONDENT_DETAILS, "Clinician’s and respondent’s details");
TR(CLINICIAN_COMMENTS, "Clinician’s comments");
TR(CLINICIAN_CONTACT_DETAILS, "Clinician’s contact details");
TR(CLINICIAN_DETAILS, "Clinician’s details");
TR(CLINICIAN_NAME, "Clinician’s name");
TR(CLINICIAN_POST, "Clinician’s post");
TR(CLINICIAN_PROFESSIONAL_REGISTRATION, "Clinician’s professional registration");
TR(CLINICIAN_SERVICE, "Clinician’s service");
TR(CLINICIAN_SPECIALTY, "Clinician’s specialty");
TR(CLINICIANS_COMMENTS, "Clinician’s comments");
TR(COMMENT, "Comment");
TR(COMMENTS, "Comments");
TR(CORRECT, "Correct");

TR(DATA_COLLECTION_ONLY,
   "Reproduction of this task/scale is not permitted. This is a data "
   "collection tool only; use it only in conjunction with a licensed copy of "
   "the original task.");
TR(DELETE, "Delete");
TR(DESCRIPTION, "Description");
TR(DIAGNOSIS, "Diagnosis");

TR(ENTER_THE_ANSWERS, "Enter the answers:");
TR(EXAMINER_COMMENTS, "Examiner’s comments");
TR(EXAMINER_COMMENTS_PROMPT, "Optional — Examiner’s comments (e.g. "
                             "difficulties the subject had with the task):");

TR(FALSE, "False");
TR(FINISHED, "Finished");

TR(ICD10, "World Health Organization International Classification of "
          "Diseases, 10th edition");
TR(IN_ADDITION, "In addition");
TR(INCORRECT, "Incorrect");

TR(LOCATION, "Location");

TR(MEETS_CRITERIA, "Meets criteria");
TR(MILD, "Mild");
TR(MILD_TO_MODERATE, "Mild to moderate");
TR(MODERATELY_SEVERE, "Moderately severe");
TR(MODERATE_TO_SEVERE, "Moderate to severe");
TR(MODERATE, "Moderate");
TR(MOVE_DOWN, "Move down");
TR(MOVE_UP, "Move up");

TR(NA, "N/A");
TR(NONE, "None");
TR(NO, "No");
TR(NO_DETAIL_SEE_FACSIMILE, "No detail available; see the facsimile instead");
TR(NO_SUMMARY_SEE_FACSIMILE, "No summary available; see the facsimile instead");
TR(NORMAL, "Normal");
TR(NOT_APPLICABLE, "Not applicable");
TR(NOT_RECALLED, "Not recalled");
TR(NOT_SPECIFIED, "<not specified>");
TR(NOTE, "Note");

TR(OF, "of");
TR(OFF, "Off");
TR(ON, "On");

TR(PAGE, "page");
TR(PART, "Part");
TR(PATIENT, "Patient");
TR(PHOTO, "Photo");
TR(PHOTOS, "Photos");
TR(PHOTO_TITLE, "Clinical photograph");
TR(PHOTO_Q,
   "1. Ensure consent is documented, if applicable.\n"
   "2. Take a photograph.\n"
   "3. Enter a description.");
TR(PHOTOSEQUENCE_ADD, "Add new photo");
TR(PHOTOSEQUENCE_DELETE, "Delete this photo");
TR(PHOTOSEQUENCE_PHOTO_DESCRIPTION, "Photo description");
TR(PHOTOSEQUENCE_SEQUENCE_DESCRIPTION, "Sequence description");
TR(PHOTOSEQUENCE_MOVE_BACK, "Move this photo backwards");
TR(PHOTOSEQUENCE_MOVE_FORWARDS, "Move this photo forwards");
TR(PLEASE_WAIT, "Please wait...");
TR(PRESS_NEXT_TO_CONTINUE,
   "Press the NEXT button (the green right-facing arrow at the TOP RIGHT of "
   "the screen) to continue.");

TR(QUESTION, "Question");

TR(RATING, "Rating");
TR(REALLY_ABORT, "Really abort?");
TR(RECALLED, "Recalled");
TR(RESPONDENT_DETAILS, "Respondent’s details");
TR(RESPONDENT_NAME_2P, "Your name");
TR(RESPONDENT_NAME_3P, "Respondent’s name");
TR(RESPONDENT_RELATIONSHIP_2P, "Your relationship to the patient");
TR(RESPONDENT_RELATIONSHIP_3P, "Respondent’s relationship to patient");

TR(SAVING, "Saving, please wait...");
TR(SCORE, "Score");
TR(SEE_FACSIMILE, "See facsimile.");
TR(SEE_FACSIMILE_FOR_MORE_DETAIL, "See facsimile for more detail.");
TR(SERVICE, "Service");
TR(SEVERE, "Severe");
TR(SEX, "Sex");
TR(SOUND_TEST_FOR, "Sound test for");

TR(THANK_YOU, "Thank you!");
TR(THANK_YOU_TOUCH_TO_EXIT, "Thank you! Please touch here to exit.");
TR(TOTAL_SCORE, "Total score");
TR(TOUCH_TO_START, "When you’re ready, touch here to start.");
TR(TRUE, "True");

TR(UNKNOWN, "Unknown");

TR(VERY_SEVERE, "Very severe");

TR(WRONG, "Wrong");

TR(YES, "Yes");


// ============================================================================
// Terms and conditions
// ============================================================================

const QString TERMS_CONDITIONS(
    "1. By using the Cambridge Cognitive and Psychiatric Assessment Kit "
    "application or web interface (“CamCOPS”), you are agreeing in full "
    "to these Terms and Conditions of Use. If you do not agree to these "
    "terms, do not use the software.\n\n"

    "2. Content that is original to CamCOPS is licensed as follows.\n\n"

    "CamCOPS is free software: you can redistribute it and/or modify "
    "it under the terms of the GNU General Public License as published by "
    "the Free Software Foundation, either version 3 of the License, or "
    "(at your option) any later version.\n\n"

    "CamCOPS is distributed in the hope that it will be useful, "
    "but WITHOUT ANY WARRANTY; without even the implied warranty of "
    "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the "
    "GNU General Public License for more details\n\n"

    "You should have received a copy of the GNU General Public License "
    "along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.\n\n"

    "3. Content created by others and distributed with CamCOPS may be in "
    "the public domain, or distributed under other licenses or "
    "permissions. THERE MAY BE CRITERIA THAT APPLY TO YOU THAT MEAN YOU "
    "ARE NOT PERMITTED TO USE SPECIFIC TASKS. IT IS YOUR RESPONSIBILITY "
    "TO CHECK THAT YOU ARE LEGALLY ENTITLED TO USE EACH TASK. You agree "
    "that the authors of CamCOPS are not responsible for any consequences "
    "that arise from your use of an unauthorized task.\n\n"

    "4. While efforts have been made to ensure that CamCOPS is reliable "
    "and accurate, you agree that the authors and distributors of CamCOPS "
    "are not responsible for errors, omissions, or defects in the "
    "content, nor liable for any direct, indirect, incidental, special "
    "and/or consequential damages, in whole or in part, resulting from "
    "your use or any user’s use of or reliance upon its content.\n\n"

    "5. Content contained in or accessed through CamCOPS should not be "
    "relied upon for medical purposes in any way. This software is not "
    "designed for use by the general public. If medical advice is "
    "required you should seek expert medical assistance. You agree that "
    "you will not rely on this software for any medical purpose.\n\n"

    "6. Regarding the European Union Council Directive 93/42/EEC of 14 "
    "June 1993 concerning medical devices (amended by further directives "
    "up to and including Directive 2007/47/EC of 5 September 2007) "
    "(“Medical Devices Directive”): CamCOPS is not intended for "
    "the diagnosis and/or monitoring of human disease. If it is used for "
    "such purposes, it must be used EXCLUSIVELY FOR CLINICAL "
    "INVESTIGATIONS in an appropriate setting by persons professionally "
    "qualified to do so. It has NOT undergone a conformity assessment "
    "under the Medical Devices Directive, and thus cannot be marketed or "
    "put into service as a medical device. You agree that you will not "
    "use it as a medical device.\n\n"

    "7. THIS SOFTWARE IS DESIGNED FOR USE BY QUALIFIED CLINICIANS ONLY. "
    "BY CONTINUING TO USE THIS SOFTWARE YOU ARE CONFIRMING THAT YOU ARE "
    "A QUALIFIED CLINICIAN, AND THAT YOU RETAIN RESPONSIBILITY FOR "
    "DIAGNOSIS AND MANAGEMENT.\n\n"

    "These terms and conditions were last revised on 2017-01-23."
);

// ============================================================================
// Test text
// ============================================================================

const QString LOREM_IPSUM_1(  // http://www.lipsum.com/
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent "
    "sed cursus mauris. Ut vulputate felis quis dolor molestie convallis. "
    "Donec lectus diam, accumsan quis tortor at, congue laoreet augue. Ut "
    "mollis consectetur elit sit amet tincidunt. Vivamus facilisis, mi et "
    "eleifend ullamcorper, lorem metus faucibus ante, ut commodo urna "
    "neque bibendum magna. Lorem ipsum dolor sit amet, consectetur "
    "adipiscing elit. Praesent nec nisi ante. Sed vitae sem et eros "
    "elementum condimentum. Proin porttitor purus justo, sit amet "
    "vulputate velit imperdiet nec. Nam posuere ipsum id nunc accumsan "
    "tristique. Etiam pellentesque ornare tortor, a scelerisque dui "
    "accumsan ac. Ut tincidunt dolor ultrices, placerat urna nec, "
    "scelerisque mi."
);
const QString LOREM_IPSUM_2(
    "Nunc vitae neque eu odio feugiat consequat ac id neque. "
    "Suspendisse id libero massa."
);
const QString LOREM_IPSUM_3(
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent "
    "sed cursus mauris. Ut vulputate felis quis dolor molestie convallis. "
    "Donec lectus diam, accumsan quis tortor at, congue laoreet augue. Ut "
    "mollis consectetur elit sit amet tincidunt."
);


}  // namespace textconst
