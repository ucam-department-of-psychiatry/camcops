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
#include <QDebug>
#include <QMap>
#include <QSsl>
#include <QString>
#include <QUrlQuery>
#include <QVariant>
#include "crypto/secureqbytearray.h"
#include "crypto/secureqstring.h"
#include "lib/version.h"
#include "maths/mathfunc.h"

class QByteArray;
class QImage;


namespace convert {

// ============================================================================
// SQL literals
// ============================================================================

extern const QString NULL_STR;

QString escapeNewlines(QString raw);
QString unescapeNewlines(const QString& escaped);

QString sqlQuoteString(QString raw);
QString sqlDequoteString(const QString& quoted);

QString blobToQuotedBase64(const QByteArray& blob);
QByteArray quotedBase64ToBlob(const QString& quoted);
QString padHexTwo(const QString& input);
QString blobToQuotedHex(const QByteArray& blob);
QByteArray quotedHexToBlob(const QString& hex);

QString toSqlLiteral(const QVariant& value);
QVariant fromSqlLiteral(const QString& literal);
QVector<QVariant> csvSqlLiteralsToValues(const QString& csv);
QString valuesToCsvSqlLiterals(const QVector<QVariant>& values);

// ============================================================================
// C++ literals
// ============================================================================

QString stringToUnquotedCppLiteral(const QString& raw);
QString stringToCppLiteral(const QString& raw);

QString unquotedCppLiteralToString(const QString& escaped);
QString cppLiteralToString(const QString& escaped);

// ============================================================================
// Images
// ============================================================================

QByteArray imageToByteArray(const QImage& image,
                            const char* format = "png");
QVariant imageToVariant(const QImage& image, const char* format = "png");
QImage byteArrayToImage(const QByteArray& array,
                        bool* successful,
                        const char* format = nullptr);
int convertLengthByDpi(int old_length, qreal to_dpi, qreal from_dpi);
int convertLengthByDpi(int old_length);  // default is runtime, not compile-time
QSize convertSizeByDpi(const QSize& old_size, qreal to_dpi, qreal from_dpi);
QSize convertSizeByDpi(const QSize& old_size);  // default is runtime, not compile-time

// ============================================================================
// Cryptography
// ============================================================================

QByteArray base64ToBytes(const QString& data_b64);
SecureQByteArray base64ToSecureBytes(const QString& data_b64);

// ============================================================================
// Display formatting
// ============================================================================

QString toDp(double x, int dp);
QString prettyValue(const QVariant& variant, int dp, QVariant::Type type);
QString prettyValue(const QVariant& variant, int dp = -1);
QString prettySize(double num, bool space = true, bool binary = false,
                   bool longform = false, const QString& suffix = "B");
QString prettyPointer(const void* pointer);

// ============================================================================
// Networking
// ============================================================================

QUrlQuery getPostDataAsUrlQuery(const QMap<QString, QString>& dict);
QMap<QString, QString> getReplyDict(const QByteArray& data);
QString getReplyString(const QByteArray& data);

extern const QString SSLPROTODESC_SSLV3;
extern const QString SSLPROTODESC_SSLV2;
extern const QString SSLPROTODESC_TLSV1_0;
extern const QString SSLPROTODESC_TLSV1_1;
extern const QString SSLPROTODESC_TLSV1_2;
extern const QString SSLPROTODESC_ANYPROTOCOL;
extern const QString SSLPROTODESC_TLSV1_SSLV3;
extern const QString SSLPROTODESC_SECUREPROTOCOLS;
extern const QString SSLPROTODESC_TLSV1_0_OR_LATER;
extern const QString SSLPROTODESC_TLSV1_1_OR_LATER;
extern const QString SSLPROTODESC_TLSV1_2_OR_LATER;
extern const QString SSLPROTODESC_UNKNOWN_PROTOCOL;

QString describeSslProtocol(QSsl::SslProtocol protocol);
QSsl::SslProtocol sslProtocolFromDescription(const QString& desc);

// ============================================================================
// QChar oddities
// ============================================================================

QVariant toQCharVariant(const QVariant& v);

// ============================================================================
// Specific vectors as strings
// ============================================================================

QString intVectorToCsvString(const QVector<int>& vec);
QVector<int> csvStringToIntVector(const QString& str);

QString qStringListToCsvString(const QStringList& vec);
QStringList csvStringToQStringList(const QString& str);

// ============================================================================
// QVariant modifications
// ============================================================================

extern const char* TYPENAME_QVECTOR_INT;
extern const char* TYPENAME_VERSION;
void registerTypesForQVariant();
bool isQVariantOfUserType(const QVariant& v, const QString& type_name);
QVector<int> qVariantToIntVector(const QVariant& v);

// ============================================================================
// JSON
// ============================================================================

QString stringListToJson(const QStringList& list, bool compact = true);

// ============================================================================
// Physical units (other than time: in datetime namespace)
// ============================================================================

extern const double CM_PER_INCH;
extern const int CM_PER_M;
extern const int INCHES_PER_FOOT;

extern const int POUNDS_PER_STONE;
extern const int OUNCES_PER_POUND;
extern const int GRAMS_PER_KG;
extern const double GRAMS_PER_POUND;
extern const double POUNDS_PER_KG;

double metresFromFeetInches(double feet, double inches);
void feetInchesFromMetres(double metres, int& feet, double& inches);
double kilogramsFromStonesPoundsOunces(double stones, double pounds,
                                       double ounces = 0);
void stonesPoundsFromKilograms(
        double kilograms, int& stones, double& pounds);
void stonesPoundsOuncesFromKilograms(
        double kilograms, int& stones, int& pounds, double& ounces);

int msFromSec(qreal seconds);


// ============================================================================
// Tests
// ============================================================================

template<typename T>
void assert_eq(const T& a, const T& b)
{
    if (a == b) {
        qDebug() << "Conversion success:" << a << "==" << b;
    } else {
        qCritical() << "Conversion failure:" << a << "!=" << b;
        Q_ASSERT(false);
        qFatal("Stopping");
    }
}

template<>
void assert_eq(const double& a, const double& b);

void testConversions();


}  // namespace convert


// ============================================================================
// Using QVector in QVariant: see also convert::registerQVectorTypesForQVariant()
// ============================================================================

Q_DECLARE_METATYPE(QVector<int>)
