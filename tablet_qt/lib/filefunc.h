#pragma once
#include <QString>

bool fileExists(const QString& filename);
QString textfileContents(const QString& filename);
QString taskHtmlFilename(const QString& stem);
