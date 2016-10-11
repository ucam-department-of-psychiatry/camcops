#pragma once
#include <QList>
#include "db/fieldref.h"
#include "quelement.h"
#include "quthermometeritem.h"

class ImageButton;


class QuThermometer : public QuElement
{
    // Offers a stack of images, allowing the user to select one (and
    // displaying an alternative image at the chosen location), such as for
    // something in the style of a distress thermometer.
    //
    // The thermometer operates on name/value pairs; the thing that gets stored
    // in the field is the value() part of the QuThermometerItem.

    Q_OBJECT
public:
    QuThermometer(FieldRefPtr fieldref,
                  const QList<QuThermometerItem>& items);
    QuThermometer(FieldRefPtr fieldref,
                  std::initializer_list<QuThermometerItem> items);
    QuThermometer* setRescale(bool rescale, double rescale_factor);
protected:
    void commonConstructor();
    void setFromField();
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
