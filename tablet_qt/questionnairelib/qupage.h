/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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
    // (A Questionnaire includes one or more QuPage objects.)

    Q_OBJECT
    friend class Questionnaire;

public:
    enum class PageType {  // "Who should be entering data into this page?"
        Inherit,  // from the Questionnaire
        Patient,
        Clinician,
        ClinicianWithPatient,
        Config,
    };

public:
    // Empty constructor.
    QuPage();

    // Construct with a list of QuElement objects.
    QuPage(const QVector<QuElementPtr>& elements);
    QuPage(std::initializer_list<QuElementPtr> elements);
    QuPage(const QVector<QuElement*>& elements);  // takes ownership
    QuPage(std::initializer_list<QuElement*> elements);  // takes ownership

    // Destructor
    virtual ~QuPage();

    virtual void build() {}  // for on-the-fly building

    // Set the page type: "who should be entering data?" (e.g. patient,
    // clinician)
    QuPage* setType(PageType type);

    // Set the page's title, displayed on the page.
    QuPage* setTitle(const QString& title);

    // Set the page's title, displayed on the page index ("jump-to-page" list).
    QuPage* setIndexTitle(const QString& index_title);

    // Add an element
    QuPage* addElement(const QuElementPtr& element);
    QuPage* addElement(QuElement* element);  // takes ownership

    // Add multiple elements
    QuPage* addElements(const QVector<QuElementPtr>& elements);
    QuPage* addElements(const QVector<QuElement*>& elements);  // takes ownership

    // Adds a string tag to this page.
    QuPage* addTag(const QString& tag);

    // Allow this page to scroll vertically? Default is true, but you may
    // want to disable this e.g. for canvas pages.
    QuPage* allowScroll(bool allow_scroll);

    // Return all elements belonging to this page that possess the specified
    // tag.
    QVector<QuElement*> elementsWithTag(const QString& tag);

    // Returns the page's type (e.g. patient, clinician).
    PageType type() const;

    // Returns the page's main title (shown on the page).
    QString title() const;

    // Returns the page's index title (shown in the jump-to-page index)>
    QString indexTitle() const;

    // Does this page have the specified tag?
    bool hasTag(const QString& tag) const;

    // Is this page marked to be skipped in the Questionnaire?
    bool skip() const;

    // Wipe all elements. (For rebuilding live pages.)
    void clearElements();

    // Does the page allow vertical scrolling?
    bool allowsScroll() const;

    // Does the page have any missing input (mandatory and with no data)?
    bool missingInput() const;

    // Set the page to block progress (or not).
    void blockProgress(bool block);

    // Is the page blocking progress?
    bool progressBlocked() const;

signals:
    // "One of our elements has changed value."
    void elementValueChanged();

public slots:
    // Sets whether this page is marked to be skipped.
    QuPage* setSkip(bool skip = true);

protected:
    // Returns this page's widget.
    QPointer<QWidget> widget(Questionnaire* questionnaire) const;

    // Returns all elements (as raw pointers, for speed).
    QVector<QuElement*> allElements() const;

    // Called when the page is being closed. (In turn, signals to its elements.)
    void closing();

protected:
    PageType m_type;  // page type (e.g. patient, clinician)
    QString m_title;  // page main title
    QString m_index_title;  // page title for jump-to-page index
    QStringList m_tags;  // tags that this page has
    QVector<QuElementPtr> m_elements;  // page's elements
    bool m_skip;  // skip this page?
    bool m_allow_scroll;  // allow vertical scroll?
    bool m_progress_blocked;  // is the page blocking progress?
};
