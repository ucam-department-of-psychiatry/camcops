#include "qupickerinline.h"
#include <QComboBox>
#include <QLabel>
#include "lib/uifunc.h"
#include "questionnaire.h"
#include "questionnairefunc.h"


const int MAX_LENGTH = 100;


QuPickerInline::QuPickerInline(FieldRefPtr fieldref,
                               const NameValueOptions& options) :
    m_fieldref(fieldref),
    m_options(options),
    m_cbox(nullptr)
{
    m_options.validateOrDie();
    Q_ASSERT(m_fieldref);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuPickerInline::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuPickerInline::fieldValueChanged);
}


QPointer<QWidget> QuPickerInline::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    m_cbox = new QComboBox();
    for (int i = 0; i < m_options.size(); ++i) {
        const NameValuePair& nvp = m_options.at(i);
        m_cbox->insertItem(i, nvp.name().left(MAX_LENGTH));
        // No real point in passing the third QVariant parameter.
    }
    // QComboBox has two signals named currentIndexChanged, differing only
    // in the parameter they pass (int versus QString&). You get
    // "no matching function for call to ... unresolved overloaded function
    // type..."
    // Disambiguate like this:
    void (QComboBox::*ic_signal)(int) = &QComboBox::currentIndexChanged;
    if (!read_only) {
        connect(m_cbox.data(), ic_signal,
                this, &QuPickerInline::currentIndexChanged);
    }
    m_cbox->setEnabled(!read_only);
    m_cbox->setObjectName("picker_inline");
    setFromField();
    return QPointer<QWidget>(m_cbox);
}


void QuPickerInline::currentIndexChanged(int index)
{
    // qDebug().nospace() << "QuPickerInline::currentIndexChanged(" << index << ")";
    if (!m_options.validIndex(index)) {
        return;
    }
    QVariant newvalue = m_options.at(index).value();
    m_fieldref->setValue(newvalue);  // Will trigger valueChanged
    emit elementValueChanged();
}


void QuPickerInline::setFromField()
{
    fieldValueChanged(m_fieldref.data());
}


void QuPickerInline::fieldValueChanged(const FieldRef* fieldref)
{
    int index = m_options.indexFromValue(fieldref->value());
    bool missing = fieldref->missingInput();
    if (m_cbox) {
        {
            const QSignalBlocker blocker(m_cbox);
            // qDebug() << "QuPickerInline::valueChanged(): index =" << index;
            m_cbox->setCurrentIndex(index);  // it's happy with -1
        }
        UiFunc::setPropertyMissing(m_cbox, missing);
    }
}


FieldRefPtrList QuPickerInline::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}
