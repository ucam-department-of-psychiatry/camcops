#include "quphoto.h"
#include <QCameraInfo>
#include <QHBoxLayout>
#include <QLabel>
#include <QVBoxLayout>
#include "common/camcopsapp.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "widgets/aspectratiopixmaplabel.h"
#include "widgets/camera.h"
#include "widgets/imagebutton.h"
#include "questionnaire.h"


QuPhoto::QuPhoto(FieldRefPtr fieldref) :
    m_fieldref(fieldref),
    m_questionnaire(nullptr),
    m_incomplete_optional(nullptr),
    m_incomplete_mandatory(nullptr),
    m_field_problem(nullptr),
    m_image(nullptr),
    m_camera(nullptr)
{
    m_have_camera = QCameraInfo::availableCameras().count() > 0;
    qDebug() << "m_have_camera:" << m_have_camera;

    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuPhoto::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuPhoto::fieldValueChanged);
}


// ============================================================================
// Building the main widget
// ============================================================================

QPointer<QWidget> QuPhoto::makeWidget(Questionnaire* questionnaire)
{
    m_questionnaire = questionnaire;
    bool read_only = questionnaire->readOnly();
    Qt::Alignment align = Qt::AlignLeft | Qt::AlignTop;

    QAbstractButton* button_open_camera = nullptr;
    QLabel* no_camera = nullptr;
    if (m_have_camera) {
        button_open_camera = new ImageButton(UiConst::CBS_CAMERA);
        button_open_camera->setEnabled(!read_only && m_have_camera);
        if (!read_only) {
            connect(button_open_camera, &QAbstractButton::clicked,
                    this, &QuPhoto::takePhoto);
        }
    } else {
        no_camera = new QLabel(tr("No camera"));
    }

    QAbstractButton* button_reset = new ImageButton(UiConst::CBS_RELOAD);
    button_reset->setEnabled(!read_only);
    if (!read_only) {
        connect(button_reset, &QAbstractButton::clicked,
                this, &QuPhoto::resetFieldToNull);
    }

    QVBoxLayout* button_layout = new QVBoxLayout();
    if (m_have_camera) {
        button_layout->addWidget(button_open_camera, 0, align);
    } else {
        button_layout->addWidget(no_camera, 0, align);
    }
    button_layout->addWidget(button_reset, 0, align);
    button_layout->addStretch();

    QWidget* button_widget = new QWidget();
    button_widget->setLayout(button_layout);

    m_incomplete_optional = UiFunc::iconWidget(
                UiFunc::iconFilename(UiConst::ICON_FIELD_INCOMPLETE_OPTIONAL));
    m_incomplete_mandatory = UiFunc::iconWidget(
                UiFunc::iconFilename(UiConst::ICON_FIELD_INCOMPLETE_MANDATORY));
    m_field_problem = UiFunc::iconWidget(
                UiFunc::iconFilename(UiConst::ICON_FIELD_PROBLEM));
    m_image = new AspectRatioPixmapLabel();

    QVBoxLayout* image_layout = new QVBoxLayout();
    image_layout->addWidget(m_incomplete_optional, 0, align);
    image_layout->addWidget(m_incomplete_mandatory, 0, align);
    image_layout->addWidget(m_field_problem, 0, align);
    image_layout->addWidget(m_image, 0, align);
    // image_layout->addStretch();

    QWidget* image_and_marker_widget = new QWidget();
    image_and_marker_widget->setLayout(image_layout);
    image_and_marker_widget->setSizePolicy(QSizePolicy::Expanding,
                                           QSizePolicy::Maximum);

    QHBoxLayout* top_layout = new QHBoxLayout();
    top_layout->addWidget(button_widget, 0, align);
    top_layout->addWidget(image_and_marker_widget, 0, align);
    top_layout->addStretch();

    QWidget* main_widget = new QWidget();
    main_widget->setLayout(top_layout);
    main_widget->setObjectName("debug_green");
    main_widget->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Maximum);

    setFromField();

    return main_widget;
}


// ============================================================================
// Talking to fields
// ============================================================================

void QuPhoto::setFromField()
{
    fieldValueChanged(m_fieldref.data());
}


FieldRefPtrList QuPhoto::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}


void QuPhoto::fieldValueChanged(const FieldRef* fieldref)
{
    bool missing = fieldref->missingInput();
    bool null = fieldref->isNull();
    bool loaded = false;
    if (m_incomplete_mandatory) {
        m_incomplete_mandatory->setVisible(missing);
    }
    if (m_incomplete_optional) {
        m_incomplete_optional->setVisible(!missing && null);
    }
    if (m_image) {
        bool show_image = !missing && !null;
        m_image->setVisible(show_image);
        QImage img;
        if (show_image) {
            loaded = img.loadFromData(fieldref->valueByteArray());
        }
        if (loaded) {
            m_image->setPixmap(QPixmap::fromImage(img));
        } else {
            m_image->clear();
        }
    }
    if (m_field_problem) {
        m_field_problem->setVisible(!missing && !null && !loaded);
    }
}


void QuPhoto::takePhoto()
{
    if (!m_questionnaire) {
        qWarning() << Q_FUNC_INFO << "no questionnaire";
    }
    if (!m_have_camera) {
        qWarning() << Q_FUNC_INFO << "no camera";
        return;
    }

    QString stylesheet = m_questionnaire->app().getSubstitutedCss(
                UiConst::CSS_CAMCOPS_CAMERA);
    m_camera = new Camera(stylesheet);

    connect(m_camera, &Camera::imageCaptured,
            this, &QuPhoto::imageCaptured);
    connect(m_camera, &Camera::cancelled,
            this, &QuPhoto::cameraCancelled);

    m_questionnaire->openSubWidget(m_camera);
}


void QuPhoto::resetFieldToNull()
{
    m_fieldref->setValue(QVariant());
    // ... skip originator; will call fieldValueChanged
    emit elementValueChanged();
}


void QuPhoto::cameraCancelled()
{
    qDebug() << Q_FUNC_INFO;
    if (!m_camera) {
        return;
    }
    m_camera->finish();  // close the camera
}


void QuPhoto::imageCaptured()
{
    qDebug() << Q_FUNC_INFO;
    if (!m_camera) {
        qDebug() << "... no camera!";
        return;
    }
    QImage img = m_camera->image();
    m_fieldref->setValue(img);
    m_camera->finish();  // close the camera
    emit elementValueChanged();
}


// *** m_wait_box while opening camera
