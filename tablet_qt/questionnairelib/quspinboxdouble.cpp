#include "quspinboxdouble.h"
#include <QDoubleSpinBox>
#include "lib/uifunc.h"
#include "questionnaire.h"


QuSpinBoxDouble::QuSpinBoxDouble(FieldRefPtr fieldref, double minimum,
                                 double maximum, int decimals) :
    m_fieldref(fieldref),
    m_minimum(minimum),
    m_maximum(maximum),
    m_decimals(decimals)
{
    Q_ASSERT(m_fieldref);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuSpinBoxDouble::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuSpinBoxDouble::fieldValueChanged);
}


void QuSpinBoxDouble::setFromField()
{
    fieldValueChanged(m_fieldref.data(), nullptr);
    // special; pretend "it didn't come from us" to disable the efficiency
    // check in fieldValueChanged
}


QPointer<QWidget> QuSpinBoxDouble::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    m_spinbox = new QDoubleSpinBox();
    m_spinbox->setEnabled(!read_only);
    m_spinbox->setDecimals(m_decimals);
    m_spinbox->setRange(m_minimum, m_maximum);
    m_spinbox->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Expanding);
    // QDoubleSpinBox has two signals named valueChanged, differing only
    // in the parameter they pass (double versus QString&). You get
    // "no matching function for call to ... unresolved overloaded function
    // type..."
    // Disambiguate like this:
    void (QDoubleSpinBox::*vc_signal)(double) = &QDoubleSpinBox::valueChanged;
    if (!read_only) {
        connect(m_spinbox.data(), vc_signal,
                this, &QuSpinBoxDouble::widgetValueChanged);
    }
    setFromField();
    return QPointer<QWidget>(m_spinbox);
}


FieldRefPtrList QuSpinBoxDouble::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}

void QuSpinBoxDouble::widgetValueChanged(double value)
{
    bool changed = m_fieldref->setValue(value, this);  // Will trigger valueChanged
    if (changed) {
        emit elementValueChanged();
    }
}


void QuSpinBoxDouble::fieldValueChanged(const FieldRef* fieldref,
                                        const QObject* originator)
{
    if (!m_spinbox) {
        return;
    }
    UiFunc::setPropertyMissing(m_spinbox, fieldref->missingInput());
    if (originator != this) {
        const QSignalBlocker blocker(m_spinbox);
        m_spinbox->setValue(fieldref->valueDouble());
    }
}
