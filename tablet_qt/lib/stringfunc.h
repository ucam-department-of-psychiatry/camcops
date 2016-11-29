#pragma once
#include <QStringList>


namespace StringFunc
{
    // ========================================================================
    // Make sequences of strings
    // ========================================================================

    QStringList strseq(const QString& prefix, int first, int last);
    // Example: stringSequence("q", 1, 3) -> {"q1", "q2", "q3"}

    QStringList strseq(const QString& prefix, int first, int last,
                       const QString& suffix);
    QStringList strseq(const QString& prefix, int first, int last,
                       const QStringList& suffixes);

    QStringList strseq(const QStringList& prefixes, int first, int last);
    QStringList strseq(const QStringList& prefixes, int first, int last,
                       const QStringList& suffixes);

    // ========================================================================
    // Other string formatting
    // ========================================================================

    QString strnum(const QString& prefix, int num);

    // ========================================================================
    // HTML processing
    // ========================================================================

    QString bold(const QString& str);
    QString joinHtmlLines(const QStringList& lines);
}
