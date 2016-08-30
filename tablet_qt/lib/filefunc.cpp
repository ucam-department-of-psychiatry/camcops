// #define DEBUG_READ_FILE
// #define DEBUG_READ_FILE_CONTENTS

#include "filefunc.h"
#include <QDebug>
#include <QFile>
#include <QString>
#include <QTextStream>


bool FileFunc::fileExists(const QString& filename)
{
    QFile file(filename);
    if (!file.open(QFile::ReadOnly | QFile::Text)) {
        return false;
    }
    return true;
}


QString FileFunc::textfileContents(const QString& filename)
{
    QFile file(filename);
    if (!file.open(QFile::ReadOnly | QFile::Text)) {
        qCritical() << Q_FUNC_INFO << "FAILED TO OPEN FILE:" << filename;
        return "";
    } else {
#ifdef DEBUG_READ_FILE
        qDebug() << "Reading file:" << filename;
#endif
    }
    QTextStream in(&file);
    in.setCodec("UTF-8");
    QString text = in.readAll();
#ifdef DEBUG_READ_FILE_CONTENTS
    qDebug() << text;
#endif
    return text;
}


QString FileFunc::taskHtmlFilename(const QString& stem)
{
    return QString(":/taskinfo/%1.html").arg(stem);
}
