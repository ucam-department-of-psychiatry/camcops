#include "filefunc.h"
#include <QDebug>
#include <QFile>
#include <QTextStream>


QString textfileContents(const QString& filename)
{
    QFile file(filename);
    if (!file.open(QFile::ReadOnly | QFile::Text)) {
        qDebug() << "FAILED TO OPEN FILE:" << filename;
        return "";
    } else {
#ifdef DEBUG_READ_FILE
        qDebug() << "Reading file:" << filename;
#endif
    }
    QTextStream in(&file);
    in.setCodec("UTF-8");
    QString text = in.readAll();
    // qDebug() << text;
    return text;
}
