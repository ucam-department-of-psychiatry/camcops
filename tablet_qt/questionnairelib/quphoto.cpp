#include "quphoto.h"
#include <QCameraInfo>
#include <QHBoxLayout>
#include <QLabel>
#include <QVBoxLayout>
#include "common/camcopsapp.h"
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "lib/slownonguifunctioncaller.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/aspectratiopixmaplabel.h"
#include "widgets/camera.h"
#include "widgets/imagebutton.h"


QuPhoto::QuPhoto(FieldRefPtr fieldref) :
    m_fieldref(fieldref),
    m_questionnaire(nullptr),
    m_incomplete_optional(nullptr),
    m_incomplete_mandatory(nullptr),
    m_field_problem(nullptr),
    m_image(nullptr),
    m_camera(nullptr),
    m_main_widget(nullptr)
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

    QAbstractButton* button_reset = new ImageButton(UiConst::CBS_DELETE);
    button_reset->setEnabled(!read_only);
    if (!read_only) {
        connect(button_reset, &QAbstractButton::clicked,
                this, &QuPhoto::resetFieldToNull);
    }

    QAbstractButton* button_rot_left = new ImageButton(
                UiConst::CBS_ROTATE_ANTICLOCKWISE);
    button_rot_left->setEnabled(!read_only);
    if (!read_only) {
        connect(button_rot_left, &QAbstractButton::clicked,
                this, &QuPhoto::rotateLeft);
    }

    QAbstractButton* button_rot_right = new ImageButton(
                UiConst::CBS_ROTATE_CLOCKWISE);
    button_rot_right->setEnabled(!read_only);
    if (!read_only) {
        connect(button_rot_right, &QAbstractButton::clicked,
                this, &QuPhoto::rotateRight);
    }

    QVBoxLayout* button_layout = new QVBoxLayout();
    button_layout->setContentsMargins(UiConst::NO_MARGINS);
    if (m_have_camera) {
        button_layout->addWidget(button_open_camera, 0, align);
    } else {
        button_layout->addWidget(no_camera, 0, align);
    }
    button_layout->addWidget(button_rot_left, 0, align);
    button_layout->addWidget(button_rot_right, 0, align);
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
    image_layout->setContentsMargins(UiConst::NO_MARGINS);
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
    top_layout->setContentsMargins(UiConst::NO_MARGINS);
    top_layout->addWidget(button_widget, 0, align);
    top_layout->addWidget(image_and_marker_widget, 0, align);
    top_layout->addStretch();

    m_main_widget = new QWidget();
    m_main_widget->setLayout(top_layout);
    m_main_widget->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Maximum);

    setFromField();

    return m_main_widget;
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
        return;
    }
    if (!m_have_camera) {
        qWarning() << Q_FUNC_INFO << "no camera";
        return;
    }

    SlowGuiGuard guard = m_questionnaire->app().getSlowGuiGuard();

    QString stylesheet = m_questionnaire->getSubstitutedCss(
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
    if (m_fieldref->isNull()) {
        return;
    }
    if (!UiFunc::confirm(tr("Delete this photo?"),
                         tr("Confirm deletion"),
                         tr("Yes, delete"),
                         tr("No, cancel"),
                         m_main_widget)) {
        return;
    }

    bool changed = m_fieldref->setValue(QVariant());
    // ... skip originator; will call fieldValueChanged
    if (changed) {
        emit elementValueChanged();
    }
}


void QuPhoto::cameraCancelled()
{
    qDebug() << Q_FUNC_INFO;
    if (!m_camera) {
        return;
    }
    m_camera->finish();  // close the camera
}


void QuPhoto::imageCaptured(const QImage& image)
{
    qDebug() << Q_FUNC_INFO;
    if (!m_camera) {
        qDebug() << "... no camera!";
        return;
    }
    bool changed = m_fieldref->setValue(image);
    m_camera->finish();  // close the camera
    if (changed) {
        emit elementValueChanged();
    }
}


void QuPhoto::rotate(qreal angle_degrees)
{
    if (m_fieldref->isNull()) {
        return;
    }
    SlowNonGuiFunctionCaller(
                std::bind(&QuPhoto::rotateWorker, this, angle_degrees),
                m_main_widget,
                "Rotating...");
}


void QuPhoto::rotateWorker(qreal angle_degrees)
{
    QImage image = m_fieldref->valueImage();
    if (image.isNull()) {
        return;
    }
    QTransform matrix;
    matrix.rotate(angle_degrees);
    m_fieldref->setValue(image.transformed(matrix));
}


void QuPhoto::rotateLeft()
{
    // http://doc.qt.io/qt-4.8/qtransform.html#rotate
    rotate(-90);
}


void QuPhoto::rotateRight()
{
    rotate(90);
}
