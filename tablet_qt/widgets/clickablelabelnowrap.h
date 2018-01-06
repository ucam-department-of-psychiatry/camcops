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

#include <QPointer>
#include <QPushButton>
class QLabel;
class QPixmap;
class QVBoxLayout;


class ClickableLabelNoWrap : public QPushButton
{
    // Label that responds to clicks.
    // - Multiple inheritance doesn't play nicely with QObject.
    //   http://doc.qt.io/qt-5.7/moc.html#multiple-inheritance-requires-qobject-to-be-first
    // - So, could inherit from QAbstractButton and implement QLabel functions.
    //   However, QLabel has some complex code for word-wrapping.
    // - Or the reverse: inherit from QLabel and implement
    //   QAbstractButton::mousePressEvent functionality (and all associated
    //   code). But even that is relatively fancy.
    // - Or use an event monitor: label with a monitor attached, e.g.
    //   http://stackoverflow.com/questions/32018941/qt-qlabel-click-event
    // - Or use ownership: label that contains a button, or button that
    //   contains a label.
    //   http://stackoverflow.com/questions/8960233
    // - Probably best: don't try to be all things to all people; have
    //      QLabel
    //          LabelWordWrapWide
    //      QPushButton
    //          ClickableLabelNoWrap (owning QLabel)
    //          ClickableLabelWordWrapWide (owning LabelWordWrapWide)
    //          [... can't have one of those sensibly derive from the other,
    //               as you get into a base-class/derived-class initialization
    //               order problem]

    Q_OBJECT
public:
    ClickableLabelNoWrap(const QString& text, QWidget* parent = nullptr);
    ClickableLabelNoWrap(QWidget* parent = nullptr);

    virtual void setTextFormat(Qt::TextFormat format);
    virtual void setWordWrap(bool on);
    virtual void setAlignment(Qt::Alignment alignment);
    virtual void setOpenExternalLinks(bool open);
    virtual void setPixmap(const QPixmap& pixmap);

    virtual QSize sizeHint() const override;
protected:
    void commonConstructor();

protected:
    QLabel* m_label;
    QVBoxLayout* m_layout;
};
