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
#include <QString>


namespace textconst
{

// ============================================================================
// PRINCIPLES:
// ============================================================================
//
// - If a string is used only once, it can live in the source code (*).
//
// - If a string is re-used on the tablet, it should live here (*).
//
// - If a string is shared between the tablet and server (but in a way that
//   is not task-specific), it should live in the "camcops" namespace of the
//   downloaded strings, unless it is "mission-critical" for the tablet.
//   Things that live in the "camcops" XML namespace should be referenced in
//   the "appstrings" namespace, in common/appstrings.h
//
// - If a string is task-specific, it should live in the task's namespace of
//   the downloaded strings. (It can be referenced by a free-floating name
//   string, or if used more than once, by a local variable.)
//
// (*) Strings that live in the source code, and involve some language, should
// use the Qt tr() mechanism to support internationalization. (The downloaded
// string system already supports this, as users can swap in a different string
// file.)


// ============================================================================
// Common text
// ============================================================================

extern const QString ABNORMAL;
extern const QString ABORT;
extern const QString ADD;
extern const QString AND;

extern const QString BACK;

extern const QString CANCEL;
extern const QString CATEGORY;
extern const QString CLINICIAN;
extern const QString CLINICIAN_AND_RESPONDENT_DETAILS;
extern const QString CLINICIAN_COMMENTS;
extern const QString CLINICIAN_CONTACT_DETAILS;
extern const QString CLINICIAN_DETAILS;
extern const QString CLINICIAN_NAME;
extern const QString CLINICIAN_POST;
extern const QString CLINICIAN_PROFESSIONAL_REGISTRATION;
extern const QString CLINICIAN_SERVICE;
extern const QString CLINICIAN_SPECIALTY;
extern const QString CLINICIANS_COMMENTS;
extern const QString COMMENT;
extern const QString COMMENTS;
extern const QString CORRECT;

extern const QString DATA_COLLECTION_ONLY;
extern const QString DELETE;
extern const QString DESCRIPTION;
extern const QString DIAGNOSIS;

extern const QString FALSE;
extern const QString FINISHED;

extern const QString ENTER_THE_ANSWERS;
extern const QString EXAMINER_COMMENTS;
extern const QString EXAMINER_COMMENTS_PROMPT;

extern const QString ICD10;
extern const QString IN_ADDITION;
extern const QString INCORRECT;

extern const QString LOCATION;

extern const QString MEETS_CRITERIA;
extern const QString MILD;
extern const QString MILD_TO_MODERATE;
extern const QString MODERATE;
extern const QString MODERATE_TO_SEVERE;
extern const QString MODERATELY_SEVERE;
extern const QString MOVE_DOWN;
extern const QString MOVE_UP;

extern const QString NA;
extern const QString NO;
extern const QString NONE;
extern const QString NO_DETAIL_SEE_FACSIMILE;
extern const QString NO_SUMMARY_SEE_FACSIMILE;
extern const QString NORMAL;
extern const QString NOT_APPLICABLE;
extern const QString NOT_RECALLED;
extern const QString NOT_SPECIFIED;
extern const QString NOTE;
// Don't use NULL; it's a keyword

extern const QString OF;
extern const QString OFF;
extern const QString ON;

extern const QString PAGE;
extern const QString PART;
extern const QString PATIENT;
extern const QString PHOTO;
extern const QString PHOTOS;
extern const QString PHOTO_TITLE;
extern const QString PHOTO_Q;
extern const QString PHOTOSEQUENCE_ADD;
extern const QString PHOTOSEQUENCE_DELETE;
extern const QString PHOTOSEQUENCE_PHOTO_DESCRIPTION;
extern const QString PHOTOSEQUENCE_SEQUENCE_DESCRIPTION;
extern const QString PHOTOSEQUENCE_MOVE_BACK;
extern const QString PHOTOSEQUENCE_MOVE_FORWARDS;
extern const QString PLEASE_WAIT;
extern const QString PRESS_NEXT_TO_CONTINUE;

extern const QString QUESTION;

extern const QString RATING;
extern const QString REALLY_ABORT;
extern const QString RECALLED;
extern const QString RESPONDENT_DETAILS;
extern const QString RESPONDENT_NAME_2P;
extern const QString RESPONDENT_NAME_3P;
extern const QString RESPONDENT_RELATIONSHIP_2P;
extern const QString RESPONDENT_RELATIONSHIP_3P;

extern const QString SAVING;
extern const QString SCORE;
extern const QString SEE_FACSIMILE;
extern const QString SEE_FACSIMILE_FOR_MORE_DETAIL;
extern const QString SERVICE;
extern const QString SEVERE;
extern const QString SEX;
extern const QString SOUND_TEST_FOR;

extern const QString THANK_YOU;
extern const QString THANK_YOU_TOUCH_TO_EXIT;
extern const QString TOTAL_SCORE;
extern const QString TOUCH_TO_START;
extern const QString TRUE;

extern const QString UNKNOWN;

extern const QString VERY_SEVERE;

extern const QString WRONG;

extern const QString YES;

// ============================================================================
// Terms and conditions
// ============================================================================

extern const QString TERMS_CONDITIONS;

// ============================================================================
// Test text
// ============================================================================

extern const QString LOREM_IPSUM_1;
extern const QString LOREM_IPSUM_2;
extern const QString LOREM_IPSUM_3;

}  // namespace textconst
