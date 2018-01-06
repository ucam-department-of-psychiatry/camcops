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
#include "common/design_defines.h"

namespace varconst {

// Version storage
extern const QString CAMCOPS_TABLET_VERSION_AS_STRING;

// Questionnaire
extern const QString QUESTIONNAIRE_SIZE_PERCENT;

// Server
extern const QString SERVER_ADDRESS;
extern const QString SERVER_PORT;
extern const QString SERVER_PATH;
extern const QString SERVER_TIMEOUT_MS;
extern const QString VALIDATE_SSL_CERTIFICATES;
extern const QString SSL_PROTOCOL;
extern const QString DEBUG_USE_HTTPS_TO_SERVER;
extern const QString STORE_SERVER_PASSWORD;
#ifdef ALLOW_SEND_ANALYTICS
extern const QString SEND_ANALYTICS;
#endif

// Uploading flag
extern const QString NEEDS_UPLOAD;

// Whisker
extern const QString WHISKER_HOST;
extern const QString WHISKER_PORT;
extern const QString WHISKER_TIMEOUT_MS;

// Terms and conditions
extern const QString AGREED_TERMS_AT;

// Intellectual property
extern const QString IP_USE_CLINICAL;
extern const QString IP_USE_COMMERCIAL;
extern const QString IP_USE_EDUCATIONAL;
extern const QString IP_USE_RESEARCH;

// Patients and policies
extern const QString ID_POLICY_UPLOAD;
extern const QString ID_POLICY_FINALIZE;

// Note that ID descriptions/short descriptions have multiple server
// variables as set by
//      DbConst::IDDESC_FIELD_FORMAT
//      DbConst::IDSHORTDESC_FIELD_FORMAT

// Other information from server
extern const QString SERVER_DATABASE_TITLE;
extern const QString SERVER_CAMCOPS_VERSION;
extern const QString LAST_SERVER_REGISTRATION;
extern const QString LAST_SUCCESSFUL_UPLOAD;

// User
// ... server interaction
extern const QString DEVICE_FRIENDLY_NAME;
extern const QString SERVER_USERNAME;
extern const QString SERVER_USERPASSWORD_OBSCURED;
extern const QString OFFER_UPLOAD_AFTER_EDIT;
// ... default clinician details
extern const QString DEFAULT_CLINICIAN_SPECIALTY;
extern const QString DEFAULT_CLINICIAN_NAME;
extern const QString DEFAULT_CLINICIAN_PROFESSIONAL_REGISTRATION;
extern const QString DEFAULT_CLINICIAN_POST;
extern const QString DEFAULT_CLINICIAN_SERVICE;
extern const QString DEFAULT_CLINICIAN_CONTACT_DETAILS;

// Cryptography
extern const QString OBSCURING_KEY;  // for server p/w, which we must retrieve
extern const QString OBSCURING_IV;
extern const QString USER_PASSWORD_HASH;
extern const QString PRIV_PASSWORD_HASH;

// Device ID
extern const QString DEVICE_ID;

}  // namespace varconst
