/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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

#include "blobfieldref.h"
#include "dbobjects/blob.h"


BlobFieldRef::BlobFieldRef(DatabaseObject* p_dbobject, const QString& fieldname,
                           bool mandatory, CamcopsApp* p_app) :
    FieldRef(p_dbobject, fieldname, mandatory,
             true,  // autosave
             true,  // blob
             p_app)
{
    Q_ASSERT(m_blob);
}


BlobFieldRef::BlobFieldRef(QSharedPointer<Blob> blob, bool mandatory) :
    FieldRef(blob, mandatory)
{
    Q_ASSERT(m_blob);
}


QImage BlobFieldRef::blobImage(bool* p_loaded) const
{
    return m_blob->image(p_loaded);
}


void BlobFieldRef::blobRotateImage(int angle_degrees_clockwise,
                                   const QObject* originator)
{
    m_blob->rotateImage(angle_degrees_clockwise, true);
    signalSetValue(true, originator);
}


bool BlobFieldRef::blobSetImage(const QImage& image, const QObject* originator)
{
    bool changed = m_blob->setImage(image, true);
    return signalSetValue(changed, originator);
}


bool BlobFieldRef::blobSetRawImage(const QByteArray& data,
                                   const QString& extension_without_dot,
                                   const QString& mimetype,
                                   const QObject* originator)
{
    bool changed = m_blob->setRawImage(data, true,
                                       extension_without_dot, mimetype);
    return signalSetValue(changed, originator);
}
