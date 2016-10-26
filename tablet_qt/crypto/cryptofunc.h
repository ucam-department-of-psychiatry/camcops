#pragma once
// #include <openssl/crypto.h>  // for OpenSSL_cleanse
#include <QString>
#include "secureqbytearray.h"
#include "secureqstring.h"


namespace CryptoFunc
{
    // ========================================================================
    // Simple calculations
    // ========================================================================
    int base64Length(int nbytes);

    // ========================================================================
    // Low-level calls
    // ========================================================================
    void aesEncrypt(const QByteArray& key_bytes, const QByteArray& iv_bytes,
                    const QByteArray& plaintext_bytes,
                    QByteArray& ciphertext_bytes);
    void aesDecrypt(const QByteArray& key_bytes, const QByteArray& iv_bytes,
                    const QByteArray& ciphertext_bytes,
                    QByteArray& recoveredtext_bytes);
    SecureQByteArray makeAesIV();
    bool isValidAesKey(const QByteArray& key_bytes);
    bool isValidAesKey(const QString& key_b64);
    bool isValidAesIV(const QByteArray& iv_bytes);
    bool isValidAesIV(const QString& iv_b64);
    SecureQByteArray hashBytes(const QByteArray& plaintext_bytes);
    QString hash(const QString& plaintext, const QString& salt);
    QString makeSalt();

    // ========================================================================
    // Front end
    // ========================================================================
    SecureQByteArray randomBytes(int n);
    SecureQString generateObscuringKeyBase64();
    QString generateIVBase64();
    QString encryptToBase64(const QString& plaintext,
                            const QString& key_b64,
                            const QString& iv_b64);
    SecureQString decryptFromBase64(const QString& ciphertext_b64,
                                    const QString& key_b64,
                                    const QString& iv_b64);
    QString hash(const QString& plaintext);
    bool matchesHash(const QString& plaintext, const QString& hashed);
}
