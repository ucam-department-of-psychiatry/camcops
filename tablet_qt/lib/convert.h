/*
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
#include <QList>
#include <QMap>
#include <QString>
#include <QUrlQuery>
#include <QVariant>
#include "crypto/secureqbytearray.h"
#include "crypto/secureqstring.h"

class QByteArray;
class QImage;


namespace Convert
{
    // SQL literals

    QString escapeNewlines(QString raw);
    QString unescapeNewlines(QString escaped);

    QString sqlQuoteString(QString raw);
    QString sqlDequoteString(const QString& quoted);

    QString blobToQuotedBase64(const QByteArray& blob);
    QByteArray quotedBase64ToBlob(const QString& quoted);
    QString padHexTwo(const QString& input);
    QString blobToQuotedHex(const QByteArray& blob);
    QByteArray quotedHexToBlob(const QString& hex);

    QString toSqlLiteral(const QVariant& value);
    QVariant fromSqlLiteral(const QString& literal);
    QList<QVariant> csvSqlLiteralsToValues(const QString& csv);
    QString valuesToCsvSqlLiterals(const QList<QVariant>& values);

    // Images

    QByteArray imageToByteArray(const QImage& image,
                                const char* format = "png");
    QVariant imageToVariant(const QImage& image, const char* format = "png");
    QImage byteArrayToImage(const QByteArray& array,
                            const char* format = nullptr);

    // Cryptography

    QByteArray base64ToBytes(const QString& data_b64);
    SecureQByteArray base64ToSecureBytes(const QString& data_b64);

    // Display formatting

    QString prettyValue(const QVariant& variant, QVariant::Type type);
    QString prettyValue(const QVariant& variant);
    QString prettySize(double num, bool space = true, bool binary = false,
                       bool longform = false, const QString& suffix = "B");

    // Network comms

    QUrlQuery getPostDataAsUrlQuery(const QMap<QString, QString>& dict);
    QMap<QString, QString> getReplyDict(const QByteArray& data);
}
