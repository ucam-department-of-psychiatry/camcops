#include "stringfunc.h"


QStringList StringFunc::strseq(const QString& prefix, int first, int last)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    QString format = "%1%2";
    for (int i = first; i <= last; ++i) {
        list.append(format.arg(prefix).arg(i));
    }
    return list;
}


QStringList StringFunc::strseq(const QString& prefix, int first, int last,
                               const QStringList& suffixes)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    QString format = "%1%2%3";
    for (int i = first; i <= last; ++i) {
        for (auto suffix : suffixes) {
            list.append(format.arg(prefix).arg(i).arg(suffix));
        }
    }
    return list;
}


QStringList StringFunc::strseq(const QString& prefix, int first, int last,
                               const QString& suffix)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    QString format = "%1%2%3";
    for (int i = first; i <= last; ++i) {
        list.append(format.arg(prefix).arg(i).arg(suffix));
    }
    return list;
}


QStringList StringFunc::strseq(const QStringList& prefixes, int first,
                               int last)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    QString format = "%1%2";
    for (auto prefix : prefixes) {
        for (int i = first; i <= last; ++i) {
            list.append(format.arg(prefix).arg(i));
        }
    }
    return list;
}


QStringList StringFunc::strseq(const QStringList& prefixes, int first,
                               int last, const QStringList& suffixes)
{
    Q_ASSERT(first >= 0 && last >= 0 && first <= last);
    QStringList list;
    QString format = "%1%2%3";
    for (auto prefix : prefixes) {
        for (int i = first; i <= last; ++i) {
            for (auto suffix : suffixes) {
                list.append(format.arg(prefix).arg(i).arg(suffix));
            }
        }
    }
    return list;
}
