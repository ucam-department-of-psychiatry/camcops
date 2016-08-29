#pragma once
#include <QList>
#include "lib/fieldref.h"
#include "quelement.h"
#include "quthermometeritem.h"

class ImageButton;


class QuThermometer : public QuElement
{
    Q_OBJECT
public:
    QuThermometer(FieldRefPtr fieldref,
                  const QList<QuThermometerItem>& items);
    QuThermometer(FieldRefPtr fieldref,
                  std::initializer_list<QuThermometerItem> items);
    QuThermometer* setRescale(bool rescale, double rescale_factor);
    void setFromField();
protected:
    void commonConstructor();
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    int indexFromValue(const QVariant& value) const;
    QVariant valueFromIndex(int index) const;
protected slots:
    void clicked(int index);
    void fieldValueChanged(const FieldRef* fieldref);
protected:
    FieldRefPtr m_fieldref;
    QList<QuThermometerItem> m_items;
    bool m_rescale;
    double m_rescale_factor;
    QPointer<QWidget> m_main_widget;
    QList<QPointer<ImageButton>> m_active_widgets;
    QList<QPointer<ImageButton>> m_inactive_widgets;
};
