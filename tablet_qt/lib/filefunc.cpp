#include "filefunc.h"
#include <QDebug>
#include <QFile>
#include <QTextStream>


QString get_textfile_contents(const QString& filename)
{
    QFile file(filename);
    if (!file.open(QFile::ReadOnly | QFile::Text)) {
        qDebug() << "FAILED TO OPEN FILE:" << filename;
        return "";
    } else {
        qDebug() << "Reading file:" << filename;
    }
    QTextStream in(&file);
    in.setCodec("UTF-8");
    QString text = in.readAll();
    // qDebug() << text;
    return text;
}
