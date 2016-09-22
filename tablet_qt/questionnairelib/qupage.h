#pragma once
#include <initializer_list>
#include <QList>
#include <QObject>
#include <QPointer>
#include <QSharedPointer>
#include "quelement.h"

class QWidget;
class Questionnaire;
class QuPage;

using QuPagePtr = QSharedPointer<QuPage>;


class QuPage : public QObject
{
    // Encapsulates a display page of QuElement objects.
    // A Questionnaire includes one or more QuPage objects.

    Q_OBJECT
    friend class Questionnaire;
public:
    enum class PageType {
        Inherit,
        Patient,
        Clinician,
        ClinicianWithPatient,
        Config,
    };
public:
    QuPage();
    QuPage(const QList<QuElementPtr>& elements);
    QuPage(std::initializer_list<QuElementPtr> elements);
    QuPage(std::initializer_list<QuElement*> elements);  // takes ownership

    QuPage* setType(PageType type);
    QuPage* setTitle(const QString& title);
    QuPage* addElement(const QuElementPtr& element);
    QuPage* addElement(QuElement* element);  // takes ownership

    virtual ~QuPage();

    PageType type() const;
    QString title() const;
signals:
    void elementValueChanged();
protected:
    QPointer<QWidget> widget(Questionnaire* questionnaire) const;
    QList<QuElementPtr> allElements() const;
    bool missingInput() const;
    void closing();
protected:
    PageType m_type;
    QString m_title;
    QList<QuElementPtr> m_elements;
};
