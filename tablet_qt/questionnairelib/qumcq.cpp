#include "qumcq.h"
#include <QVBoxLayout>
#include <QWidget>
#include "lib/uifunc.h"
#include "widgets/booleanwidget.h"
#include "widgets/labelwordwrapwide.h"
#include "widgets/flowlayout.h"
#include "questionnaire.h"
#include "questionnairefunc.h"


QuMCQ::QuMCQ(FieldRefPtr fieldref, const NameValueOptions& options) :
    m_fieldref(fieldref),
    m_options(options),
    m_randomize(false),
    m_show_instruction(false),
    m_horizontal(false),
    m_as_text_button(false)
{
    m_options.validateOrDie();
    Q_ASSERT(m_fieldref);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuMCQ::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuMCQ::fieldValueChanged);
}


QuMCQ* QuMCQ::setRandomize(bool randomize)
{
    m_randomize = randomize;
    return this;
}


QuMCQ* QuMCQ::setShowInstruction(bool show_instruction)
{
    m_show_instruction = show_instruction;
    return this;
}


QuMCQ* QuMCQ::setHorizontal(bool horizontal)
{
    m_horizontal = horizontal;
    return this;
}


QuMCQ* QuMCQ::setAsTextButton(bool as_text_button)
{
    m_as_text_button = as_text_button;
    return this;
}


QPointer<QWidget> QuMCQ::makeWidget(Questionnaire* questionnaire)
{
    // Clear old stuff (BEWARE: "empty()" = "isEmpty()" != "clear()")
    m_widgets.clear();

    // Randomize?
    if (m_randomize) {
        m_options.shuffle();
    }

    bool read_only = questionnaire->readOnly();

    // Actual MCQ: widget containing {widget +/- label} for each option
    QPointer<QWidget> mainwidget = new QWidget();
    QLayout* mainlayout;
    if (m_horizontal) {
        mainlayout = new FlowLayout();
    } else {
        mainlayout = new QVBoxLayout();
    }
    mainlayout->setContentsMargins(UiConst::NO_MARGINS);
    mainwidget->setLayout(mainlayout);
    // QGridLayout, but not QVBoxLayout or QHBoxLayout, can use addChildLayout;
    // the latter use addWidget.
    // FlowLayout is better than QHBoxLayout.

    Qt::Alignment align = Qt::AlignLeft | Qt::AlignVCenter;
    for (int i = 0; i < m_options.size(); ++i) {
        const NameValuePair& nvp = m_options.at(i);

        // MCQ touch-me widget
        QPointer<BooleanWidget> w = new BooleanWidget();
        w->setReadOnly(read_only);
        w->setAppearance(m_as_text_button ? BooleanWidget::Appearance::Text
                                          : BooleanWidget::Appearance::Radio);
        if (m_as_text_button) {
            w->setText(nvp.name());
        }
        if (!read_only) {
            connect(w, &BooleanWidget::clicked,
                    std::bind(&QuMCQ::clicked, this, i));
        }
        m_widgets.append(w);

        if (m_as_text_button) {
            mainlayout->addWidget(w);
            mainlayout->setAlignment(w, align);
        } else {
            // MCQ option label
            // Even in a horizontal layout, encapsulating widget/label pairs
            // prevents them being split apart.
            QWidget* itemwidget = new QWidget();
            LabelWordWrapWide* namelabel = new LabelWordWrapWide(nvp.name());
            if (!read_only) {
                namelabel->setClickable(true);
                connect(namelabel, &LabelWordWrapWide::clicked,
                        std::bind(&QuMCQ::clicked, this, i));
            }
            QHBoxLayout* itemlayout = new QHBoxLayout();
            itemlayout->setContentsMargins(UiConst::NO_MARGINS);
            itemwidget->setLayout(itemlayout);
            itemlayout->addWidget(w);
            itemlayout->addWidget(namelabel);
            itemlayout->setAlignment(w, align);
            itemlayout->setAlignment(namelabel, align);
            itemlayout->addStretch();
            mainlayout->addWidget(itemwidget);
            mainlayout->setAlignment(itemwidget, align);
        }
        // The FlowLayout seems to ignore vertical centring. This makes it look
        // slightly dumb when one label has much longer text than the others,
        // but overall this is the best compromise I've found.
    }

    QPointer<QWidget> final_widget;
    if (m_show_instruction) {
        // Higher-level widget containing {instructions, actual MCQ}
        QVBoxLayout* layout_w_instr = new QVBoxLayout();
        layout_w_instr->setContentsMargins(UiConst::NO_MARGINS);
        LabelWordWrapWide* instructions = new LabelWordWrapWide(
            tr("Pick one:"));
        instructions->setObjectName("mcq_instruction");
        layout_w_instr->addWidget(instructions);
        layout_w_instr->addWidget(mainwidget);
        QPointer<QWidget> widget_w_instr = new QWidget();
        widget_w_instr->setLayout(layout_w_instr);
        final_widget = widget_w_instr;
    } else {
        final_widget = mainwidget;
    }

    setFromField();

    return final_widget;
}


void QuMCQ::clicked(int index)
{
    // qDebug() << "QuMCQ::clicked:" << index;
    if (!m_options.validIndex(index)) {
        qWarning() << "QuMCQ::clicked - out of range";
        return;
    }
    QVariant newvalue = m_options.value(index);
    m_fieldref->setValue(newvalue);  // Will trigger valueChanged
    emit elementValueChanged();
}


void QuMCQ::setFromField()
{
    fieldValueChanged(m_fieldref.data());
}


void QuMCQ::fieldValueChanged(const FieldRef* fieldref)
{
    // qDebug().nospace() << "QuBooleanText: receiving valueChanged: this="
    //                    << this  << ", value=" << value;
    // We can have a "not chosen" null and an "actively chosen" null.
    QVariant value = fieldref->value();
    bool null = value.isNull();
    int index = m_options.indexFromValue(value);
    if (!null && index == -1) {
        qWarning() << "QuMCQ::valueChanged - unknown value";
        return;
    }
    for (int i = 0; i < m_widgets.size(); ++i) {
        QPointer<BooleanWidget> w = m_widgets.at(i);
        if (!w) {
            qCritical() << "QuMCQ::valueChanged(): defunct pointer!";
            continue;
        }
        if (i == index) {
            w->setState(BooleanWidget::State::True);
        } else if (index == -1) {  // null but not selected
            w->setState(fieldref->mandatory()
                        ? BooleanWidget::State::NullRequired
                        : BooleanWidget::State::Null);
        } else {
            w->setState(BooleanWidget::State::False);
        }
    }
}


FieldRefPtrList QuMCQ::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}
