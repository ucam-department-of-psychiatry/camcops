#include "qucanvas.h"
#include <QDebug>
#include <QLabel>
#include "questionnaire.h"


QuCanvas::QuCanvas(FieldRefPtr fieldref, const QSize& size,
                   QImage::Format format, const QColor& background_colour,
                   const QColor& pen_colour) :
    m_fieldref(fieldref),
    m_size(size),
    m_format(format),
    m_background_colour(background_colour),
    m_pen_colour(pen_colour)
  // m_template_filename: default
{
    m_using_template = false;
    commonConstructor();
}


QuCanvas::QuCanvas(FieldRefPtr fieldref, const QString& template_filename,
                   const QColor& pen_colour) :
    m_fieldref(fieldref),
    // m_size: below
    // m_format: below
    m_background_colour(Qt::white),
    m_pen_colour(pen_colour),
    m_template_filename(template_filename)
{
    if (m_template_img.load(m_template_filename)) {
        m_using_template = true;
        m_size = m_template_img.size();
        m_format = m_template_img.format();
    } else {
        // Failed to load
        qWarning() << Q_FUNC_INFO << "- failed to load:"
                   << m_template_filename;
        m_using_template = false;
        m_size = QSize(100, 100);  // some random default
        m_format = QImage::Format_RGB32;
    }
    commonConstructor();
}


void QuCanvas::commonConstructor()
{
    Q_ASSERT(m_fieldref);
    m_label = nullptr;
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuCanvas::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuCanvas::fieldValueChanged);
}


QPointer<QWidget> QuCanvas::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    // ***
}


void QuCanvas::setFromField()
{
    fieldValueChanged(m_fieldref.data(), nullptr);
}


void QuCanvas::fieldValueChanged(const FieldRef* fieldref,
                                 const QObject* originator)
{
    if (!m_label) {
        return;
    }
    // *** mandatory
    if (originator != this) {
        if (fieldref->isNull()) {
            reset();
        } else {
            bool success = m_img.loadFromData(fieldref->valueByteArray());
            if (!success) {
                qWarning() << Q_FUNC_INFO
                           << "- bad image data in field; resetting";
                reset();
            }
        }
        // *** copy m_img to widget
    }
}


FieldRefPtrList QuCanvas::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}


void QuCanvas::reset()
{
    if (m_using_template) {
        m_img = m_template_img;
    } else {
        m_img = QImage(m_size, m_format);
        m_img.fill(m_background_colour);
    }
}


bool QuCanvas::mono() const
{
    return m_format == QImage::Format_Mono ||
            m_format == QImage::Format_MonoLSB;
}
