#include "quphoto.h"
#include <QCamera>
#include <QHBoxLayout>
#include <QLabel>
#include <QVBoxLayout>
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "widgets/imagebutton.h"
#include "questionnaire.h"


QuPhoto::QuPhoto(FieldRefPtr fieldref) :
    m_fieldref(fieldref)
{
    m_have_camera = QCameraInfo::availableCameras().count() > 0;
}


void QuPhoto::setFromField()
{
    fieldValueChanged(m_fieldref.data(), nullptr);
}


QPointer<QWidget> QuPhoto::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    Qt::Alignment align = Qt::AlignLeft | Qt::AlignTop;

    QWidget* widget = new QWidget();
    QHBoxLayout* top_layout = new QHBoxLayout();
    widget->setLayout(top_layout);

    // *** image widget, m_image
    // m_image->setEnabled(!read_only);
    // top_layout->addWidget(m_image, 0, align);

    QWidget* button_widget = new QWidget();
    top_layout->addWidget(button_widget, 0, align);
    QVBoxLayout* button_layout = new QVBoxLayout();
    button_widget->setLayout(button_layout);

    QAbstractButton* button_take = new ImageButton(UiConst::CBS_CAMERA);
    QAbstractButton* button_reload = new ImageButton(UiConst::CBS_RELOAD);
    button_take->setEnabled(!read_only && m_have_camera);
    button_reload->setEnabled(!read_only);
    if (!read_only) {
        connect(button_take, &QAbstractButton::clicked,
                this, &QuPhoto::takePhoto);
        connect(button_reload, &QAbstractButton::clicked,
                this, &QuPhoto::resetFieldToNull);
    }
    button_layout->addWidget(button_reload, 0, align);
    m_missing_indicator = UiFunc::iconWidget(
                UiFunc::iconFilename(UiConst::ICON_WARNING));
    button_layout->addWidget(m_missing_indicator, 0, align);
    button_layout->addStretch();

    top_layout->addStretch();

    setFromField();
    return widget;
}


FieldRefPtrList QuPhoto::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}


void QuPhoto::fieldValueChanged(const FieldRef* fieldref,
                                const QObject* originator)
{
    (void)fieldref;
    (void)originator;
}


void QuPhoto::photoChanged()
{

}


void QuPhoto::takePhoto()
{

}


void QuPhoto::resetFieldToNull()
{

}
