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

typedef QSharedPointer<QuPage> QuPagePtr;


class QuPage : public QObject
{
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

    QuPage* setType(PageType type);
    QuPage* setTitle(const QString& title);
    QuPage* addElement(const QuElementPtr& element);

    PageType type() const;
    QString title() const;
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
