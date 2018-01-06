/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

#pragma once
#include <QByteArray>
#include <QImage>
#include "db/databaseobject.h"


class Blob : public DatabaseObject
{
public:
    Blob(CamcopsApp& app,
         DatabaseManager& db,
         const QString& src_table = "",  // defaults for specimen construction
         int src_pk = -1,
         const QString& src_field = "");
    virtual ~Blob();

    bool setBlob(const QVariant& value,
                 bool save_to_db = true,
                 const QString& extension_without_dot = "png",
                 const QString& mimetype = "image/png");  // returns: changed?
    QVariant blobVariant() const;
    QByteArray blobByteArray() const;

    // Handling BLOBs as images:
    QImage image(bool* p_loaded) const;
    void rotateImage(int angle_degrees_clockwise, bool save_to_db);
    bool setImage(const QImage& image, bool save_to_db);  // returns: changed?
    bool setRawImage(const QByteArray& data,
                     bool save_to_db,
                     const QString& extension_without_dot,
                     const QString& mimetype);  // returns: changed?

    // Classmethod:
    void makeIndexes();

protected:
    void rotateCachedImage(int angle_degrees_clockwise) const;

public:
    static const QString TABLENAME;
    static const QString SRC_TABLE_FIELDNAME;
    static const QString SRC_PK_FIELDNAME;
protected:
    QString m_filename_stem;
    mutable QImage m_image;  // cached image, as conversion to/from byte array is slow
    mutable bool m_image_loaded_from_data;
};
