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

#define DEBUG_UNIT_CONVERSION

#include "convert.h"
#include <cmath>
#include <QBuffer>
#include <QByteArray>
#include <QChar>
#include <QDate>
#include <QDateTime>
#include <QDebug>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QRegularExpression>
#include <QtMath>
#include <QUrl>
#include "lib/datetime.h"
#include "lib/uifunc.h"
#include "lib/stringfunc.h"

namespace convert {

// ============================================================================
// Constants used in several places
// ============================================================================

const QChar COMMA(',');
const QChar SQUOTE('\'');  // single quote
const QChar DQUOTE('"');  // double quote
const QChar NL('\n');  // newline
const QChar CR('\r');  // carriage return
const QChar TAB('\t');
const QChar BACKSLASH('\\');
const QChar SPACE(' ');
const QChar ZERO('0');

const ushort UNICODE_COMMA = COMMA.unicode();
const ushort UNICODE_DQUOTE = DQUOTE.unicode();
const ushort UNICODE_NL = NL.unicode();
const ushort UNICODE_CR = CR.unicode();
const ushort UNICODE_TAB = TAB.unicode();
const ushort UNICODE_BACKSLASH = BACKSLASH.unicode();
const ushort UNICODE_SPACE = SPACE.unicode();


// ============================================================================
// SQL literals
// ============================================================================

const QString NULL_STR("NULL");

const QString RECORD_RE_STR("^([\\S]+?):\\s*([\\s\\S]*)");
// double-backslashes for C++ escaping
// \s whitespace, \S non-whitespace
// ? makes the + lazy, not greedy
// ... thus: (lazy-non-whitespace) : whitespace (anything)
const QRegularExpression RECORD_RE(RECORD_RE_STR);


QString escapeNewlines(QString raw)
{
    // Raw string literal, from C++ 11 (note the parentheses):
    // http://en.cppreference.com/w/cpp/language/string_literal
    raw.replace(R"(\)", R"(\\)");
    raw.replace("\n", R"(\n)");
    raw.replace("\r", R"(\r)");
    return raw;
}


QString unescapeNewlines(const QString& escaped)
{
    if (escaped.isEmpty()) {
        return escaped;
    }
    QString result;
    bool in_escape = false;
    int n = escaped.length();
    for (int i = 0; i < n; ++i) {
        QChar c = escaped.at(i);
        if (in_escape) {
            // Can't use switch statement with a QChar
            if (c == 'r') {
                result += "\r";
            } else if (c == 'n') {
                result += "\n";
            } else {
                result += c;
            }
            in_escape = false;
        } else {
            if (c == SQUOTE) {
                in_escape = true;
            } else {
                result += c;
            }
        }
    }
    return result;
}


QString sqlQuoteString(QString raw)
{
    // In: my name's Bob
    // Out: 'my name''s Bob'
    raw.replace("'", "''");
    return QString("'%1'").arg(raw);
}


QString sqlDequoteString(const QString& quoted)
{
    // In: 'my name''s Bob'
    // Out: my name's Bob

    // Strip off outside quotes:
    int n = quoted.length();
    if (n < 2 || quoted.at(0) != SQUOTE || quoted.at(n - 1) != SQUOTE) {
        // Wrong format
        return QString();
    }
    QString raw = quoted.mid(1, n - 2);
    // De-escape quotes:
    raw.replace("''", "'");
    return raw;
}


QString blobToQuotedBase64(const QByteArray& blob)
{
    // Returns in the format: 64'...'
    return QString("64'%1'").arg(QString(blob.toBase64()));
}


QByteArray quotedBase64ToBlob(const QString& quoted)
{
    // Reverses blobToQuotedBase64()
    int n = quoted.length();
    if (n < 4 || !quoted.startsWith("64'") || !quoted.endsWith(SQUOTE)) {
        // Wrong format
        return QByteArray();
    }
    QString b64data = quoted.mid(3, n - 4);
    return QByteArray::fromBase64(b64data.toLocal8Bit());
}


QString padHexTwo(const QString& input)
{
    return input.length() == 1 ? QString("0") + input : input;
}


QString blobToQuotedHex(const QByteArray& blob)
{
    // Returns in the format: X'01FF76A8'
    // Since Qt is magic:
    return QString("X'%1'").arg(QString(blob.toHex()));
}


QByteArray quotedHexToBlob(const QString& hex)
{
    // Reverses blobToQuotedHex()
    int n = hex.length();
    if (n < 3 || !hex.startsWith("X'") || !hex.endsWith(SQUOTE)) {
        // Wrong format
        return QByteArray();
    }
    QString hexdata = hex.mid(2, n - 3);
    return QByteArray::fromHex(hexdata.toLocal8Bit());
}


QString toSqlLiteral(const QVariant& value)
{
    if (value.isNull()) {
        return NULL_STR;
    }
    QVariant::Type variant_type = value.type();
    switch (variant_type) {
    // Integer types
    case QVariant::Int:
        return QString("%1").arg(value.toInt());
    case QVariant::LongLong:
        return QString("%1").arg(value.toLongLong());
    case QVariant::UInt:
        return QString("%1").arg(value.toUInt());
    case QVariant::ULongLong:
        return QString("%1").arg(value.toULongLong());

    // Boolean
    case QVariant::Bool:
        return QString("%1").arg(value.toInt());  // boolean to integer

    // Floating-point:
    case QVariant::Double:
        return QString("%1").arg(value.toDouble());

    // String
    case QVariant::Char:
    case QVariant::String:
        return sqlQuoteString(escapeNewlines(value.toString()));
    case QVariant::StringList:
        return sqlQuoteString(qStringListToCsvString(value.toStringList()));

    // Dates, times
    case QVariant::Date:
        return value.toDate().toString("'yyyy-MM-dd'");
    case QVariant::DateTime:
        return QString("'%1'").arg(datetime::datetimeToIsoMs(value.toDateTime()));
    case QVariant::Time:
        return value.toTime().toString("'HH:mm:ss'");

    // BLOB types
    case QVariant::ByteArray:
        // Base 64 is more efficient for network transmission than hex.
        return blobToQuotedBase64(value.toByteArray());

    // Other
    case QVariant::Invalid:
        uifunc::stopApp("toSqlLiteral: Invalid field type");
        // We'll never get here, but to stop compilers complaining:
        return NULL_STR;

    case QVariant::UserType:
        if (isQVariantOfUserType(value, TYPENAME_QVECTOR_INT)) {
            QVector<int> intvec = qVariantToIntVector(value);
            return sqlQuoteString(intVectorToCsvString(intvec));
        }
        uifunc::stopApp("toSqlLiteral: Unknown user type");
        // We'll never get here, but to stop compilers complaining:
        return NULL_STR;

    default:
        uifunc::stopApp("toSqlLiteral: Unknown user type: " + variant_type);
        // We'll never get here, but to stop compilers complaining:
        return NULL_STR;
    }
}


QVariant fromSqlLiteral(const QString& literal)
{
    if (literal.isEmpty() ||
            literal.compare(NULL_STR, Qt::CaseInsensitive) == 0) {
        // NULL
        return QVariant();
    }

    int n = literal.length();

    if (n >= 4 && literal.startsWith("64'") && literal.endsWith(SQUOTE)) {
        // Base 64-encoded BLOB
        // Waste of time doing a more sophisticated (e.g. regex) check. If it
        // passes this test, it's *claiming* to be a base-64 BLOB, and we're
        // not going to decode it as anything else, even if it's duff.
        return quotedBase64ToBlob(literal);
    }

    if (n >= 3 && literal.startsWith("X'") && literal.endsWith(SQUOTE)) {
        // Hex-encoded BLOB
        return quotedHexToBlob(literal);
    }

    if (n >= 2 && literal.startsWith(SQUOTE) && literal.endsWith(SQUOTE)) {
        // String, date, or time... we will let autoconversion take care of
        // dates/times given as sensible string literals.
        return unescapeNewlines(sqlDequoteString(literal));
    }

    // Numeric
    if (literal.contains(".")) {
        return literal.toDouble();
    }

    return literal.toInt();
}


QVector<QVariant> csvSqlLiteralsToValues(const QString& csv)
{
    // In: 34, NULL, 'a string''s test, with commas', X'0FB2AA', 64'c3VyZS4='
    // Out: split by commas, dealing with quotes appropriately
    QVector<QVariant> values;
    int n = csv.length();
    bool in_quotes = false;
    int startpos = 0;
    int pos = 0;
    while (pos < n) {
        QChar at_pos = csv.at(pos);
        if (!in_quotes) {
            if (at_pos == COMMA) {
                // end of chunk
                QString chunk = csv.mid(startpos, pos - startpos).trimmed();
                // ... will not include csv[pos]
                startpos = pos + 1;  // one beyond the comma

                // ------------------------------------------------------------
                // SQL literal processing here: more memory-efficient (e.g.
                // with BLOBs) to process here rather than returning large
                // string intermediates unnecessarily to a calling function
                // that does the next step.
                // ------------------------------------------------------------
                values.append(fromSqlLiteral(chunk));

            } else if (at_pos == SQUOTE) {
                // start of quote
                in_quotes = true;
            }

        } else {
            if (at_pos == SQUOTE && pos < n - 1 && csv.at(pos + 1) == SQUOTE) {
                // double quote, '', is an escaped quote, not end of quote
                pos += 1;  // skip one more than we otherwise would
            } else if (at_pos == SQUOTE) {
                // end of quote
                in_quotes = false;
            }
        }

        pos += 1;
    }
    // Last chunk
    QString chunk = csv.mid(startpos, n - startpos).trimmed();
    // ------------------------------------------------------------------------
    // More SQL literal processing here
    // ------------------------------------------------------------------------
    values.append(fromSqlLiteral(chunk));
    return values;
}


QString valuesToCsvSqlLiterals(const QVector<QVariant>& values)
{
    QStringList literals;
    for (auto value : values) {
        literals.append(toSqlLiteral(value));
    }
    return literals.join(COMMA);
}


// ============================================================================
// C++ literals
// ============================================================================

const int BASE_OCTAL = 8;
const int OCTAL_NUM_DIGITS = 3;


QString stringToUnquotedCppLiteral(const QString& raw)
{
    // https://stackoverflow.com/questions/10220401
    QString escaped;
    for (QChar c : raw) {
        ushort u = c.unicode();
        if (u == UNICODE_NL) {
            escaped += R"(\n)";
        } else if (u == UNICODE_CR) {
            escaped += R"(\r)";
        } else if (u == UNICODE_TAB) {
            escaped += R"(\t)";
        } else if (u == UNICODE_BACKSLASH) {
            escaped += R"(\\)";
        } else if (u == UNICODE_DQUOTE) {
            escaped += R"(\")";
        } else if (u < UNICODE_SPACE) {
            QString octal = QString("\\%1").arg(u, OCTAL_NUM_DIGITS,
                                                BASE_OCTAL, ZERO);
            // ... number, fieldwidth (+ right align, - left align), base, fillchar
            escaped += octal;
        } else {
            escaped += c;
        }
    }
    return escaped;
}


QString stringToCppLiteral(const QString &raw)
{
    return DQUOTE + stringToUnquotedCppLiteral(raw) + DQUOTE;
}


QString unquotedCppLiteralToString(const QString& escaped)
{
    // reverses stringToUnquotedCppLiteral()
    QString raw;
    QString escape_digits;
    bool in_escape = false;
    bool in_octal = false;
    for (QChar c : escaped) {
        ushort u = c.unicode();
        if (in_escape) {
            if (in_octal) {
                bool ok = c.isDigit();
                if (ok) {
                    escape_digits.append(c);
                    if (escape_digits.length() >= OCTAL_NUM_DIGITS) {
                        bool ok;
                        ushort code = escape_digits.toInt(&ok, BASE_OCTAL);
                        if (ok) {
                            // our octal code has finished
                            raw += QChar(code);
                            in_escape = false;
                        }
                    }
                }
                if (!ok) {
                    qWarning() << Q_FUNC_INFO << "Bad octal in:" << escaped;
                    in_escape = false;
                }
                // otherwise, in_escape remains true
            } else if (u == UNICODE_BACKSLASH) {
                in_octal = true;
                // in_escape remains true
            } else {
                if (c == 'r') {
                    raw += CR;
                } else if (c == 'n') {
                    raw += NL;
                } else {
                    qWarning() << Q_FUNC_INFO << "Unknown escape code:" << c;
                }
                in_escape = false;
            }
        } else {
            if (u == UNICODE_BACKSLASH) {
                in_escape = true;
                in_octal = false;
                escape_digits = "";
            } else {
                raw += c;
            }
        }
    }
    return raw;
}


QString cppLiteralToString(const QString& escaped)
{
    // reverses stringToCppLiteral()
    int len = escaped.length();
    if (len >= 2 && escaped.at(0) == DQUOTE && escaped.at(len - 1) == DQUOTE) {
        // quoted string
        return unquotedCppLiteralToString(escaped.mid(1, len - 2));
    } else {
        return unquotedCppLiteralToString(escaped);
    }
}


// ============================================================================
// Images
// ============================================================================

QByteArray imageToByteArray(const QImage& image, const char* format)
{
    // I thought passing a QImage to a QVariant-accepting function would lead
    // to autoconversion via
    //     http://doc.qt.io/qt-5/qimage.html#operator-QVariant
    // ... but it doesn't.
    // So: http://stackoverflow.com/questions/27343576
    QByteArray arr;
    QBuffer buffer(&arr);
    buffer.open(QIODevice::WriteOnly);
    image.save(&buffer, format);
    return arr;
}


QVariant imageToVariant(const QImage& image, const char* format)
{
    return QVariant(imageToByteArray(image, format));
}


QImage byteArrayToImage(const QByteArray& array, const char* format)
{
    QImage image;
    image.loadFromData(array, format);
    return image;
}


// ============================================================================
// Cryptography
// ============================================================================

QByteArray base64ToBytes(const QString& data_b64)
{
    return QByteArray::fromBase64(data_b64.toLocal8Bit());
}


SecureQByteArray base64ToSecureBytes(const QString& data_b64)
{
    return SecureQByteArray::fromBase64(data_b64.toLocal8Bit());
}


// ============================================================================
// Display formatting
// ============================================================================

QString toDp(double x, int dp)
{
    return QString("%1").arg(x, 0, 'f', dp);
}


QString prettyValue(const QVariant& variant, int dp, QVariant::Type type)
{
    if (variant.isNull()) {
        return NULL_STR;
    }
    switch (type) {
    case QVariant::ByteArray:
        return "<binary>";
    case QVariant::Double:
        if (dp < 0) {
            return variant.toString();
        }
        return toDp(variant.toDouble(), dp);
    case QVariant::String:
        {
            QString escaped = variant.toString().toHtmlEscaped();
            stringfunc::toHtmlLinebreaks(escaped, false);
            return escaped;
        }
    case QVariant::StringList:
        {
            QStringList raw = variant.toStringList();
            QStringList escaped;
            for (const QString& r : raw) {
                QString e = r.toHtmlEscaped();
                stringfunc::toHtmlLinebreaks(e, false);
                escaped.append(e);
            }
            return escaped.join(",");
        }
    case QVariant::UserType:
        if (isQVariantOfUserType(variant, TYPENAME_QVECTOR_INT)) {
            QVector<int> intvec = qVariantToIntVector(variant);
            return intVectorToCsvString(intvec);
        }
        uifunc::stopApp("prettyValue: Unknown user type");
    default:
        return variant.toString();
    }
}


QString prettyValue(const QVariant& variant, int dp)
{
    return prettyValue(variant, dp, variant.type());
}


const QStringList PREFIXES_SHORT_BINARY{"", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi", "Yi"};
const QStringList PREFIXES_LONG_BINARY{"", "kibi", "mebi", "gibi", "tebi", "peti", "exbi", "zebi", "yobi"};
const QStringList PREFIXES_SHORT_DECIMAL{"", "k", "M", "G", "T", "P", "E", "Z", "Y"};
const QStringList PREFIXES_LONG_DECIMAL{"", "kilo", "mega", "giga", "tera", "peta", "exa", "zetta", "yotta"};


QString prettySize(double num, bool space, bool binary, bool longform,
                   const QString& suffix)
{
    // http://stackoverflow.com/questions/3758606/how-to-convert-byte-size-into-human-readable-format-in-java
    const QStringList& prefixes = binary
            ? (longform ? PREFIXES_LONG_BINARY : PREFIXES_SHORT_BINARY)
            : (longform ? PREFIXES_LONG_DECIMAL : PREFIXES_SHORT_DECIMAL);
    QString optional_space = space ? " " : "";
    double base = binary ? 1024 : 1000;
    int exponent = (int)(qLn(num) / qLn(base));
    exponent = qBound(0, exponent, prefixes.length() - 1);
    QString prefix = prefixes.at(exponent);
    double converted_num = num / pow(base, exponent);
    int precision = (exponent == 0) ? 0 : 1;  // decimals, for 'f'
    return QString("%1%2%3%4")
            .arg(converted_num, 0, 'f', precision)
            .arg(optional_space,
                 prefix,
                 suffix);
}


QString prettyPointer(const void* pointer)
{
    // http://stackoverflow.com/questions/8881923/how-to-convert-a-pointer-value-to-qstring
    return QString("0x%1").arg((quintptr)pointer,
                               QT_POINTER_SIZE * 2, 16, QChar('0'));
}


// ============================================================================
// Networking
// ============================================================================

QMap<QString, QString> getReplyDict(const QByteArray& data)
{
    // For server replies looking like key1:value1\nkey2:value2 ...
    QList<QByteArray> lines = data.split('\n');
    QMap<QString, QString> dict;
    for (auto line : lines) {
        QRegularExpressionMatch match = RECORD_RE.match(line);
        if (match.hasMatch()) {
            QString key = match.captured(1);
            QString value = match.captured(2);
            dict[key] = value;
        }
    }
    return dict;
}


QUrlQuery getPostDataAsUrlQuery(const QMap<QString, QString>& dict)
{
    // http://stackoverflow.com/questions/2599423/how-can-i-post-data-to-a-url-using-qnetworkaccessmanager

    // We had a difficulty here in that semicolons were not being encoded.
    // This thread describes the problem (not a Qt bug; matches relevant RFC):
    // - https://bugreports.qt.io/browse/QTBUG-50843
    // Note in particular Thiago Maciera's comment that "QUrlQuery manages a
    // list of key-value pairs of *encoded* strings."

    QUrlQuery postdata;
    QMapIterator<QString, QString> it(dict);
    while (it.hasNext()) {
        it.next();
        postdata.addQueryItem(QUrl::toPercentEncoding(it.key()),
                              QUrl::toPercentEncoding(it.value()));
    }
    return postdata;
}

// http://doc.qt.io/qt-5/qssl.html#SslProtocol-enum
const QString SSLPROTODESC_SSLV3 = "SslV3";
const QString SSLPROTODESC_SSLV2 = "SslV2";
const QString SSLPROTODESC_TLSV1_0 = "TlsV1_0";
const QString SSLPROTODESC_TLSV1_1 = "TlsV1_1";
const QString SSLPROTODESC_TLSV1_2 = "TlsV1_2";
const QString SSLPROTODESC_ANYPROTOCOL = "AnyProtocol";
const QString SSLPROTODESC_TLSV1_SSLV3 = "TlsV1SslV3";
const QString SSLPROTODESC_SECUREPROTOCOLS = "SecureProtocols";
const QString SSLPROTODESC_TLSV1_0_OR_LATER = "TlsV1_0OrLater";
const QString SSLPROTODESC_TLSV1_1_OR_LATER = "TlsV1_1OrLater";
const QString SSLPROTODESC_TLSV1_2_OR_LATER = "TlsV1_2OrLater";
const QString SSLPROTODESC_UNKNOWN_PROTOCOL = "UnknownProtocol";


QString describeSslProtocol(QSsl::SslProtocol protocol) {
    using namespace QSsl;
    switch (protocol) {
    case SslV3: return SSLPROTODESC_SSLV3;
    case SslV2: return SSLPROTODESC_SSLV2;
    case TlsV1_0: return SSLPROTODESC_TLSV1_0;
#if QT_DEPRECATED_SINCE(5,0)
    case TlsV1: return TLSV1_0;
#endif
    case TlsV1_1: return SSLPROTODESC_TLSV1_1;
    case TlsV1_2: return SSLPROTODESC_TLSV1_2;
    case AnyProtocol: return SSLPROTODESC_ANYPROTOCOL;
    case TlsV1SslV3: return SSLPROTODESC_TLSV1_SSLV3;
    case SecureProtocols: return SSLPROTODESC_SECUREPROTOCOLS;
    case TlsV1_0OrLater: return SSLPROTODESC_TLSV1_0_OR_LATER;
    case TlsV1_1OrLater: return SSLPROTODESC_TLSV1_1_OR_LATER;
    case TlsV1_2OrLater: return SSLPROTODESC_TLSV1_2_OR_LATER;
    default:
    case UnknownProtocol: return SSLPROTODESC_UNKNOWN_PROTOCOL;
    }
}

QSsl::SslProtocol sslProtocolFromDescription(const QString& desc) {
    using namespace QSsl;
    if (desc == SSLPROTODESC_SSLV3) return SslV3;
    if (desc == SSLPROTODESC_SSLV2) return SslV2;
    if (desc == SSLPROTODESC_TLSV1_0) return TlsV1_0;
    if (desc == SSLPROTODESC_TLSV1_1) return TlsV1_1;
    if (desc == SSLPROTODESC_TLSV1_2) return TlsV1_2;
    if (desc == SSLPROTODESC_ANYPROTOCOL) return AnyProtocol;
    if (desc == SSLPROTODESC_TLSV1_SSLV3) return TlsV1SslV3;
    if (desc == SSLPROTODESC_SECUREPROTOCOLS) return SecureProtocols;
    if (desc == SSLPROTODESC_TLSV1_0_OR_LATER) return TlsV1_0OrLater;
    if (desc == SSLPROTODESC_TLSV1_1_OR_LATER) return TlsV1_1OrLater;
    if (desc == SSLPROTODESC_TLSV1_2_OR_LATER) return TlsV1_2OrLater;
    return UnknownProtocol;
}

// ============================================================================
// QChar oddities
// ============================================================================

QVariant toQCharVariant(const QVariant& v)
{
    // The oddity is that a QVariant of type QString, even if of length 1,
    // won't convert() to type QChar.
    // - http://lists.qt-project.org/pipermail/interest/2016-January/020587.html
    if (v.isNull() || !v.isValid()) {
        return QVariant();
    }
    QString str = v.toString();
    if (str.isEmpty()) {
        return QVariant();
    }
    return str.at(0);
}


// ============================================================================
// Specific vectors as strings
// ============================================================================

QString intVectorToCsvString(const QVector<int>& vec)
{
    QStringList strings;
    for (int value : vec) {
        strings.append(QString::number(value));
    }
    return strings.join(COMMA);
}


QVector<int> csvStringToIntVector(const QString& str)
{
    QStringList strings = str.split(COMMA);
    QVector<int> vec;
    for (const QString& s : strings) {
        vec.append(s.toInt());
    }
    return vec;
}


QString qStringListToCsvString(const QStringList& vec)
{
    QStringList words;
    for (QString word : vec) {
        words.append(stringToCppLiteral(word));
    }
    return words.join(COMMA);
}


QStringList csvStringToQStringList(const QString& str)
{
    QStringList words;
    QString word;
    bool in_quote = false;
    bool in_escape = false;
    for (QChar c : str) {
        ushort u = c.unicode();
        if (in_escape) {
            // We don't have to be concerned with sophisticated escaping.
            // We just want to make sure that \" isn't treated like it's an
            // opening or closing quote, but that the " in \\" is.
            word += c;
            in_escape = false;
        } else {
            if (u == UNICODE_BACKSLASH) {
                word += c;
                in_escape = true;
            } else if (in_quote) {
                word += c;
                if (u == UNICODE_DQUOTE) {
                    // end of quoted string
                    in_quote = false;
                }
            } else {
                // Not within quotes, so commas mean CSV breaks
                if (u == UNICODE_COMMA) {
                    // CSV break: MAIN POINT OF ONWARD PROCESSING
                    words.append(cppLiteralToString(word.trimmed()));
                    word = "";
                } else if (u == UNICODE_DQUOTE) {
                    // start of quoted string
                    word += c;
                    in_quote = true;  // so we can have commas within quotes
                } else {
                    // character outside quotes
                    word += c;
                }
            }
        }
    }
    words.append(cppLiteralToString(word.trimmed()));
    return words;
}


// ============================================================================
// QVariant modifications
// ============================================================================

const char* TYPENAME_QVECTOR_INT("QVector<int>");


void registerQVectorTypesForQVariant()
{
    // http://stackoverflow.com/questions/6177906/is-there-a-reason-why-qvariant-accepts-only-qlist-and-not-qvector-nor-qlinkedlis
    qRegisterMetaType<QVector<int>>(TYPENAME_QVECTOR_INT);
}


bool isQVariantOfUserType(const QVariant& v, const QString& type_name)
{
    return v.userType() >= QMetaType::User && v.typeName() == type_name;
}


QVector<int> qVariantToIntVector(const QVariant& v)
{
    // We're adding support for QVector<int>.
    // - http://stackoverflow.com/questions/6177906/is-there-a-reason-why-qvariant-accepts-only-qlist-and-not-qvector-nor-qlinkedlis
    // - http://doc.qt.io/qt-5/qvariant.html
    // - http://doc.qt.io/qt-5/qmetatype.html
    return v.value<QVector<int>>();
}


// ============================================================================
// JSON
// ============================================================================

QString stringListToJson(const QStringList& list, bool compact)
{
    QJsonArray ja(QJsonArray::fromStringList(list));
    QJsonDocument jd(ja);
    return jd.toJson(compact ? QJsonDocument::Compact
                             : QJsonDocument::Indented);
}


// ============================================================================
// Physical units
// ============================================================================

#ifdef DEBUG_UNIT_CONVERSION
#define UNIT_CONVERSION "Unit conversion: "
#endif

const double CM_PER_INCH = 2.54;
const double CM_PER_M = 100;
const double INCHES_PER_FOOT = 12;

const double POUNDS_PER_STONE = 14;
const double OUNCES_PER_POUND = 16;
const double GRAMS_PER_KG = 1000;
const double GRAMS_PER_POUND = 453.592;
const double POUNDS_PER_KG = 2.20462;


double metresFromFeetInches(double feet, double inches)
{
    double metres = (feet * INCHES_PER_FOOT + inches) * CM_PER_INCH / CM_PER_M;
#ifdef DEBUG_UNIT_CONVERSION
    qDebug() << UNIT_CONVERSION
             << feet << "ft" << inches << "in ->" << metres << "m";
#endif
    return metres;
}


void feetInchesFromMetres(double metres, int& feet, double& inches)
{
    double total_inches = metres * CM_PER_M / CM_PER_INCH;
    feet = std::trunc(total_inches / INCHES_PER_FOOT);
    inches = std::fmod(total_inches, INCHES_PER_FOOT);
#ifdef DEBUG_UNIT_CONVERSION
    qDebug() << UNIT_CONVERSION
             << metres << "m ->" << feet << "ft" << inches << "in";
#endif
}


double kilogramsFromStonesPoundsOunces(double stones, double pounds,
                                       double ounces)
{
    double kg = (stones * POUNDS_PER_STONE +
                 pounds +
                 ounces / OUNCES_PER_POUND) * GRAMS_PER_POUND / GRAMS_PER_KG;
#ifdef DEBUG_UNIT_CONVERSION
    qDebug() << UNIT_CONVERSION
             << stones << "st" << pounds << "lb" << ounces << "oz ->"
             << kg << "kg";
#endif
    return kg;
}


void stonesPoundsFromKilograms(double kilograms,
                               int& stones, double& pounds)
{
    double total_pounds = kilograms * POUNDS_PER_KG;
    stones = std::trunc(total_pounds / POUNDS_PER_STONE);
    pounds = std::fmod(total_pounds, POUNDS_PER_STONE);
#ifdef DEBUG_UNIT_CONVERSION
    qDebug() << UNIT_CONVERSION
             << kilograms << "kg ->" << stones << "st" << pounds << "lb";
#endif
}


void stonesPoundsOuncesFromKilograms(double kilograms,
                                     int& stones, int& pounds, double& ounces)
{
    double total_pounds = kilograms * POUNDS_PER_KG;
    stones = std::trunc(total_pounds / POUNDS_PER_STONE);
    double float_pounds = std::fmod(total_pounds, POUNDS_PER_STONE);
    pounds = std::trunc(float_pounds);
    ounces = std::fmod(float_pounds, 1);
#ifdef DEBUG_UNIT_CONVERSION
    qDebug() << UNIT_CONVERSION << kilograms << "kg ->"
             << stones << "st" << pounds << "lb" << ounces << "oz";
#endif
}


// ============================================================================
// Tests
// ============================================================================

void testConversions()
{
    qDebug() << "Testing conversions...";

    QStringList stringlist{"a", "b", "c1\nc2"};
    QString stringlist_to_str(R"("a","b","c1\nc2")");
    assert_eq(qStringListToCsvString(stringlist), stringlist_to_str);
    assert_eq(csvStringToQStringList(stringlist_to_str), stringlist);

    qDebug() << "... all conversions correct.";
}


}  // namespace convert
