/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

// #define DEBUG_UNIT_CONVERSION
// #define DEBUG_IMAGE_CONVERSION_TIMES

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
#include <QMetaType>
#include <QRegularExpression>
#include <QtMath>
#include <QUrl>

#include "common/preprocessor_aid.h"  // IWYU pragma: keep
#include "common/uiconst.h"
#include "lib/customtypes.h"
#include "lib/datetime.h"
#include "lib/errorfunc.h"
#include "lib/stringfunc.h"
#include "maths/floatingpoint.h"
#include "maths/mathfunc.h"

namespace convert {

// ============================================================================
// Constants used in several places internally
// ============================================================================

const QChar BACKSLASH('\\');
const QChar COMMA(',');
const QChar CR('\r');  // carriage return
const QChar DQUOTE('"');  // double quote
const QChar NL('\n');  // newline
const QChar QMARK('?');
const QChar SPACE(' ');
const QChar SQUOTE('\'');  // single quote
const QChar TAB('\t');
const QChar ZERO('0');

const ushort UNICODE_BACKSLASH = BACKSLASH.unicode();
const ushort UNICODE_COMMA = COMMA.unicode();
const ushort UNICODE_CR = CR.unicode();
const ushort UNICODE_DQUOTE = DQUOTE.unicode();
const ushort UNICODE_NL = NL.unicode();
const ushort UNICODE_SPACE = SPACE.unicode();
const ushort UNICODE_TAB = TAB.unicode();
// const ushort UNICODE_ZERO = ZERO.unicode();

// ============================================================================
// SQL literals
// ============================================================================

const QString NULL_STR(QStringLiteral("NULL"));

const QString RECORD_RE_STR(QStringLiteral(R"(^([\S]+?):\s*([\s\S]*))"));
// double-backslashes for C++ escaping, or C++ raw string R"(...)"
// \s whitespace, \S non-whitespace
// ? makes the + lazy, not greedy
// ... thus: (lazy-non-whitespace) : whitespace (anything)
const QRegularExpression RECORD_RE(RECORD_RE_STR);

QString escapeNewlines(QString raw)
{
    // Raw string literal, from C++ 11 (note the parentheses):
    // http://en.cppreference.com/w/cpp/language/string_literal
    raw.replace(
        QStringLiteral(R"(\)"), QStringLiteral(R"(\\)")
    );  // escape backslashes
    raw.replace(
        QStringLiteral("\n"), QStringLiteral(R"(\n)")
    );  // escape LF (\n) to "\n" two-char literal
    raw.replace(
        QStringLiteral("\r"), QStringLiteral(R"(\r)")
    );  // escape CR (\r) to "\r" two-char literal
    return raw;
}

QString unescapeNewlines(const QString& escaped)
{
    if (escaped.isEmpty()) {
        return escaped;
    }
    QString result;
    bool in_escape = false;
    const int n = escaped.length();
    for (int i = 0; i < n; ++i) {
        const QChar c = escaped.at(i);
        if (in_escape) {
            // Can't use switch statement with a QChar
            if (c == 'r') {
                result += QStringLiteral("\r");
            } else if (c == 'n') {
                result += QStringLiteral("\n");
            } else {
                result += c;
            }
            in_escape = false;
        } else {
            if (c == BACKSLASH) {
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
    raw.replace(QStringLiteral("'"), QStringLiteral("''"));
    return QString(QStringLiteral("'%1'")).arg(raw);
}

QString sqlDequoteString(const QString& quoted)
{
    // In: 'my name''s Bob'
    // Out: my name's Bob

    // Strip off outside quotes:
    const int n = quoted.length();
    if (n < 2 || quoted.at(0) != SQUOTE || quoted.at(n - 1) != SQUOTE) {
        // Wrong format
        return QString();
    }
    QString raw = quoted.mid(1, n - 2);
    // De-escape quotes:
    raw.replace(QStringLiteral("''"), QStringLiteral("'"));
    return raw;
}

QString blobToQuotedBase64(const QByteArray& blob)
{
    // Returns in the format: 64'...'
    return QString(QStringLiteral("64'%1'")).arg(QString(blob.toBase64()));
}

QByteArray quotedBase64ToBlob(const QString& quoted)
{
    // Reverses blobToQuotedBase64()
    const int n = quoted.length();
    if (n < 4 || !quoted.startsWith(QStringLiteral("64'"))
        || !quoted.endsWith(SQUOTE)) {
        // Wrong format
        return QByteArray();
    }
    const QString b64data = quoted.mid(3, n - 4);
    return QByteArray::fromBase64(b64data.toLocal8Bit());
}

QString padHexTwo(const QString& input)
{
    return input.length() == 1 ? QString(QStringLiteral("0")) + input : input;
}

QString blobToQuotedHex(const QByteArray& blob)
{
    // Returns in the format: X'01FF76A8'
    // Since Qt is magic:
    return QString(QStringLiteral("X'%1'")).arg(QString(blob.toHex()));
}

QByteArray quotedHexToBlob(const QString& hex)
{
    // Reverses blobToQuotedHex()
    const int n = hex.length();
    if (n < 3 || !hex.startsWith(QStringLiteral("X'"))
        || !hex.endsWith(SQUOTE)) {
        // Wrong format
        return QByteArray();
    }
    const QString hexdata = hex.mid(2, n - 3);
    return QByteArray::fromHex(hexdata.toLocal8Bit());
}

QString toSqlLiteral(const QVariant& value)
{
    if (value.isNull()) {
        return NULL_STR;
    }
    const int variant_type = value.typeId();
    QString retval;
    switch (variant_type) {
        // Integer types
        case QMetaType::Int:
            retval.setNum(value.toInt());
            return retval;
        case QMetaType::LongLong:
            retval.setNum(value.toLongLong());
            return retval;
        case QMetaType::UInt:
            retval.setNum(value.toUInt());
            return retval;
        case QMetaType::ULongLong:
            retval.setNum(value.toULongLong());
            return retval;

        // Boolean
        case QMetaType::Bool:
            retval.setNum(value.toInt());  // boolean to integer
            return retval;

        // Floating-point:
        case QMetaType::Double:
            retval.setNum(value.toDouble());
            return retval;

        // String
        case QMetaType::QChar:
        case QMetaType::QString:
            return sqlQuoteString(escapeNewlines(value.toString()));
        case QMetaType::QStringList:
            return sqlQuoteString(qStringListToCsvString(value.toStringList())
            );

        // Dates, times
        case QMetaType::QDate:
            return QString(QStringLiteral("'%1'"))
                .arg(value.toDate().toString(QStringLiteral("yyyy-MM-dd")));
        case QMetaType::QDateTime:
            return QString(QStringLiteral("'%1'"))
                .arg(datetime::datetimeToIsoMs(value.toDateTime()));
        case QMetaType::QTime:
            return QString(QStringLiteral("'%1'"))
                .arg(value.toTime().toString(QStringLiteral("HH:mm:ss")));

        // BLOB types
        case QMetaType::QByteArray:
            // Base 64 is more efficient for network transmission than hex.
            return blobToQuotedBase64(value.toByteArray());

        // Other
        case QMetaType::UnknownType:
            errorfunc::fatalError(
                QStringLiteral("toSqlLiteral: Invalid field type")
            );
#ifdef COMPILER_WANTS_RETURN_AFTER_NORETURN
            // We'll never get here, but to stop compilers complaining:
            return NULL_STR;
#endif

        default:
            if (value.typeId() == customtypes::TYPE_ID_QVECTOR_INT) {
                QVector<int> intvec = qVariantToIntVector(value);
                return sqlQuoteString(numericVectorToCsvString(intvec));
            }
            errorfunc::fatalError(
                QStringLiteral("toSqlLiteral: Unknown user type")
            );
#ifdef COMPILER_WANTS_RETURN_AFTER_NORETURN
            // We'll never get here, but to stop compilers complaining:
            return NULL_STR;
#endif
    }
}

QVariant fromSqlLiteral(const QString& literal)
{
    if (literal.isEmpty()
        || literal.compare(NULL_STR, Qt::CaseInsensitive) == 0) {
        // NULL
        return QVariant();
    }

    const int n = literal.length();

    if (n >= 4 && literal.startsWith(QStringLiteral("64'"))
        && literal.endsWith(SQUOTE)) {
        // Base 64-encoded BLOB
        // Waste of time doing a more sophisticated (e.g. regex) check. If it
        // passes this test, it's *claiming* to be a base-64 BLOB, and we're
        // not going to decode it as anything else, even if it's duff.
        return quotedBase64ToBlob(literal);
    }

    if (n >= 3 && literal.startsWith(QStringLiteral("X'"))
        && literal.endsWith(SQUOTE)) {
        // Hex-encoded BLOB
        return quotedHexToBlob(literal);
    }

    if (n >= 2 && literal.startsWith(SQUOTE) && literal.endsWith(SQUOTE)) {
        // String, date, or time... we will let autoconversion take care of
        // dates/times given as sensible string literals.
        return unescapeNewlines(sqlDequoteString(literal));
    }

    // Numeric
    if (literal.contains(QStringLiteral("."))) {
        return literal.toDouble();
    }

    return literal.toInt();
}

QVector<QVariant> csvSqlLiteralsToValues(const QString& csv)
{
    // In: 34, NULL, 'a string''s test, with commas', X'0FB2AA', 64'c3VyZS4='
    // Out: split by commas, dealing with quotes appropriately
    QVector<QVariant> values;
    const int n = csv.length();
    bool in_quotes = false;
    int startpos = 0;
    int pos = 0;
    while (pos < n) {
        const QChar at_pos = csv.at(pos);
        if (!in_quotes) {
            if (at_pos == COMMA) {
                // end of chunk
                const QString chunk
                    = csv.mid(startpos, pos - startpos).trimmed();
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
    const QString chunk = csv.mid(startpos, n - startpos).trimmed();
    // ------------------------------------------------------------------------
    // More SQL literal processing here
    // ------------------------------------------------------------------------
    values.append(fromSqlLiteral(chunk));
    return values;
}

QString valuesToCsvSqlLiterals(const QVector<QVariant>& values)
{
    QStringList literals;
    literals.reserve(values.size());
    for (const QVariant& value : values) {
        literals.append(toSqlLiteral(value));
    }
    return literals.join(COMMA);
}

// ============================================================================
// C++ literals
// ============================================================================

const int BASE_OCTAL = 8;
const int OCTAL_NUM_DIGITS = 3;
const int BASE_HEX = 16;
const int HEX_NUM_DIGITS = 2;

#define ENCODE_LOW_VALUES_AS_HEX

QString stringToUnquotedCppLiteral(const QString& raw)
{
    // https://stackoverflow.com/questions/10220401
    QString escaped;
    for (QChar c : raw) {
        const ushort u = c.unicode();
        if (u == UNICODE_NL) {
            escaped += QStringLiteral(R"(\n)");
        } else if (u == UNICODE_CR) {
            escaped += QStringLiteral(R"(\r)");
        } else if (u == UNICODE_TAB) {
            escaped += QStringLiteral(R"(\t)");
        } else if (u == UNICODE_BACKSLASH) {
            escaped += QStringLiteral(R"(\\)");
        } else if (u == UNICODE_DQUOTE) {
            escaped += QStringLiteral(R"(\")");
        } else if (u < UNICODE_SPACE) {
#ifdef ENCODE_LOW_VALUES_AS_HEX
            const QString hex = QString(QStringLiteral("\\x%1"))
                                    .arg(u, HEX_NUM_DIGITS, BASE_HEX, ZERO);
            // ... number, fieldwidth (+ right align, - left align),
            //     base, fillchar
            escaped += hex;
#else
            const QString octal
                = QString(QStringLiteral("\\%1"))
                      .arg(u, OCTAL_NUM_DIGITS, BASE_OCTAL, ZERO);
            // ... number, fieldwidth (+ right align, - left align),
            //     base, fillchar
            escaped += octal;
#endif
        } else {
            escaped += c;
        }
    }
    return escaped;
}

QString stringToCppLiteral(const QString& raw)
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
    bool in_hex = false;
    for (QChar c : escaped) {
        ushort u = c.unicode();
        if (in_escape) {
            // Currently in escape sequence:

            if (in_octal) {
                bool ok = c.isDigit();
                if (ok) {
                    escape_digits.append(c);
                    // Octal numbers have a fixed number of digits.
                    if (escape_digits.length() >= OCTAL_NUM_DIGITS) {
                        ushort code = escape_digits.toUShort(&ok, BASE_OCTAL);
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
            } else if (in_hex) {
                bool ok = c.isDigit()
                    || (c.toUpper() >= 'A' && c.toUpper() <= 'F');
                if (ok) {
                    escape_digits += c;
                    if (escape_digits.length() >= HEX_NUM_DIGITS) {
                        ushort code = escape_digits.toUShort(&ok, BASE_HEX);
                        if (ok) {
                            raw += QChar(code);
                            in_escape = false;
                        }
                    }
                }
            } else if (c.isDigit()) {
                // An octal escape sequence is \nnn
                in_octal = true;
                escape_digits = c;
                // in_escape remains true
            } else if (c == 'x') {
                // A hex sequence is \xnn
                in_hex = true;
                escape_digits = QString();
            } else {
                // All the following are two-character escape sequences
                if (c == 'n') {
                    raw += NL;
                } else if (c == 'r') {
                    raw += CR;
                } else if (c == 't') {
                    raw += TAB;
                } else if (c == BACKSLASH) {
                    raw += BACKSLASH;
                } else if (c == DQUOTE) {
                    raw += DQUOTE;
                } else {
                    qWarning() << Q_FUNC_INFO << "Unknown escape code:" << c;
                }
                in_escape = false;
            }

        } else {
            // Not currently in escape sequence:

            if (u == UNICODE_BACKSLASH) {
                in_escape = true;
                in_octal = false;
                in_hex = false;
                escape_digits = QString();
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
    const int len = escaped.length();
    if (len >= 2 && escaped.at(0) == DQUOTE && escaped.at(len - 1) == DQUOTE) {
        // quoted string
        return unquotedCppLiteralToString(escaped.mid(1, len - 2));
    }
    return unquotedCppLiteralToString(escaped);
}

// ============================================================================
// Images
// ============================================================================

QByteArray imageToByteArray(const QImage& image, const char* format)
{
    // I thought passing a QImage to a QVariant-accepting function would lead
    // to autoconversion via
    //     https://doc.qt.io/qt-6.5/qimage.html#operator-QVariant
    // ... but it doesn't.
    // So: http://stackoverflow.com/questions/27343576
#ifdef DEBUG_IMAGE_CONVERSION_TIMES
    qDebug() << "imageToByteArray(): starting...";
#endif
    QByteArray arr;
    QBuffer buffer(&arr);
    buffer.open(QIODevice::WriteOnly);
    image.save(&buffer, format);
#ifdef DEBUG_IMAGE_CONVERSION_TIMES
    qDebug().nospace().noquote() << "imageToByteArray(): ... done ("
                                 << prettySize(buffer.size()) << ")";
#endif
    return arr;

    // This function is SLOW for large pictures.
    // Still, not hugely important, and fixes are complex (e.g. offloading it
    // to another thread +/- storing QImage objects in QVariant for database
    // storage and converting them to QByteArray etc. at the time of database
    // access).

    // This does not work:
    // QDataStream stream(&arr, QIODevice::WriteOnly);
    // stream << image;
}

QVariant imageToVariant(const QImage& image, const char* format)
{
    return QVariant(imageToByteArray(image, format));
}

QImage byteArrayToImage(
    const QByteArray& array, bool* successful, const char* format
)
{
    QImage image;
#ifdef DEBUG_IMAGE_CONVERSION_TIMES
    qDebug() << "byteArrayToImage(): starting...";
#endif
    const bool success = image.loadFromData(array, format);
    // When format is not specified, QImage tries to work it out from the data.
#ifdef DEBUG_IMAGE_CONVERSION_TIMES
    qDebug().nospace().noquote()
        << "byteArrayToImage(): ... done (" << prettySize(array.size()) << ")";
#endif
    if (!success) {
        qWarning() << Q_FUNC_INFO << "Failed to convert to image";
    }
    if (successful) {
        *successful = success;
    }
    return image;
}

int convertLengthByDpi(
    const int old_length, const qreal to_dpi, const qreal from_dpi
)
{
    // For example: 48 pixels (old_length) on a 96 dpi monitor (from_dpi)
    // should become 96 pixels on a 192-dpi screen
    if (qFuzzyCompare(to_dpi, from_dpi)) {
        return old_length;
    }
    return qRound(old_length * to_dpi / from_dpi);
}

int convertLengthByLogicalDpiX(const int old_length)
{
    return convertLengthByDpi(
        old_length, uiconst::g_logical_dpi.x, uiconst::DEFAULT_DPI.x
    );
}

int convertLengthByLogicalDpiY(const int old_length)
{
    return convertLengthByDpi(
        old_length, uiconst::g_logical_dpi.y, uiconst::DEFAULT_DPI.y
    );
}

QSize convertSizeByDpi(
    const QSize& old_size, const Dpi& to_dpi, const Dpi& from_dpi
)
{
    if (!old_size.isValid()) {
        return old_size;
    }
    return QSize(
        convertLengthByDpi(old_size.width(), to_dpi.x, from_dpi.x),
        convertLengthByDpi(old_size.height(), to_dpi.y, from_dpi.y)
    );
}

QSize convertSizeByLogicalDpi(const QSize& old_size)
{
    return convertSizeByDpi(
        old_size, uiconst::g_logical_dpi, uiconst::DEFAULT_DPI
    );
}

int convertCmToPx(const qreal cm, const qreal dpi)
{
    const qreal inches = cm / CM_PER_INCH;
    return qRound(dpi * inches);
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
    QString retval;
    retval.setNum(x, 'f', dp);
    return retval;
    // return QString("%1").arg(x, 0, 'f', dp);
}

QString
    prettyValue(const QVariant& variant, const int dp, const QMetaType type)
{
    const int type_id = type.id();

    if (variant.isNull()) {
        return NULL_STR;
    }
    switch (type_id) {
        case QMetaType::QByteArray:
            return QStringLiteral("<binary>");
        case QMetaType::QDate:
            return datetime::dateToIso(variant.toDate());
        case QMetaType::QDateTime:
            return datetime::datetimeToIsoMs(variant.toDateTime());
        case QMetaType::Double:
            if (dp < 0) {
                return variant.toString();
            }
            return toDp(variant.toDouble(), dp);
        case QMetaType::QString: {
            QString escaped = variant.toString().toHtmlEscaped();
            stringfunc::toHtmlLinebreaks(escaped, false);
            return escaped;
        }
        case QMetaType::QStringList: {
            QStringList raw = variant.toStringList();
            QStringList escaped;
            escaped.reserve(raw.size());
            for (const QString& r : raw) {
                QString e = r.toHtmlEscaped();
                stringfunc::toHtmlLinebreaks(e, false);
                escaped.append(e);
            }
            return escaped.join(QStringLiteral(","));
        }
        default:
            if (type_id > QMetaType::User) {
                if (type_id == customtypes::TYPE_ID_QVECTOR_INT) {
                    QVector<int> intvec = qVariantToIntVector(variant);
                    return numericVectorToCsvString(intvec);
                }
                errorfunc::fatalError("prettyValue: Unknown user type");
            }

            return variant.toString();
    }
}

QString prettyValue(const QVariant& variant, const int dp)
{
    return prettyValue(variant, dp, variant.metaType());
}

const QStringList PREFIXES_SHORT_BINARY{
    "", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi", "Yi"};
const QStringList PREFIXES_LONG_BINARY{
    "", "kibi", "mebi", "gibi", "tebi", "peti", "exbi", "zebi", "yobi"};
const QStringList PREFIXES_SHORT_DECIMAL{
    "", "k", "M", "G", "T", "P", "E", "Z", "Y"};
const QStringList PREFIXES_LONG_DECIMAL{
    "", "kilo", "mega", "giga", "tera", "peta", "exa", "zetta", "yotta"};

QString prettySize(
    const double num,
    const bool space,
    const bool binary,
    const bool longform,
    const QString& suffix
)
{
    // http://stackoverflow.com/questions/3758606/how-to-convert-byte-size-into-human-readable-format-in-java
    const QStringList& prefixes = binary
        ? (longform ? PREFIXES_LONG_BINARY : PREFIXES_SHORT_BINARY)
        : (longform ? PREFIXES_LONG_DECIMAL : PREFIXES_SHORT_DECIMAL);
    const QString optional_space
        = space ? QStringLiteral(" ") : QStringLiteral("");
    const double base = binary ? 1024 : 1000;
    auto exponent = static_cast<int>(qLn(num) / qLn(base));
    exponent = qBound(0, exponent, prefixes.length() - 1);
    const QString& prefix = prefixes.at(exponent);
    const double converted_num = num / pow(base, exponent);
    const int precision = (exponent == 0) ? 0 : 1;  // decimals, for 'f'
    return QString(QStringLiteral("%1%2%3%4"))
        .arg(converted_num, 0, 'f', precision)
        .arg(optional_space, prefix, suffix);
}

QString prettyPointer(const void* pointer)
{
    // http://stackoverflow.com/questions/8881923/how-to-convert-a-pointer-value-to-qstring
    return QString(QStringLiteral("0x%1"))
        .arg(
            reinterpret_cast<quintptr>(pointer),
            QT_POINTER_SIZE * 2,
            16,
            QChar('0')
        );
}

// ============================================================================
// Networking
// ============================================================================

QMap<QString, QString> getReplyDict(const QByteArray& data)
{
    // For server replies looking like key1:value1\nkey2:value2 ...
    const QList<QByteArray> lines = data.split('\n');
    QMap<QString, QString> dict;
    for (const QByteArray& line : lines) {
        const QRegularExpressionMatch match = RECORD_RE.match(line);
        if (match.hasMatch()) {
            const QString key = match.captured(1);
            const QString value = match.captured(2);
            dict[key] = value;
        }
    }
    return dict;
}

QString getReplyString(const QByteArray& data)
{
    return QString::fromUtf8(data);
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
        postdata.addQueryItem(
            QUrl::toPercentEncoding(it.key()),
            QUrl::toPercentEncoding(it.value())
        );
    }
    return postdata;
}

// https://doc.qt.io/qt-6/qssl.html#SslProtocol-enum
const QString SSLPROTODESC_TLSV1_2 = QStringLiteral("TlsV1_2");
const QString SSLPROTODESC_TLSV1_2_OR_LATER = QStringLiteral("TlsV1_2OrLater");
const QString SSLPROTODESC_DTLSV1_2 = QStringLiteral("DtlsV1_2");
const QString SSLPROTODESC_DTLSV1_2_OR_LATER
    = QStringLiteral("DtlsV1_2OrLater");
const QString SSLPROTODESC_TLSV1_3 = QStringLiteral("TlsV1_3");
const QString SSLPROTODESC_TLSV1_3_OR_LATER = QStringLiteral("TlsV1_3OrLater");
const QString SSLPROTODESC_ANYPROTOCOL = QStringLiteral("AnyProtocol");
const QString SSLPROTODESC_SECUREPROTOCOLS = QStringLiteral("SecureProtocols");
const QString SSLPROTODESC_UNKNOWN_PROTOCOL
    = QStringLiteral("UnknownProtocol");

QString describeSslProtocol(const QSsl::SslProtocol protocol)
{
    using namespace QSsl;
    switch (protocol) {
        case TlsV1_2:
            return SSLPROTODESC_TLSV1_2;
        case TlsV1_2OrLater:
            return SSLPROTODESC_TLSV1_2_OR_LATER;
        case DtlsV1_2:
            return SSLPROTODESC_DTLSV1_2;
        case DtlsV1_2OrLater:
            return SSLPROTODESC_DTLSV1_2_OR_LATER;
        case TlsV1_3:
            return SSLPROTODESC_TLSV1_3;
        case TlsV1_3OrLater:
            return SSLPROTODESC_TLSV1_3_OR_LATER;
        case AnyProtocol:
            return SSLPROTODESC_ANYPROTOCOL;
        case SecureProtocols:
            return SSLPROTODESC_SECUREPROTOCOLS;
        default:
        case UnknownProtocol:
            return SSLPROTODESC_UNKNOWN_PROTOCOL;
    }
}

QSsl::SslProtocol sslProtocolFromDescription(const QString& desc)
{
    using namespace QSsl;
    if (desc == SSLPROTODESC_TLSV1_2) {
        return TlsV1_2;
    }
    if (desc == SSLPROTODESC_TLSV1_2_OR_LATER) {
        return TlsV1_2OrLater;
    }
    if (desc == SSLPROTODESC_DTLSV1_2) {
        return DtlsV1_2;
    }
    if (desc == SSLPROTODESC_DTLSV1_2_OR_LATER) {
        return DtlsV1_2OrLater;
    }
    if (desc == SSLPROTODESC_TLSV1_3) {
        return TlsV1_3;
    }
    if (desc == SSLPROTODESC_TLSV1_3_OR_LATER) {
        return TlsV1_3OrLater;
    }
    if (desc == SSLPROTODESC_ANYPROTOCOL) {
        return AnyProtocol;
    }
    if (desc == SSLPROTODESC_SECUREPROTOCOLS) {
        return SecureProtocols;
    }
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
    const QString str = v.toString();
    if (str.isEmpty()) {
        return QVariant();
    }
    return str.at(0);
}

// ============================================================================
// Specific vectors as strings
// ============================================================================

QVector<int> csvStringToIntVector(const QString& str)
{
    QVector<int> vec;
    if (str.isEmpty()) {
        return vec;
    }
    const QStringList strings = str.split(COMMA);
    vec.reserve(strings.size());
    for (const QString& s : strings) {
        vec.append(s.toInt());
        // https://doc.qt.io/qt-6/qstring.html#toInt
        // toInt() ignores leading/trailing whitespace, and returns 0 if the
        // conversion fails.
    }
    return vec;
}

QString qStringListToCsvString(const QStringList& vec)
{
    QStringList words;
    words.reserve(vec.size());
    for (const QString& word : vec) {
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
    for (const QChar& c : str) {
        const ushort u = c.unicode();
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
                    // ... trims off start/end whitespace
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

QVector<int> qVariantToIntVector(const QVariant& v)
{
    // We're adding support for QVector<int>.
    // - http://stackoverflow.com/questions/6177906/is-there-a-reason-why-qvariant-accepts-only-qlist-and-not-qvector-nor-qlinkedlis
    // - https://doc.qt.io/qt-6.5/qvariant.html
    // - https://doc.qt.io/qt-6.5/qmetatype.html
    return v.value<QVector<int>>();
}

// ============================================================================
// JSON
// ============================================================================

QString stringListToJson(const QStringList& list, const bool compact)
{
    const QJsonArray ja(QJsonArray::fromStringList(list));
    const QJsonDocument jd(ja);
    return jd.toJson(
        compact ? QJsonDocument::Compact : QJsonDocument::Indented
    );
}

// ============================================================================
// Physical units
// ============================================================================

#ifdef DEBUG_UNIT_CONVERSION
    #define UNIT_CONVERSION "Unit conversion: "
#endif

const double CM_PER_INCH = 2.54;  // exactly
const int CM_PER_M = 100;
const int INCHES_PER_FOOT = 12;

const int POUNDS_PER_STONE = 14;
const int OUNCES_PER_POUND = 16;
const int GRAMS_PER_KG = 1000;
// International pounds:
// - https://en.wikipedia.org/wiki/Pound_(mass)#Relationship_to_the_kilogram
const double GRAMS_PER_POUND = 453.59237;  // Weights and Measures Act 1963
const double KG_PER_POUND = GRAMS_PER_POUND / GRAMS_PER_KG;
const double GRAMS_PER_STONE = GRAMS_PER_POUND * POUNDS_PER_STONE;
const double KG_PER_STONE = GRAMS_PER_STONE / GRAMS_PER_KG;
const double GRAMS_PER_OUNCE = GRAMS_PER_POUND / OUNCES_PER_POUND;
const double KG_PER_OUNCE = GRAMS_PER_OUNCE / GRAMS_PER_KG;
const double POUNDS_PER_KG = GRAMS_PER_KG / GRAMS_PER_POUND;

double metresFromFeetInches(const double feet, const double inches)
{
    const double metres
        = (feet * INCHES_PER_FOOT + inches) * CM_PER_INCH / CM_PER_M;
#ifdef DEBUG_UNIT_CONVERSION
    qDebug() << UNIT_CONVERSION << feet << "ft" << inches << "in ->" << metres
             << "m";
#endif
    return metres;
}

void feetInchesFromMetres(const double metres, int& feet, double& inches)
{
    const double total_inches = metres * CM_PER_M / CM_PER_INCH;
    feet = static_cast<int>(mathfunc::trunc(total_inches / INCHES_PER_FOOT));
    inches = std::fmod(total_inches, INCHES_PER_FOOT);
#ifdef DEBUG_UNIT_CONVERSION
    qDebug() << UNIT_CONVERSION << metres << "m ->" << feet << "ft" << inches
             << "in";
#endif
}

double centimetresFromInches(const double inches)
{
    return inches * CM_PER_INCH;
}

double inchesFromCentimetres(const double centimetres)
{
    return centimetres / CM_PER_INCH;
}

double kilogramsFromStonesPoundsOunces(
    double stones, double pounds, double ounces
)
{
    const QVector<double> kg_parts{
        stones * KG_PER_STONE,
        pounds * KG_PER_POUND,
        ounces * KG_PER_OUNCE,
    };
    const double kg = mathfunc::kahanSum(kg_parts);
#ifdef DEBUG_UNIT_CONVERSION
    qDebug() << UNIT_CONVERSION << stones << "st" << pounds << "lb" << ounces
             << "oz ->" << kg << "kg";
#endif
    return kg;
}

void stonesPoundsFromKilograms(
    const double kilograms, int& stones, double& pounds
)
{
    const double total_pounds = kilograms * POUNDS_PER_KG;
    stones
        = static_cast<int>(mathfunc::trunc(total_pounds / POUNDS_PER_STONE));
    pounds = std::fmod(total_pounds, POUNDS_PER_STONE);
#ifdef DEBUG_UNIT_CONVERSION
    qDebug() << UNIT_CONVERSION << kilograms << "kg ->" << stones << "st"
             << pounds << "lb";
#endif
}

void stonesPoundsOuncesFromKilograms(
    const double kilograms, int& stones, int& pounds, double& ounces
)
{
    const double total_pounds = kilograms * POUNDS_PER_KG;
    stones
        = static_cast<int>(mathfunc::trunc(total_pounds / POUNDS_PER_STONE));
    const double float_pounds = std::fmod(total_pounds, POUNDS_PER_STONE);
    pounds = static_cast<int>(mathfunc::trunc(float_pounds));
    ounces = (float_pounds - pounds) * OUNCES_PER_POUND;
#ifdef DEBUG_UNIT_CONVERSION
    qDebug() << UNIT_CONVERSION << kilograms << "kg ->" << stones << "st"
             << pounds << "lb" << ounces << "oz";
#endif
}

int msFromMin(const qreal minutes)
{
    return qRound(minutes * 60000);
}

int msFromSec(const qreal seconds)
{
    return qRound(seconds * 1000);
}

// ============================================================================
// Tests
// ============================================================================

// Specialization for double.
// Template specializations are declared in .h files but defined in .cpp files.
// https://stackoverflow.com/questions/4445654

template<> void assert_eq(const double& a, const double& b)
{
    FloatingPoint<double> fa(a);
    FloatingPoint<double> fb(b);
    if (fa.AlmostEquals(fb)) {
        qDebug() << "Conversion success:" << a << "==" << b;
    } else {
        qCritical() << "Conversion failure:" << a << "!=" << b;
        Q_ASSERT(false);
        qFatal("Stopping");
    }
}

void testConversions()
{
    qDebug() << "Testing conversions...";

    const QStringList stringlist{"a", "b", "c1\nc2"};
    const QString stringlist_as_str(QStringLiteral(R"("a","b","c1\nc2")"));
    QString test_string;
    for (int i = 0; i < 1000; ++i) {
        QChar c(i);
        test_string += c;
    }
    const QVariant test_string_var(test_string);
    const QByteArray blob(test_string.toUtf8());
    const QVector<QVariant> varvec{
        test_string_var, QVariant(), QVariant(5), QVariant(7.26)};
    const double kilograms = 35;
    const double metres = 1.82;

    assert_eq(test_string, unescapeNewlines(escapeNewlines(test_string)));

    assert_eq(test_string, sqlDequoteString(sqlQuoteString(test_string)));

    assert_eq(blob, quotedBase64ToBlob(blobToQuotedBase64(blob)));
    assert_eq(blob, quotedHexToBlob(blobToQuotedHex(blob)));

    assert_eq(test_string_var, fromSqlLiteral(toSqlLiteral(test_string_var)));
    assert_eq(varvec, csvSqlLiteralsToValues(valuesToCsvSqlLiterals(varvec)));

    assert_eq(
        test_string, cppLiteralToString(stringToCppLiteral(test_string))
    );

    assert_eq(qStringListToCsvString(stringlist), stringlist_as_str);
    assert_eq(csvStringToQStringList(stringlist_as_str), stringlist);

    int feet = 0;
    double inches = 0;
    feetInchesFromMetres(metres, feet, inches);
    assert_eq(metres, metresFromFeetInches(feet, inches));

    int stones = 0;
    double double_pounds = 0;  // for st, lb
    int int_pounds = 0;  // for st, lb, oz
    double ounces = 0;
    stonesPoundsFromKilograms(kilograms, stones, double_pounds);
    assert_eq(
        kilograms, kilogramsFromStonesPoundsOunces(stones, double_pounds)
    );
    stonesPoundsOuncesFromKilograms(kilograms, stones, int_pounds, ounces);
    assert_eq(
        kilograms, kilogramsFromStonesPoundsOunces(stones, int_pounds, ounces)
    );

    qDebug() << "... all conversions correct.";
}


}  // namespace convert
