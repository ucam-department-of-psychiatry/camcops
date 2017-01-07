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

// #define DEBUG_READ_FILE
// #define DEBUG_READ_FILE_CONTENTS

#include "filefunc.h"
#include <QDebug>
#include <QFile>
#include <QString>
#include <QTextStream>


bool filefunc::fileExists(const QString& filename)
{
    QFile file(filename);
    if (!file.open(QFile::ReadOnly | QFile::Text)) {
        return false;
    }
    return true;
}


QString filefunc::textfileContents(const QString& filename)
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


QString filefunc::taskHtmlFilename(const QString& stem)
{
    return QString(":/taskinfo/%1.html").arg(stem);
}
