#include "quslider.h"
#include <QHBoxLayout>
#include <QLabel>
#include <QTimer>
#include <QVBoxLayout>
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "questionnaire.h"


const int WRITE_DELAY_MS = 10;


QuSlider::QuSlider(FieldRefPtr fieldref, int minimum, int maximum, int step) :
    // Core
    m_fieldref(fieldref),
    m_minimum(minimum),
    m_maximum(maximum),
    m_step(step),
    m_convert_for_real_field(false),
    m_field_minimum(minimum),
    m_field_maximum(maximum),
    m_null_apparent_value(minimum),
    // Visuals
    m_horizontal(true),
    m_show_value(false),
    m_tick_interval(false),
    m_tick_position(QSlider::NoTicks),
    m_use_default_labels(false),
    m_tick_label_position(QSlider::NoTicks),
    // Internals
    m_value_label(nullptr),
    m_slider(nullptr),
    m_field_write_pending(false),
    m_timer(new QTimer(this))
{
    Q_ASSERT(m_fieldref);
    m_big_step = 2 * step;
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuSlider::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuSlider::fieldValueChanged);
    m_timer->setSingleShot(true);
    connect(m_timer.data(), &QTimer::timeout,
            this, &QuSlider::completePendingFieldWrite);
}


QuSlider* QuSlider::setBigStep(int big_step)
{
    m_big_step = qMin(m_step, big_step);
    return this;
}


QuSlider* QuSlider::setTickInterval(bool tick_interval)
{
    m_tick_interval = tick_interval;
    return this;
}


QuSlider* QuSlider::setTickPosition(QSlider::TickPosition position)
{
    m_tick_position = position;
    return this;
}


QuSlider* QuSlider::setConvertForRealField(bool convert_for_real_field,
                                           double field_minimum,
                                           double field_maximum,
                                           int display_dp)
{
    m_convert_for_real_field = convert_for_real_field;
    m_field_minimum = field_minimum;
    m_field_maximum = field_maximum;
    m_display_dp = display_dp;
    return this;
}


QuSlider* QuSlider::setHorizontal(bool horizontal)
{
    m_horizontal = horizontal;
    return this;
}


QuSlider* QuSlider::setShowValue(bool show_value)
{
    m_show_value = show_value;
    return this;
}


QuSlider* QuSlider::setTickLabels(const QMap<int, QString>& labels)
{
    m_tick_labels = labels;
    m_use_default_labels = false;
    return this;
}


QuSlider* QuSlider::setTickLabelPosition(QSlider::TickPosition position)
{
    m_tick_label_position = position;
    return this;
}


QuSlider* QuSlider::setUseDefaultTickLabels(bool use_default)
{
    m_use_default_labels = use_default;
    return this;
}


void QuSlider::setFromField()
{
    fieldValueChanged(m_fieldref.data(), nullptr);
    // special; pretend "it didn't come from us" to disable the efficiency
    // check in fieldValueChanged
}


int QuSlider::sliderValueFromField(const QVariant& field_value) const
{
    if (field_value.isNull()) {
        return m_null_apparent_value;
    }
    if (!m_convert_for_real_field) {
        return field_value.toInt();
    }
    double field_from_left = field_value.toDouble() - m_field_minimum;
    double slider_range = m_maximum - m_minimum;
    double field_range = m_field_maximum - m_field_minimum;
    int slider_pos = (field_from_left * slider_range / field_range) +
            m_minimum;
    return slider_pos;
}


QVariant QuSlider::fieldValueFromSlider(int slider_value) const
{
    if (!m_convert_for_real_field) {
        return slider_value;
    }
    double slider_from_left = slider_value - m_minimum;
    double slider_range = m_maximum - m_minimum;
    double field_range = m_field_maximum - m_field_minimum;
    double field_pos = (slider_from_left * field_range / slider_range ) +
            m_field_minimum;
    return field_pos;
}


QPointer<QWidget> QuSlider::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    m_container_widget = new QWidget();
    m_value_label = nullptr;

    // 1. Value label
    if (m_show_value) {
        m_value_label = new QLabel();
        m_value_label->setObjectName("slider");
    }

    // 2. Slider (with labels)
    m_slider = new TickSlider(m_horizontal ? Qt::Horizontal : Qt::Vertical);
    m_slider->setMinimum(m_minimum);
    m_slider->setMaximum(m_maximum);
    m_slider->setSingleStep(m_step);
    m_slider->setPageStep(m_big_step);
    m_slider->setTickInterval(m_tick_interval);
    m_slider->setTickPosition(m_tick_position);
    if (m_use_default_labels) {
        m_slider->addDefaultTickLabels();
    } else {
        m_slider->setTickLabels(m_tick_labels);
    }
    m_slider->setTickLabelPosition(m_tick_label_position);
    m_slider->setReverseVerticalLabels(true);
    if (!read_only) {
        connect(m_slider.data(), &QSlider::valueChanged,
                this, &QuSlider::sliderValueChanged);
    }
    m_slider->setEnabled(!read_only);

    // Layout
    if (m_horizontal) {
        // --------------------------------------------------------------------
        // Horizontal
        // --------------------------------------------------------------------
        QVBoxLayout* layout = new QVBoxLayout();
        if (m_value_label) {
            layout->addWidget(m_value_label);
            layout->setAlignment(m_value_label,
                                 Qt::AlignHCenter | Qt::AlignVCenter);
        }
        QSizePolicy sp(QSizePolicy::MinimumExpanding, QSizePolicy::Fixed);
        m_slider->setSizePolicy(sp);
        layout->addWidget(m_slider);
        m_container_widget->setLayout(layout);
    } else {
        // --------------------------------------------------------------------
        // Vertical
        // --------------------------------------------------------------------
        QHBoxLayout* outerlayout = new QHBoxLayout();
        // Even for a vertical slider, have the numerical label above it,
        // or as it changes from "9" to "10" and its width changes, the
        // slider jiggles.
        QVBoxLayout* innerlayout = new QVBoxLayout();
        if (m_value_label) {
            innerlayout->addWidget(m_value_label);
            innerlayout->setAlignment(m_value_label,
                                      Qt::AlignHCenter | Qt::AlignVCenter);
        }
        QSizePolicy sp(QSizePolicy::Fixed, QSizePolicy::MinimumExpanding);
        m_slider->setSizePolicy(sp);
        innerlayout->addWidget(m_slider);
        outerlayout->addLayout(innerlayout);
        outerlayout->addStretch();
        m_container_widget->setLayout(outerlayout);
    }

    setFromField();
    return m_container_widget;
}


void QuSlider::sliderValueChanged(int slider_value)
{
    // Now, watch out. This can really screw up the UI performance.
    // QSlider objects can trigger lots of valueChanged signals very quickly.
    // http://stackoverflow.com/questions/26371571/qt-qslider-not-smooth
    m_field_write_slider_value = slider_value;
    m_field_write_pending = true;
    m_timer->start(WRITE_DELAY_MS);  // fires in same thread via event loop
    // ... goes to completePendingFieldWrite()
}


void QuSlider::completePendingFieldWrite()
{
    if (!m_field_write_pending) {
        return;
    }
    QVariant newvalue = fieldValueFromSlider(m_field_write_slider_value);
    m_fieldref->setValue(newvalue, this);  // Will trigger valueChanged
    m_field_write_pending = false;
    emit elementValueChanged();
}


void QuSlider::closing()
{
    completePendingFieldWrite();
}


void QuSlider::fieldValueChanged(const FieldRef* fieldref,
                                 const QObject* originator)
{
    if (m_container_widget) {
        UiFunc::setPropertyMissing(m_container_widget,
                                   fieldref->missingInput());
    }

    // Slider
    if (m_slider) {
        // Optimization: no point in setting the value of a slider whose
        // change was the immediate reason we're here.
        if (originator != this) {
            // Imperative that the slider doesn't generate an infinite loop
            // by emitting further "valueChanged" signals, which it will do
            // when you use its setValue() command, unless you use blockSignals
            // (and the safe way to do that is with a QSignalBlocker).
            const QSignalBlocker blocker(m_slider);
            int slider_value = sliderValueFromField(fieldref->value());
            // qDebug() << "Setting slider value to:" << slider_value;
            m_slider->setValue(slider_value);
        }
        m_slider->update();
    }

    // Text
    if (m_value_label) {
        QString text;
        if (fieldref->isNull()) {
            text = "?";
        } else if (m_convert_for_real_field) {
            text = QString::number(fieldref->valueDouble(), 'f', m_display_dp);
        } else {
            text = QString::number(fieldref->valueInt());
        }
        m_value_label->setText(text);
    }
}


FieldRefPtrList QuSlider::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}
