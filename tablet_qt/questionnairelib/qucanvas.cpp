#include "qucanvas.h"
#include <QDebug>
#include <QHBoxLayout>
#include <QLabel>
#include <QTimer>
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/canvaswidget.h"
#include "widgets/imagebutton.h"
#include "widgets/spacer.h"

const int WRITE_DELAY_MS = 200;


QuCanvas::QuCanvas(FieldRefPtr fieldref, const QSize& size,
                   QImage::Format format, const QColor& background_colour) :
    m_fieldref(fieldref),
    m_size(size),
    m_format(format),
    m_background_colour(background_colour),
    m_using_template(false)
{
    commonConstructor();
}


QuCanvas::QuCanvas(FieldRefPtr fieldref, const QString& template_filename,
                   const QSize& size) :
    m_fieldref(fieldref),
    m_size(size),
    m_background_colour(Qt::white),
    m_template_filename(template_filename),
    m_using_template(true)
{
    commonConstructor();
}


void QuCanvas::commonConstructor()
{
    Q_ASSERT(m_fieldref);
    m_pen_colour = Qt::red;
    m_pen_width = 5;
    m_canvas = nullptr;
    m_missing_indicator = nullptr;
    m_no_missing_indicator = nullptr;
    m_field_write_pending = false;
    m_timer = QSharedPointer<QTimer>(new QTimer());
    m_timer->setSingleShot(true);
    connect(m_timer.data(), &QTimer::timeout,
            this, &QuCanvas::completePendingFieldWrite);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuCanvas::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuCanvas::fieldValueChanged);
}


QuCanvas* QuCanvas::setPenColour(const QColor& pen_colour)
{
    m_pen_colour = pen_colour;
    return this;
}


QuCanvas* QuCanvas::setPenWidth(int pen_width)
{
    m_pen_width = pen_width;
    return this;
}


QPointer<QWidget> QuCanvas::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    Qt::Alignment align = Qt::AlignLeft | Qt::AlignTop;

    m_canvas = new CanvasWidget();
    QPen pen;
    pen.setColor(m_pen_colour);
    pen.setWidth(m_pen_width);
    m_canvas->setPen(pen);
    m_canvas->setEnabled(!read_only);
    if (!read_only) {
        connect(m_canvas.data(), &CanvasWidget::imageChanged,
                this, &QuCanvas::imageChanged);
    }

    QAbstractButton* button_reset = new ImageButton(UiConst::CBS_DELETE);
    button_reset->setEnabled(!read_only);
    if (!read_only) {
        connect(button_reset, &QAbstractButton::clicked,
                this, &QuCanvas::resetFieldToNull);
    }
    m_missing_indicator = UiFunc::iconWidget(
                UiFunc::iconFilename(UiConst::ICON_WARNING));
    m_no_missing_indicator = QPointer<Spacer>(new Spacer(UiConst::ICONSIZE));
    QVBoxLayout* button_layout = new QVBoxLayout();
    button_layout->setContentsMargins(UiConst::NO_MARGINS);
    button_layout->addWidget(button_reset, 0, align);
    button_layout->addWidget(m_missing_indicator, 0, align);
    button_layout->addWidget(m_no_missing_indicator, 0, align);
    QWidget* button_widget = new QWidget();
    button_widget->setLayout(button_layout);

    QHBoxLayout* top_layout = new QHBoxLayout();
    top_layout->setContentsMargins(UiConst::NO_MARGINS);
    top_layout->addWidget(button_widget, 0, align);
    top_layout->addWidget(m_canvas, 0, align);

    QWidget* widget = new QWidget();
    widget->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    widget->setLayout(top_layout);

    setFromField();
    return widget;
}


void QuCanvas::imageChanged()
{
    m_field_write_pending = true;
    m_timer->start(WRITE_DELAY_MS);  // goes to timerComplete
}


void QuCanvas::completePendingFieldWrite()
{
    if (!m_canvas || !m_field_write_pending) {
        return;
    }
    QImage img = m_canvas->image();
    bool changed = m_fieldref->setValue(img, this);
    m_field_write_pending = false;
    if (changed) {
        emit elementValueChanged();
    }
}


void QuCanvas::closing()
{
    completePendingFieldWrite();
}


void QuCanvas::setFromField()
{
    fieldValueChanged(m_fieldref.data(), nullptr);
}


void QuCanvas::fieldValueChanged(const FieldRef* fieldref,
                                 const QObject* originator)
{
    if (!m_canvas) {
        return;
    }

    // Mandatory: don't try to do it with a background; that doesn't work for
    // non-transparent templates, and it requires an immediate re-update when
    // the first strokes are drawn (but at all other times, we don't need to
    // redraw the widget when the user changes it).
    // So we'll do it with an indicator widget.

    bool missing_input = fieldref->missingInput();
    if (m_missing_indicator) {
        m_missing_indicator->setVisible(missing_input);
    }
    if (m_no_missing_indicator) {
        m_no_missing_indicator->setVisible(!missing_input);
    }
    // This prevents the overall widget's vertical size from changing (which
    // looks odd) on first draw, if the canvas is smaller vertically than the
    // two buttons/indicators.

    if (originator != this) {
        if (fieldref->isNull()) {
            resetWidget();
        } else {
            QImage img;
            bool success = img.loadFromData(fieldref->valueByteArray());
            if (success) {
                m_canvas->setImage(img);
            } else {
                qWarning() << Q_FUNC_INFO
                           << "- bad image data in field; resetting";
                resetWidget();
            }
        }
    }
}


FieldRefPtrList QuCanvas::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}


void QuCanvas::resetWidget()
{
    QImage img;
    bool make_duff_image = !m_using_template;
    bool use_source_image_size = true;
    if (m_using_template) {
        if (img.load(m_template_filename)) {  // side effect!
            use_source_image_size = !m_size.isValid();
        } else {
            // Failed to load
            qWarning() << Q_FUNC_INFO << "- failed to load:"
                       << m_template_filename;
            make_duff_image = true;
        }
    }
    if (make_duff_image) {
        img = QImage(m_size, m_format);
        img.fill(m_background_colour);
    }
    m_canvas->setImage(img, use_source_image_size);
    if (!use_source_image_size) {
        m_canvas->setSize(m_size);
    }
}


void QuCanvas::resetFieldToNull()
{
    resetWidget();
    m_fieldref->setValue(QVariant(), this);
    emit elementValueChanged();
}
