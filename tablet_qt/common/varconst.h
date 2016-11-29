#pragma once
#include <QString>

namespace VarConst
{
    // Version storage
    extern const QString CAMCOPS_VERSION_AS_STRING;

    // Questionnaire
    extern const QString QUESTIONNAIRE_SIZE_PERCENT;

    // Server
    extern const QString SERVER_ADDRESS;
    extern const QString SERVER_PORT;
    extern const QString SERVER_PATH;
    extern const QString SERVER_TIMEOUT_MS;
    extern const QString VALIDATE_SSL_CERTIFICATES;
    extern const QString STORE_SERVER_PASSWORD;
    extern const QString SEND_ANALYTICS;

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
}
