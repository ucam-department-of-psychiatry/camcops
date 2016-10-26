#pragma once
// As per http://doc.qt.io/qt-5/qtwidgets-layouts-flowlayout-example.html


/*===========================================================================
==
== Copyright (C) 2016 The Qt Company Ltd.
== Contact: https://www.qt.io/licensing/
==
== This file is part of the examples of the Qt Toolkit.
==
== $QT_BEGIN_LICENSE:BSD$
== Commercial License Usage
== Licensees holding valid commercial Qt licenses may use this file in
== accordance with the commercial license agreement provided with the
== Software or, alternatively, in accordance with the terms contained in
== a written agreement between you and The Qt Company. For licensing terms
== and conditions see https://www.qt.io/terms-conditions. For further
== information use the contact form at https://www.qt.io/contact-us.
==
== BSD License Usage
== Alternatively, you may use this file under the terms of the BSD license
== as follows:
==
== "Redistribution and use in source and binary forms, with or without
== modification, are permitted provided that the following conditions are
== met:
==   * Redistributions of source code must retain the above copyright
==     notice, this list of conditions and the following disclaimer.
==   * Redistributions in binary form must reproduce the above copyright
==     notice, this list of conditions and the following disclaimer in
==     the documentation and/or other materials provided with the
==     distribution.
==   * Neither the name of The Qt Company Ltd nor the names of its
==     contributors may be used to endorse or promote products derived
==     from this software without specific prior written permission.
==
==
== THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
== "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
== LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
== A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
== OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
== SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
== LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
== DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
== THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
== (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
== OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
==
== $QT_END_LICENSE$
==
===========================================================================*/

#include <QLayout>
#include <QMap>  // RNC
#include <QRect>
#include <QStyle>

class FlowLayout : public QLayout
{
    // Flow layout, as per Qt demo.
    Q_OBJECT  // RNC
public:
    explicit FlowLayout(QWidget* parent, int margin = -1,
                        int h_spacing = -1, int v_spacing = -1);
    explicit FlowLayout(int margin = -1,
                        int h_spacing = -1, int v_spacing = -1);
    ~FlowLayout();

    virtual void addItem(QLayoutItem* item) override;
    virtual int horizontalSpacing() const;
    virtual int verticalSpacing() const;
    virtual Qt::Orientations expandingDirections() const override;
    virtual bool hasHeightForWidth() const override;
    virtual int heightForWidth(int) const override;
    virtual int count() const override;
    virtual QLayoutItem* itemAt(int index) const override;
    virtual QSize minimumSize() const override;
    virtual void setGeometry(const QRect& rect) override;
    virtual QSize sizeHint() const override;
    virtual QLayoutItem* takeAt(int index) override;
    virtual void invalidate() override;  // RNC

protected:  // RNC (was private)
    void commonConstructor(int margin);  // RNC
    virtual QSize doLayout(const QRect& rect, bool test_only) const;
    int smartSpacing(QStyle::PixelMetric pm) const;

    QList<QLayoutItem*> m_item_list;
    int m_h_space;
    int m_v_space;
    mutable QSize m_size_hint;
    mutable QMap<int, int> m_width_to_height;
};
