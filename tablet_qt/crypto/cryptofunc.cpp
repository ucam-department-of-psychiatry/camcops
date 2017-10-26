/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

// #define DANGER_DEBUG_CRYPTO  // never use this in a production environment

#include "cryptofunc.h"
#include <math.h>  // for ceil
#include <memory>  // for std::unique_ptr
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <QDebug>
#include <QByteArray>
#include "lib/convert.h"
#include "lib/uifunc.h"

// ============================================================================
// Notes
// ============================================================================
// RNG
// - OpenSSL will seed itself automatically.
//   https://wiki.openssl.org/index.php/Random_Numbers#Seeds
//
// Simple reversible encryption
// - Under Titanium, we used SJCL: http://bitwiseshiftleft.github.io/sjcl/
// - Here, we'll use OpenSSL.
//   - https://wiki.openssl.org/index.php/EVP_Symmetric_Encryption_and_Decryption
//
// You need to store the IV (initialization vector) for AES
// - http://crypto.stackexchange.com/questions/7935/does-the-iv-need-to-be-known-by-aes-cbc-mode
// - http://crypto.stackexchange.com/questions/3965/what-is-the-main-difference-between-a-key-an-iv-and-a-nonce
// - https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation#Initialization_vector_.28IV.29

// ============================================================================
// typedefs
// ============================================================================

using EVP_CIPHER_CTX_ptr = std::unique_ptr<EVP_CIPHER_CTX, decltype(&::EVP_CIPHER_CTX_free)>;
using EVP_MD_CTX_ptr = std::unique_ptr<EVP_MD_CTX, decltype(&::EVP_MD_CTX_destroy)>;

// ============================================================================
// Constants
// ============================================================================

const int BCRYPT_LOG_ROUNDS = 6;
// because tablets are pretty slow; see
// http://security.stackexchange.com/questions/3959/

const unsigned int AES_256BIT_KEY_SIZE = 256 / 8;
const unsigned int AES_BLOCK_SIZE_BYTES = 16;  // AES is 128 bits = 16 bytes
const unsigned int SALT_LENGTH_BYTES = 64;
// ... https://www.owasp.org/index.php/Password_Storage_Cheat_Sheet
const int SALT_LENGTH_TEXT = cryptofunc::base64Length(SALT_LENGTH_BYTES);


// ============================================================================
// Simple calculations
// ============================================================================

int cryptofunc::base64Length(const int nbytes)
{
    // http://stackoverflow.com/questions/13378815/base64-length-calculation
    double d = nbytes;
    int len = ceil(4 * (d / 3));
    // Round up to a multiple of 4:
    while (len % 4 != 0) {
        ++len;
    }
    return len;
}

// ============================================================================
// OpenSSL low-level calls
// ============================================================================

void cryptofunc::aesEncrypt(const QByteArray& key_bytes,
                            const QByteArray& iv_bytes,
                            const QByteArray& plaintext_bytes,
                            QByteArray& ciphertext_bytes)
{
#ifdef DANGER_DEBUG_CRYPTO
    qDebug() << Q_FUNC_INFO;
    qDebug() << "key_bytes" << key_bytes;
    qDebug() << "iv_bytes" << iv_bytes;
    qDebug() << "plaintext_bytes" << plaintext_bytes;
#endif
    auto keydata = reinterpret_cast<const unsigned char*>(key_bytes.constData());
    auto ivdata = reinterpret_cast<const unsigned char*>(iv_bytes.constData());
    auto ptextdata = reinterpret_cast<const unsigned char*>(plaintext_bytes.constData());

    EVP_CIPHER_CTX_ptr ctx(EVP_CIPHER_CTX_new(), ::EVP_CIPHER_CTX_free);
    int retcode = EVP_EncryptInit_ex(ctx.get(),  // EVP_CIPHER_CTX* ctx
                                     EVP_aes_256_cbc(), // const EVP_CIPHER* type
                                     NULL,  // ENGINE* impl: implementation
                                     keydata, // unsigned char* key
                                     ivdata);  // unsigned char* iv
    if (retcode != 1) {
        throw std::runtime_error("EVP_EncryptInit_ex failed");
    }

    // Recovered text expands up to BLOCK_SIZE
    ciphertext_bytes.resize(plaintext_bytes.size() + AES_BLOCK_SIZE_BYTES);
    // Set the pointer (ctextdata) AFTER the resize; it's likely that the
    // resize invalidates any previous pointers to the data.
    auto ctextdata = reinterpret_cast<unsigned char*>(ciphertext_bytes.data());
    int out_len1 = (int)ciphertext_bytes.size();

    retcode = EVP_EncryptUpdate(ctx.get(), ctextdata, &out_len1,
                                ptextdata, plaintext_bytes.size());
    if (retcode != 1) {
        throw std::runtime_error("EVP_EncryptUpdate failed");
    }

    int out_len2 = ciphertext_bytes.size() - out_len1;
    retcode = EVP_EncryptFinal_ex(ctx.get(), ctextdata + out_len1, &out_len2);
    if (retcode != 1) {
        throw std::runtime_error("EVP_EncryptFinal_ex failed");
    }

    // Set cipher text size now that we know it
    ciphertext_bytes.resize(out_len1 + out_len2);
#ifdef DANGER_DEBUG_CRYPTO
    qDebug() << "-> ciphertext_bytes" << ciphertext_bytes;
#endif
}


void cryptofunc::aesDecrypt(const QByteArray& key_bytes,
                            const QByteArray& iv_bytes,
                            const QByteArray& ciphertext_bytes,
                            QByteArray& recoveredtext_bytes)
{
#ifdef DANGER_DEBUG_CRYPTO
    qDebug() << Q_FUNC_INFO;
    qDebug() << "key_bytes" << key_bytes;
    qDebug() << "iv_bytes" << iv_bytes;
    qDebug() << "ciphertext_bytes" << ciphertext_bytes;
#endif
    const unsigned char* keydata = reinterpret_cast<const unsigned char*>(key_bytes.constData());
    const unsigned char* ivdata = reinterpret_cast<const unsigned char*>(iv_bytes.constData());
    const unsigned char* ctextdata = reinterpret_cast<const unsigned char*>(ciphertext_bytes.constData());

    EVP_CIPHER_CTX_ptr ctx(EVP_CIPHER_CTX_new(), ::EVP_CIPHER_CTX_free);
    int retcode = EVP_DecryptInit_ex(ctx.get(), EVP_aes_256_cbc(), NULL,
                                     keydata, ivdata);
    if (retcode != 1) {
        throw std::runtime_error("EVP_DecryptInit_ex failed");
    }

    // Recovered text contracts up to AES_BLOCK_SIZE_BYTES
    recoveredtext_bytes.resize(ciphertext_bytes.size());
    // Set the pointer (ptextdata) AFTER the resize; it's likely that the
    // resize invalidates any previous pointers to the data.
    auto ptextdata = reinterpret_cast<unsigned char*>(recoveredtext_bytes.data());
    int out_len1 = (int)recoveredtext_bytes.size();

    retcode = EVP_DecryptUpdate(ctx.get(), ptextdata, &out_len1,
                                ctextdata, ciphertext_bytes.size());
    if (retcode != 1) {
        // throw std::runtime_error("EVP_DecryptUpdate failed");
        qWarning() << "DECRYPTION FAILED (EVP_DecryptUpdate failed)";
        recoveredtext_bytes = QByteArray();
        return;
    }

    int out_len2 = (int)recoveredtext_bytes.size() - out_len1;
    retcode = EVP_DecryptFinal_ex(ctx.get(), ptextdata + out_len1, &out_len2);
    if (retcode != 1) {
        // throw std::runtime_error("EVP_DecryptFinal_ex failed");
        qWarning() << "DECRYPTION FAILED (EVP_DecryptFinal_ex failed)";
        recoveredtext_bytes = QByteArray();
        return;
    }

    // Set recovered text size now that we know it
    recoveredtext_bytes.resize(out_len1 + out_len2);
#ifdef DANGER_DEBUG_CRYPTO
    qDebug() << "-> recoveredtext_bytes" << recoveredtext_bytes;
#endif
}


SecureQByteArray cryptofunc::hashBytes(const QByteArray& plaintext_bytes)
{
    EVP_MD_CTX_ptr context(EVP_MD_CTX_create(), ::EVP_MD_CTX_destroy);
    // This is for OpenSSL 1.0.2h. In OpenSSL 1.1,
    // - EVP_MD_CTX_create is renamed EVP_MD_CTX_new
    // - EVP_MD_CTX_destroy is renamed EVP_MD_CTX_free
    int retcode = EVP_DigestInit_ex(context.get(), EVP_sha512(), NULL);
    if (retcode != 1) {
        throw std::runtime_error("EVP_DigestInit_ex failed");
    }
    auto msgdata = reinterpret_cast<const unsigned char*>(plaintext_bytes.constData());
    int msglen = plaintext_bytes.size();
    retcode = EVP_DigestUpdate(context.get(), msgdata, msglen);
    if (retcode != 1) {
        qWarning() << "HASHING FAILED (EVP_DigestUpdate failed)";
        return QByteArray();
    }
    QByteArray result(EVP_MAX_MD_SIZE, 0);
    auto resultdata = reinterpret_cast<unsigned char*>(result.data());
    unsigned int digestlen;
    retcode = EVP_DigestFinal_ex(context.get(), resultdata, &digestlen);
    if (retcode != 1) {
        qWarning() << "HASHING FAILED (EVP_DigestUpdate failed)";
        return QByteArray();
    }
    result.resize(digestlen);
    return result;
}


SecureQByteArray cryptofunc::makeAesIV()
{
    SecureQByteArray iv(AES_BLOCK_SIZE_BYTES, 0);
    auto ivdata = reinterpret_cast<unsigned char*>(iv.data());
    RAND_bytes(ivdata, AES_BLOCK_SIZE_BYTES);
    return iv;
}


QString cryptofunc::generateIVBase64()
{
    SecureQByteArray iv = makeAesIV();
    return QString(iv.toBase64());
}


bool cryptofunc::isValidAesKey(const QByteArray& key_bytes)
{
    // https://en.wikipedia.org/wiki/Advanced_Encryption_Standard
    int n_bytes = key_bytes.size();
    int n_bits = n_bytes * 8;
#ifdef DANGER_DEBUG_CRYPTO
    qDebug() << Q_FUNC_INFO << "key_bytes" << key_bytes
             << "n_bytes" << n_bytes << "n_bits" << n_bits;
#endif
    if (n_bits == 128 || n_bits == 192 || n_bits == 256) {
        return true;
    }
    qWarning() << "... Invalid AES key size (must be 128, 192, or 256 bits); "
                  "was" << n_bytes << "bytes =" << n_bits << "bits";
    return false;
}


bool cryptofunc::isValidAesKey(const QString& key_b64)
{
    SecureQByteArray key_bytes = convert::base64ToSecureBytes(key_b64);
#ifdef DANGER_DEBUG_CRYPTO
    qDebug() << Q_FUNC_INFO
             << "key_b64" << key_b64
             << "key_bytes" << key_bytes;
#endif
    return isValidAesKey(key_bytes);
}


bool cryptofunc::isValidAesIV(const QByteArray& iv_bytes)
{
    int n_bytes = iv_bytes.size();
    int n_bits = n_bytes * 8;
#ifdef DANGER_DEBUG_CRYPTO
    qDebug() << Q_FUNC_INFO << "iv_bytes" << iv_bytes
             << "n_bytes" << n_bytes << "n_bits" << n_bits;
#endif
    if (n_bits == 128) {
        return true;
    }
    qWarning() << "... Invalid AES IV size (must be 128 bits); "
                  "was" << n_bytes << "bytes =" << n_bits << "bits";
    return false;
}


bool cryptofunc::isValidAesIV(const QString& iv_b64)
{
    QByteArray iv_bytes = convert::base64ToBytes(iv_b64);
#ifdef DANGER_DEBUG_CRYPTO
    qDebug() << Q_FUNC_INFO
             << "iv_b64" << iv_b64
             << "iv_bytes" << iv_bytes;
#endif
    return isValidAesIV(iv_bytes);
}


// ============================================================================
// Front end
// ============================================================================

SecureQByteArray cryptofunc::randomBytes(const int n)
{
    SecureQByteArray array(n, 0);
    auto ptr = reinterpret_cast<unsigned char*>(array.data());
    int retcode = RAND_bytes(ptr, n);
    if (retcode == -1) {  // failure; see rand_lib.c
        uifunc::stopApp("Call to OpenSSL RAND_bytes failed");
    }
    return array;
}


SecureQString cryptofunc::generateObscuringKeyBase64()
{
    // This doesn't need a cryptographically secure RNG, really.
    // Still, we have openSSL...
    return randomBytes(AES_256BIT_KEY_SIZE).toBase64();
}


QString cryptofunc::encryptToBase64(const QString& plaintext,
                                    const QString& key_b64,
                                    const QString& iv_b64)
{
#ifdef DANGER_DEBUG_CRYPTO
    qDebug() << Q_FUNC_INFO
             << "plaintext" << plaintext
             << "key_b64" << key_b64
             << "iv_b64" << iv_b64;
#endif
    SecureQByteArray key_bytes = convert::base64ToSecureBytes(key_b64);
    if (!isValidAesKey(key_bytes)) {
        qCritical() << Q_FUNC_INFO << "Bad AES key";
        return "";
    }
    SecureQByteArray iv_bytes = convert::base64ToSecureBytes(iv_b64);
    SecureQByteArray plaintext_bytes = plaintext.toLocal8Bit();  // no other conversion
    SecureQByteArray ciphertext_bytes;
    aesEncrypt(key_bytes, iv_bytes, plaintext_bytes, ciphertext_bytes);
    QString ciphertext_b64(ciphertext_bytes.toBase64());
#ifdef DANGER_DEBUG_CRYPTO
    qDebug() << "... encrypted to" << ciphertext_b64;
#endif
    return ciphertext_b64;
}


SecureQString cryptofunc::decryptFromBase64(const QString& ciphertext_b64,
                                            const QString& key_b64,
                                            const QString& iv_b64)
{
#ifdef DANGER_DEBUG_CRYPTO
    qDebug() << Q_FUNC_INFO
             << "ciphertext_b64" << ciphertext_b64
             << "key_b64" << key_b64;
#endif
    SecureQByteArray key_bytes = convert::base64ToSecureBytes(key_b64);
    if (!isValidAesKey(key_bytes)) {
        qCritical() << Q_FUNC_INFO << "Bad AES key";
        return "";
    }
    SecureQByteArray ciphertext_bytes = convert::base64ToSecureBytes(ciphertext_b64);
    SecureQByteArray iv_bytes = convert::base64ToSecureBytes(iv_b64);
    SecureQByteArray plaintext_bytes;
    aesDecrypt(key_bytes, iv_bytes, ciphertext_bytes, plaintext_bytes);
    SecureQString plaintext(plaintext_bytes);  // ASSUMES IT IS TEXT.
    // If there are zero bytes in plaintext_bytes, this will go wrong.
#ifdef DANGER_DEBUG_CRYPTO
    qDebug() << "... decrypted to" << plaintext;
#endif
    return plaintext;
}


QString cryptofunc::hash(const QString& plaintext, const QString& salt)
{
    if (salt.length() != SALT_LENGTH_TEXT) {
        qWarning() << "Salt length is" << salt.length()
                   << "but should be" << SALT_LENGTH_TEXT;
    }
    SecureQString to_hash_text(salt + plaintext);
    SecureQByteArray to_hash_bytes = to_hash_text.toLocal8Bit();
    QByteArray hashed_bytes = hashBytes(to_hash_bytes);
    QString hashed_text = hashed_bytes.toBase64();
    QString result = salt + hashed_text;
#ifdef DANGER_DEBUG_CRYPTO
    qDebug() << Q_FUNC_INFO
             << "salt" << salt
             << "+ plaintext" << plaintext
             << "-> " << result;
#endif
    return result;
}


QString cryptofunc::hash(const QString& plaintext)
{
    QString salt = makeSalt();
    return hash(plaintext, salt);
}


bool cryptofunc::matchesHash(const QString& plaintext, const QString& hashed)
{
    if (hashed.length() < SALT_LENGTH_TEXT) {
        return false;
    }
    QString salt = hashed.left(SALT_LENGTH_TEXT);  // recover salt
    return hashed == hash(plaintext, salt);
}


QString cryptofunc::makeSalt()
{
    return randomBytes(SALT_LENGTH_BYTES).toBase64();
}
