#include "qumcq.h"
#include <QVBoxLayout>
#include <QWidget>
#include "common/random.h"
#include "lib/uifunc.h"
#include "widgets/booleanwidget.h"
#include "widgets/labelwordwrapwide.h"
#include "widgets/flowlayout.h"
#include "questionnaire.h"
#include "questionnairefunc.h"


QuMCQ::QuMCQ(FieldRefPtr fieldref, const NameValuePairList& options) :
    m_fieldref(fieldref),
    m_options(options),
    m_randomize(false),
    m_show_instruction(false),
    m_horizontal(false),
    m_as_text_button(false)
{
    QuestionnaireFunc::ensureValidNvpList(m_options);
    Q_ASSERT(m_fieldref);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuMCQ::valueChanged);
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
    m_as_text_button = as_text_button; // ***
    return this;
}


QPointer<QWidget> QuMCQ::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    int fontsize = questionnaire->fontSizePt(UiConst::FontSize::Normal);

    QPointer<QWidget> mainwidget = new QWidget();
    QLayout* mainlayout;
    if (m_horizontal) {
        // mainlayout = new QHBoxLayout();
        mainlayout = new FlowLayout();
    } else {
        mainlayout = new QVBoxLayout();
    }
    mainwidget->setLayout(mainlayout);

    if (m_randomize) {
        std::shuffle(m_options.begin(), m_options.end(), Random::rng);
    }
    m_widgets.empty();
    m_value_to_index.empty();
    m_index_to_value.empty();
    // QGridLayout, but not QVBoxLayout or QHBoxLayout, can use addChildLayout;
    // the latter use addWidget.
    Qt::Alignment align = Qt::AlignLeft | Qt::AlignVCenter;
    for (int i = 0; i < m_options.size(); ++i) {
        const NameValuePair& nvp = m_options.at(i);
        qDebug() << "Option:" << nvp.name() << "->" << nvp.value();

        m_value_to_index[nvp.value()] = i;
        m_index_to_value[i] = nvp.value();

        // Widget
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
            // Label
            // Even in a horizontal layout, encapsulating widget/label pairs
            // prevents them being split apart.
            QWidget* itemwidget = new QWidget();
            LabelWordWrapWide* namelabel = new LabelWordWrapWide(nvp.name());
            namelabel->setStyleSheet(UiFunc::textCSS(fontsize));
            if (!read_only) {
                namelabel->setClickable(true);
                connect(namelabel, &LabelWordWrapWide::clicked,
                        std::bind(&QuMCQ::clicked, this, i));
            }
            QHBoxLayout* itemlayout = new QHBoxLayout();
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
        QVBoxLayout* layout_w_instr = new QVBoxLayout();
        LabelWordWrapWide* instructions = new LabelWordWrapWide(
            tr("Pick one:"));
        QString css = UiFunc::textCSS(fontsize, false, false,
                                      UiConst::MCQ_INSTRUCTION_COLOUR);
        instructions->setStyleSheet(css);
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


bool QuMCQ::complete() const
{
    QVariant value = m_fieldref->value();
    if (chosenIndex(value) != -1) {
        // Something actively chosen, even if that something is null
        return true;
    }
    return !value.isNull();
}


void QuMCQ::clicked(int index)
{
    qDebug() << "QuMCQ::clicked:" << index;
    if (!m_index_to_value.contains(index)) {
        qWarning() << "QuMCQ::clicked - out of range";
        return;
    }
    const QVariant& newvalue = m_index_to_value[index];
    m_fieldref->setValue(newvalue);  // Will trigger valueChanged
    emit elementValueChanged();
}


void QuMCQ::setFromField()
{
    valueChanged(m_fieldref->value());
}


int QuMCQ::chosenIndex(const QVariant& value) const
{
    int index = -1;
    if (m_value_to_index.contains(value)) {
        index = m_value_to_index[value];
    }
    return index;
}


void QuMCQ::valueChanged(const QVariant &value)
{
    qDebug().nospace() << "QuBooleanText: receiving valueChanged: this="
                       << this  << ", value=" << value;
    // We can have a "not chosen" null and an "actively chosen" null.
    bool null = value.isNull();
    int index = chosenIndex(value);
    if (!null && index == -1) {
        qWarning() << "QuMCQ::valueChanged - unknown value";
        return;
    }
    for (int i = 0; i < m_widgets.size(); ++i) {
        QPointer<BooleanWidget> w = m_widgets.at(i);
        if (i == index) {
            w->setState(BooleanWidget::State::True);
        } else if (index == -1) {  // null but not selected
            w->setState(m_mandatory ? BooleanWidget::State::NullRequired
                                    : BooleanWidget::State::Null);
        } else {
            w->setState(BooleanWidget::State::False);
        }
    }
}
