#include "qupickerpopup.h"
#include <QDialog>
#include "lib/uifunc.h"
#include "widgets/clickablelabel.h"
#include "widgets/nvpchoicedialog.h"
#include "questionnaire.h"


const int MAX_LENGTH = 100;


QuPickerPopup::QuPickerPopup(FieldRefPtr fieldref,
                             const NameValueOptions& options) :
    m_fieldref(fieldref),
    m_options(options),
    m_label(nullptr)
{
    m_options.validateOrDie();
    Q_ASSERT(m_fieldref);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuPickerPopup::valueChanged);
}


QuPickerPopup* QuPickerPopup::setPopupTitle(const QString &popup_title)
{
    m_popup_title = popup_title;
    return this;
}


QPointer<QWidget> QuPickerPopup::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    m_label = new ClickableLabel();
    m_label->setClickable(!read_only);
    m_label->setObjectName("picker_popup");
    if (!read_only) {
        connect(m_label.data(), &ClickableLabel::clicked,
                this, &QuPickerPopup::clicked);
    }
    setFromField();
    return QPointer<QWidget>(m_label);
}


void QuPickerPopup::clicked()
{
    if (!m_label) {
        return;
    }
    NvpChoiceDialog* dlg = new NvpChoiceDialog(m_label, m_options,
                                               m_popup_title);
    QVariant newvalue;
    if (dlg->choose(&newvalue) != QDialog::Accepted) {
        return;  // user pressed cancel, or some such
    }
    m_fieldref->setValue(newvalue);  // Will trigger valueChanged
    emit elementValueChanged();
}


void QuPickerPopup::setFromField()
{
    valueChanged(m_fieldref.data());
}


void QuPickerPopup::valueChanged(const FieldRef* fieldref)
{
    if (!m_label) {
        return;
    }
    int index = m_options.indexFromValue(fieldref->value());
    bool missing = fieldref->missingInput();
    QString text = m_options.name(index).left(MAX_LENGTH);
    m_label->setText(text);
    UiFunc::setPropertyMissing(m_label, missing);
}


FieldRefPtrList QuPickerPopup::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}
