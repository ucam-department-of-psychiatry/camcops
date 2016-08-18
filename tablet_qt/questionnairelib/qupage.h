#pragma once
#include <initializer_list>
#include <QList>
#include <QPointer>
#include <QSharedPointer>
#include "quelement.h"

class QWidget;
class Questionnaire;


enum class QuPageType {
    Inherit,
    Patient,
    Clinician,
    ClinicianWithPatient,
    Config,
};


class QuPage
{
    friend class Questionnaire;
public:
    QuPage();
    QuPage(const QList<QuElementPtr>& elements);
    QuPage(std::initializer_list<QuElementPtr> elements);

    QuPage* setType(QuPageType type);
    QuPage* setTitle(const QString& title);
    QuPage* addElement(const QuElementPtr& element);

    QuPageType type() const;
    QString title() const;
protected:
    QPointer<QWidget> widget(Questionnaire* questionnaire) const;
    QList<QuElementPtr> allElements() const;
    bool missingInput() const;
protected:
    QuPageType m_type;
    QString m_title;
    QList<QuElementPtr> m_elements;
};


typedef QSharedPointer<QuPage> QuPagePtr;
