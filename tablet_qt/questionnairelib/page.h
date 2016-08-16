#pragma once
#include <initializer_list>
#include <QList>
#include <QPointer>
#include <QSharedPointer>
#include "element.h"

class QWidget;
class Questionnaire;


enum class PageType {
    Inherit,
    Patient,
    Clinician,
    ClinicianWithPatient,
    Config,
};


class Page
{
public:
    Page();
    Page(const QList<ElementPtr>& elements);
    Page(std::initializer_list<ElementPtr> elements);

    Page* setType(PageType type);
    Page* setTitle(const QString& title);
    Page* addElement(const ElementPtr& element);

    PageType type() const;
    QString title() const;
    QPointer<QWidget> widget(Questionnaire* questionnaire) const;
protected:
    PageType m_type;
    QString m_title;
    QList<ElementPtr> m_elements;
};


typedef QSharedPointer<Page> PagePtr;
