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

#pragma once
#include <QPushButton>
class LabelWordWrapWide;
class QVBoxLayout;


class ClickableLabelWordWrapWide : public QPushButton
{
    Q_OBJECT
public:
    ClickableLabelWordWrapWide(const QString& text, bool stretch = false,
                               QWidget* parent = nullptr);
    ClickableLabelWordWrapWide(bool stretch = false,
                               QWidget* parent = nullptr);

    virtual void setTextFormat(Qt::TextFormat format);
    virtual void setWordWrap(bool on);
    virtual void setAlignment(Qt::Alignment alignment);
    virtual void setOpenExternalLinks(bool open);
    virtual void setText(const QString& text);

    virtual QSize sizeHint() const override;
    virtual QSize minimumSizeHint() const override;
    virtual void resizeEvent(QResizeEvent* event) override;
protected:
    void commonConstructor(bool stretch);
    QSize translateSize(const QSize& size) const;

protected:
    LabelWordWrapWide* m_label;
    QVBoxLayout* m_layout;
};
