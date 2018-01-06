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
#include <initializer_list>
#include <QList>
#include <QObject>
#include <QPointer>
#include <QSharedPointer>
#include "common/aliases_camcops.h"
#include "questionnairelib/quelement.h"

class QWidget;
class Questionnaire;


class QuPage : public QObject
{
    // Encapsulates a display page of QuElement objects.
    // A Questionnaire includes one or more QuPage objects.

    Q_OBJECT
    friend class Questionnaire;
public:
    enum class PageType {
        Inherit,  // from the Questionnaire
        Patient,
        Clinician,
        ClinicianWithPatient,
        Config,
    };
public:
    QuPage();
    QuPage(const QVector<QuElementPtr>& elements);
    QuPage(std::initializer_list<QuElementPtr> elements);
    QuPage(const QVector<QuElement*>& elements);  // takes ownership
    QuPage(std::initializer_list<QuElement*> elements);  // takes ownership
    virtual ~QuPage();

    virtual void build() {}  // for on-the-fly building

    QuPage* setType(PageType type);
    QuPage* setTitle(const QString& title);
    QuPage* addElement(const QuElementPtr& element);
    QuPage* addElement(QuElement* element);  // takes ownership
    QuPage* addElements(const QVector<QuElementPtr>& elements);
    QuPage* addElements(const QVector<QuElement*>& elements);  // takes ownership
    QuPage* addTag(const QString& tag);
    QuPage* allowScroll(bool allow_scroll);
    QVector<QuElement*> elementsWithTag(const QString& tag);

    PageType type() const;
    QString title() const;
    bool hasTag(const QString& tag) const;
    bool skip() const;
    void clearElements();  // for rebuilding live pages
    bool allowsScroll() const;
    bool missingInput() const;
    void blockProgress(bool block);
    bool progressBlocked() const;
signals:
    void elementValueChanged();
public slots:
    QuPage* setSkip(bool skip = true);
protected:
    void commonConstructor();
    QPointer<QWidget> widget(Questionnaire* questionnaire) const;
    QVector<QuElement*> allElements() const;
    void closing();
protected:
    PageType m_type;
    QString m_title;
    QStringList m_tags;
    QVector<QuElementPtr> m_elements;
    bool m_skip;
    bool m_allow_scroll;
    bool m_progress_blocked;
};
