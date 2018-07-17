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

// #define OPENSSL_VIA_QLIBRARY

// #include <openssl/crypto.h>  // for OpenSSL_cleanse
#include <QString>
#include "secureqbytearray.h"
#include "secureqstring.h"


namespace cryptofunc {

// ============================================================================
// DLL helpers
// ============================================================================

#ifdef OPENSSL_VIA_QLIBRARY
void ensureAllCryptoFunctionsLoaded();
#endif

// ============================================================================
// Simple calculations
// ============================================================================
int base64Length(int nbytes);

// ============================================================================
// Low-level calls
// ============================================================================
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

// ============================================================================
// Front end
// ============================================================================
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

}  // namespace cryptofunc
