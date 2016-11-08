#include "varconst.h"

namespace VarConst
{
    // Version storage
    const QString CAMCOPS_VERSION_AS_STRING("camcopsVersion");

    // Questionnaire
    const QString QUESTIONNAIRE_SIZE_PERCENT("questionnaireTextSizePercent");

    // Server
    const QString SERVER_ADDRESS("serverAddress");
    const QString SERVER_PORT("serverPort");
    const QString SERVER_PATH("serverPath");
    const QString SERVER_TIMEOUT_MS("serverTimeoutMs");
    const QString VALIDATE_SSL_CERTIFICATES("validateSSLCertificates");
    const QString STORE_SERVER_PASSWORD("storeServerPassword");
    const QString SEND_ANALYTICS("sendAnalytics");

    // Uploading flag
    const QString NEEDS_UPLOAD("needsUpload");

    // Whisker
    const QString WHISKER_HOST("whiskerHost");
    const QString WHISKER_PORT("whiskerPort");
    const QString WHISKER_TIMEOUT_MS("whiskerTimeoutMs");

    // Intellectual property
    const QString IP_USE_CLINICAL("useClinical");
    const QString IP_USE_COMMERCIAL("useCommercial");
    const QString IP_USE_EDUCATIONAL("useEducational");
    const QString IP_USE_RESEARCH("useResearch");

    // Patients and policies
    const QString ID_POLICY_UPLOAD("idPolicyUpload");
    const QString ID_POLICY_FINALIZE("idPolicyFinalize");

    // User
    const QString DEVICE_FRIENDLY_NAME("deviceFriendlyName");
    const QString SERVER_USERNAME("serverUser");
    const QString SERVER_USERPASSWORD_OBSCURED("serverPasswordObscured");
    const QString DEFAULT_CLINICIAN_SPECIALTY("defaultClinicianSpecialty");
    const QString DEFAULT_CLINICIAN_NAME("defaultClinicianName");
    const QString DEFAULT_CLINICIAN_PROFESSIONAL_REGISTRATION("defaultClinicianProfessionalRegistration");
    const QString DEFAULT_CLINICIAN_POST("defaultClinicianPost");
    const QString DEFAULT_CLINICIAN_SERVICE("defaultClinicianService");
    const QString DEFAULT_CLINICIAN_CONTACT_DETAILS("defaultClinicianContactDetails");
    const QString OFFER_UPLOAD_AFTER_EDIT("offerUploadAfterEdit");

    // Cryptography
    const QString OBSCURING_KEY("obscuringKey");
    const QString OBSCURING_IV("obscuringIV");
    const QString USER_PASSWORD_HASH("userPassword");
    const QString PRIV_PASSWORD_HASH("privPassword");
}
