#pragma once
#include <QList>
#include <QString>

class QByteArray;
class QImage;
class QVariant;


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

    // Images
    QByteArray imageToByteArray(const QImage& image,
                                const char* format = "png");
    QVariant imageToVariant(const QImage& image, const char* format = "png");
    QImage byteArrayToImage(const QByteArray& array,
                            const char* format = nullptr);
}
