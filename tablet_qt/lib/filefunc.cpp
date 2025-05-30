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

// #define DEBUG_READ_FILE
// #define DEBUG_READ_FILE_CONTENTS

#include "filefunc.h"

#include <QDebug>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QString>
#include <QTextStream>

#include "lib/errorfunc.h"

namespace filefunc {


bool fileExists(const QString& filename)
{
    // http://stackoverflow.com/questions/10273816/how-to-check-whether-file-exists-in-qt-in-c
    const QFileInfo check_file(filename);
    return check_file.exists() && check_file.isFile();
}

QString textfileContents(const QString& filename)
{
    QFile file(filename);
    if (!file.open(QFile::ReadOnly | QFile::Text)) {
        qCritical() << Q_FUNC_INFO << "FAILED TO OPEN FILE:" << filename;
        return "";
    }
#ifdef DEBUG_READ_FILE
    qDebug() << "Reading file:" << filename;
#endif
    QTextStream in(&file);
    in.setEncoding(QStringConverter::Utf8);
    const QString text = in.readAll();
#ifdef DEBUG_READ_FILE_CONTENTS
    qDebug() << text;
#endif
    return text;
}

/*
QString taskHtmlFilename(const QString& stem)
{
    return QString(":/taskinfo/%1.html").arg(stem);
}
*/


bool deleteFile(const QString& filename)
{
    QFile file(filename);
    return file.remove();
}

bool renameFile(const QString& from, const QString& to)
{
    QFile file(from);
    return file.rename(to);
}

bool ensureDirectoryExists(const QString& dir)
{
    if (!QDir(dir).exists()) {
        if (QDir().mkpath(dir)) {
            qDebug() << "Made directory:" << dir;
        } else {
            qDebug() << "Failed to make directory:" << dir;
            return false;
        }
    }
    return true;
}

void ensureDirectoryExistsOrDie(const QString& dir)
{
    if (!ensureDirectoryExists(dir)) {
        errorfunc::fatalError(QObject::tr("Failed to make directory: ") + dir);
    }
}

bool fileContainsLine(const QString& filename, const QString& line)
{
    // https://doc.qt.io/qt-6.5/qfile.html
    // https://doc.qt.io/qt-6.5/qtextstream.html
    QFile file(filename);
    if (!file.open(QFile::ReadOnly | QFile::Text)) {
        qCritical() << Q_FUNC_INFO << "FAILED TO OPEN FILE:" << filename;
        return false;
    }
    QTextStream in(&file);
    while (!in.atEnd()) {
        const QString file_line = in.readLine();  // strips newlines
        if (line == file_line) {
            return true;
        }
    }
    return false;
}


}  // namespace filefunc
