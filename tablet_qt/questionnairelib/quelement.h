#pragma once
#include <QObject>
#include <QPointer>
#include <QSharedPointer>
#include <QStringList>

class QWidget;
class Questionnaire;
class QuElement;

typedef QSharedPointer<QuElement> QuElementPtr;


class QuElement : public QObject  // derivation allows signals for children
{
    Q_OBJECT
    friend class QuPage;
public:
    QuElement();
    virtual ~QuElement();
    QuElement* addTag(const QString& tag);
protected:
    virtual QPointer<QWidget> getWidget(Questionnaire* questionnaire);
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) = 0;
    bool hasTag(const QString& tag);
    void show();
    void hide();
    void setVisible(bool visible);
    virtual QList<QuElementPtr> subelements() const;
    bool missingInput() const;  // block progress because required input is missing?
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
