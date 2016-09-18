#pragma once
#include <QByteArray>
#include "lib/databaseobject.h"


class Blob : public DatabaseObject
{
public:
    Blob(const QSqlDatabase& db,
         const QString& src_table = "",  // defaults for specimen construction
         int src_pk = -1,
         const QString& src_field = "");
    virtual ~Blob();
    bool setBlob(const QVariant& value, bool save_to_db = true,
                 const QString& extension_without_dot = "png");
    QVariant blobVariant() const;
    QByteArray blobByteArray() const;
protected:
    QString m_filename_stem;
};
