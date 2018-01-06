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
#include <QCoreApplication>  // for Q_DECLARE_TR_FUNCTIONS
#include <QList>
#include <QObject>
#include <QPointer>
#include <QSharedPointer>
#include <QStringList>
#include "common/aliases_camcops.h"

class QWidget;
class Questionnaire;


class QuElement : public QObject
{
    // Base class for all questionnaire elements.
    //
    // Owns Qt widgets, but only creates them when asked (since a questionnaire
    // may contain many elements, but only a small subset are on the current
    // page and being displayed at any one time).

    Q_OBJECT
    friend class Questionnaire;
    friend class QuPage;
    friend class QuFlowContainer;
    friend class QuHorizontalContainer;
    friend class QuVerticalContainer;
    friend class QuGridContainer;
    friend class SettingsMenu;
    friend class WidgetTestMenu;
public:
    QuElement();
    virtual ~QuElement();
    QuElement* addTag(const QString& tag);

    bool hasTag(const QString& tag) const;
    bool visible() const;
    QuElement* setVisible(bool visible);
signals:
    void elementValueChanged();
protected:
    virtual QPointer<QWidget> widget(Questionnaire* questionnaire);
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) = 0;
    virtual QPointer<QWidget> cachedWidget() const;  // Not for general use!
    void show();
    void hide();
    virtual QVector<QuElementPtr> subelements() const;
    QVector<QuElement*> subelementsRaw() const;
    QVector<QuElementPtr> subelementsWithChildrenFlattened() const;
    QVector<QuElement*> subelementsWithChildrenFlattenedRaw() const;
    virtual bool missingInput() const;
    virtual FieldRefPtrList fieldrefs() const;
    virtual void closing();  // called prior to focus leaving this page (e.g. silence audio)
protected:
    QPointer<QWidget> m_widget;  // used to cache a widget pointer
    QStringList m_tags;
    bool m_visible;
};


/*
===============================================================================
Constructing element lists and pages
===============================================================================

 - When we make a Page of Elements, we have to use pointers, because we are
   going to be using polymorphic objects that inherit from Element, and we
   can't have a list of Elements (that may not be base class Elements)
   without using pointers.
   Example: http://stackoverflow.com/questions/7223613/c-polymorphism-without-pointers
 - Moreover, we cannot create a plain object then take a pointer from
   its address, since we'd be constructing the objects on the stack (by a
   task's edit() function), and they'd be destroyed before we want to use
   them (via a Qt call to the Questionnaire object).
 - So, we must create them on the heap with "new".
 - However, we want to be able to use method chaining, e.g.

      Text& bold() { ... return *this; }
      // ...
      ... Text("content").bold() ...

   But that doesn't work with "new".

   So it seems we must do:

      Text* bold() { ... return this; }
      // ...
      ... ElementPtr((new Text("content"))->bold()) ...

 - One other thing to look at: std::reference_wrapper
   ... but that still requires the objects to stay in scope:
       http://stackoverflow.com/questions/33110013/polymorphism-in-c-with-a-vector-with-base-classes-and-reference-wrapper

 - So, ElementPtr and "return this" it is.
 - We also have to create Questionnaire objects using "new", since they are
   Qt objects that Qt will manage.
 - It therefore seems a bit inconsistent to create Page objects on the stack
   and copy them, as that'd give odd-one-out usage.
 - So, pointers all the way in the Questionnaire system.

 - AH, NO. MORE ELEGANT (AND MUCH MORE READABLE FOR TASKS) IS THIS:

    - implement clone() method
    - Text& bold() { ... return *this; }
    - Text("content").bold().clone()

 - We could, ordinarily, implement the clone method automatically using CRTP.
   Search for "FighterPlane" in qt_notes.txt.
   However, this throws up a whole bunch of errors in QObject-derived objects,
   relating to
     - cannot convert from pointer to base class 'QObject' to pointer to
       derived class 'QuButton' via virtual base 'QuElement'
     - use of deleted function...
     - QObject::QObject(const QObject&) is private
       in definition of macro 'Q_DISABLE_COPY'
 - ... so do that by hand?
 - Still have similar problems relating to Q_DISABLE_COPY
    http://doc.qt.io/qt-5/qobject.html#Q_DISABLE_COPY
    http://stackoverflow.com/questions/2855495/qobject-cloning
 - So can we make elements *not* inherit from QObject? We're only deriving
   so we can receive signals.
   Yes, we can use a Handler:
        http://stackoverflow.com/questions/7502600/how-to-use-signal-and-slot-without-deriving-from-qobject
   or a lambda/more generic functor:
        http://stackoverflow.com/questions/26937517/qt-connect-without-qobject-or-slots
        http://doc.qt.io/qt-5.7/qobject.html#connect-4

 - HOWEVER, ONCE YOU ADD SIGNALS TO NON-QOBJECT OBJECTS WITH std::bind,
   the process of copying BREAKS THE SIGNAL.
   So either we have to have a two-phase process, saying "whatever you do,
   don't set up signals in your creation process", and have the Questionnaire
   set them up later (ugly, dangerous), or we just have to PROHIBIT COPYING,
   like QObject does. You see why...
 - In which case, we're back to the slightly uglier way, using pointers.
 - Ho hum, it's worth it for flexibility.
 - And if you're going to make them non-copyable, make them QObjects,
   to prevent accidental copying. Embrace the QObject!

===============================================================================
Widgets
===============================================================================

- Element widgets will be made using "new" and owned by Qt as usual.
- But we might like to access them +/- cache them.
- http://stackoverflow.com/questions/19331396/how-does-qt-delete-objects-and-what-is-the-best-way-to-store-qobjects
- Using a shared pointer for a QObject is tricky
  http://stackoverflow.com/questions/34433435/why-dont-the-official-qt-examples-and-tutorials-use-smart-pointers
- The proper way to hold a pointer to a QObject (particularly when you are not
  an appropriately lifetime-limited QObject yourself) is with a QPointer.

*/
