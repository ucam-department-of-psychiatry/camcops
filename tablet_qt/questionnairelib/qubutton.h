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
#include <functional>
#include <QMap>
#include <QString>
#include <QVariant>
#include "questionnairelib/quelement.h"


class QuButton : public QuElement
{
    // Element to offer a button (calling a callback function).

    Q_OBJECT
public:
    using Args = QMap<QString, QVariant>;
    using CallbackFunction = std::function<void()>;
    // To pass other arguments, use std::bind to bind them before passing here

    QuButton(const QString& label, const CallbackFunction& callback);
    QuButton(const QString& icon_filename, bool filename_is_camcops_stem,
             bool alter_unpressed_image, const CallbackFunction& callback);
    QuButton* setActive(bool active);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
protected slots:
    void clicked();
protected:
    QString m_label;
    QString m_icon_filename;
    bool m_filename_is_camcops_stem;
    bool m_alter_unpressed_image;
    CallbackFunction m_callback;
    bool m_active;
};
