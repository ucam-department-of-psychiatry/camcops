#include "qumultipleresponse.h"
#include <QVBoxLayout>
#include "common/random.h"
#include "widgets/booleanwidget.h"
#include "widgets/flowlayout.h"
#include "widgets/labelwordwrapwide.h"
#include "questionnaire.h"


QuMultipleResponse::QuMultipleResponse()
{
    commonConstructor();
}


QuMultipleResponse::QuMultipleResponse(
        const QList<QuestionWithOneField> items) :
    m_items(items)
{
    commonConstructor();
}


QuMultipleResponse::QuMultipleResponse(
        std::initializer_list<QuestionWithOneField> items) :
    m_items(items)
{
    commonConstructor();
}


void QuMultipleResponse::commonConstructor()
{
    m_minimum_answers = -1;
    m_maximum_answers = -1;
    m_randomize = false;
    m_show_instruction = true;
    m_horizontal = false;
    m_as_text_button = false;
    // Connect fieldrefs at widget build time, for simplicity.
}


QuMultipleResponse* QuMultipleResponse::addItem(
        const QuestionWithOneField& item)
{
    m_items.append(item);
    return this;
}


QuMultipleResponse* QuMultipleResponse::setMinimumAnswers(int minimum_answers)
{
    m_minimum_answers = minimum_answers;
    return this;
}


QuMultipleResponse* QuMultipleResponse::setMaximumAnswers(int maximum_answers)
{
    m_maximum_answers = maximum_answers;
    if (m_maximum_answers == 0) {  // dumb value, use -1 for don't care
        m_maximum_answers = -1;
    }
    return this;
}


QuMultipleResponse* QuMultipleResponse::setRandomize(bool randomize)
{
    m_randomize = randomize;
    return this;
}


QuMultipleResponse* QuMultipleResponse::setShowInstruction(
        bool show_instruction)
{
    m_show_instruction = show_instruction;
    return this;
}


QuMultipleResponse* QuMultipleResponse::setInstruction(
        const QString& instruction)
{
    m_instruction = instruction;
    return this;
}


QuMultipleResponse* QuMultipleResponse::setHorizontal(bool horizontal)
{
    m_horizontal = horizontal;
    return this;
}


QuMultipleResponse* QuMultipleResponse::setAsTextButton(bool as_text_button)
{
    m_as_text_button = as_text_button;
    return this;
}


QPointer<QWidget> QuMultipleResponse::makeWidget(Questionnaire* questionnaire)
{
    // Clear old stuff
    m_widgets.clear();

    // Randomize?
    if (m_randomize) {
        std::shuffle(m_items.begin(), m_items.end(), Random::rng);
    }

    bool read_only = questionnaire->readOnly();

    QPointer<QWidget> mainwidget = new QWidget();
    QLayout* mainlayout;
    if (m_horizontal) {
        mainlayout = new FlowLayout();
    } else {
        mainlayout = new QVBoxLayout();
    }
    mainlayout->setContentsMargins(UiConst::NO_MARGINS);
    mainwidget->setLayout(mainlayout);

    Qt::Alignment align = Qt::AlignLeft | Qt::AlignVCenter;
    for (int i = 0; i < m_items.size(); ++i) {
        const QuestionWithOneField& item = m_items.at(i);

        // Widget
        QPointer<BooleanWidget> w = new BooleanWidget();
        w->setReadOnly(read_only);
        w->setAppearance(m_as_text_button
                         ? BooleanWidget::Appearance::Text
                         : BooleanWidget::Appearance::CheckRed);
        if (m_as_text_button) {
            w->setText(item.text());
        }
        if (!read_only) {
            connect(w, &BooleanWidget::clicked,
                    std::bind(&QuMultipleResponse::clicked, this, i));
        }
        m_widgets.append(w);

        // Layout, +/- label
        if (m_as_text_button) {
            mainlayout->addWidget(w);
            mainlayout->setAlignment(w, align);
        } else {
            // cf. QuMCQ
            QWidget* itemwidget = new QWidget();
            LabelWordWrapWide* namelabel = new LabelWordWrapWide(item.text());
            if (!read_only) {
                namelabel->setClickable(true);
                connect(namelabel, &LabelWordWrapWide::clicked,
                        std::bind(&QuMultipleResponse::clicked, this, i));
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

        // Field-to-this connections
        // You can't use connect() with a std::bind and simultaneously
        // specify a connection type such as Qt::UniqueConnection (which
        // only works with QObject, I think).
        // However, you can use a QSignalMapper. Then you can wipe it before
        // connecting, removing the need for Qt::UniqueConnection.
        // Finally, you need to disambiguate the slot with e.g.
        //      void (QSignalMapper::*map_signal)() = &QSignalMapper::map;
        // ... But in the end, all widgets may need to be updated when a single
        // value changes (based on the number required), so all this was
        // pointless and we can use a single signal with no parameters.

        FieldRef* fr = item.fieldref().data();
        connect(fr, &FieldRef::valueChanged,
                this, &QuMultipleResponse::fieldValueChanged,
                Qt::UniqueConnection);
        connect(fr, &FieldRef::mandatoryChanged,
                this, &QuMultipleResponse::fieldValueChanged,
                Qt::UniqueConnection);
    }

    QPointer<QWidget> final_widget;
    if (m_show_instruction) {
        // Higher-level widget containing {instructions, actual MCQ}
        QVBoxLayout* layout_w_instr = new QVBoxLayout();
        layout_w_instr->setContentsMargins(UiConst::NO_MARGINS);
        QString instruction = m_instruction.isEmpty() ? defaultInstruction()
                                                      : m_instruction;
        LabelWordWrapWide* instructions = new LabelWordWrapWide(instruction);
        instructions->setObjectName("mcq_instruction");
        layout_w_instr->addWidget(instructions);
        layout_w_instr->addWidget(mainwidget);
        QPointer<QWidget> widget_w_instr = new QWidget();
        widget_w_instr->setLayout(layout_w_instr);
        final_widget = widget_w_instr;
    } else {
        final_widget = mainwidget;
    }

    setFromFields();

    return final_widget;
}


void QuMultipleResponse::clicked(int index)
{
    if (!validIndex(index)) {
        qWarning() << Q_FUNC_INFO << "- out of range";
        return;
    }
    bool at_max = nTrueAnswers() >= maximumAnswers();
    bool changed = false;
    const QuestionWithOneField item = m_items.at(index);
    FieldRefPtr fieldref = item.fieldref();
    QVariant value = fieldref->value();
    QVariant newvalue;
    if (value.isNull()) {  // NULL -> true
        if (!at_max) {
            newvalue = true;
            changed = true;
        }
    } else if (value.toBool()) {  // true -> false
        newvalue = false;
        changed = true;
    } else {  // false -> true
        if (!at_max) {
            newvalue = true;
            changed = true;
        }
    }
    if (!changed) {
        return;
    }
    fieldref->setValue(newvalue);  // Will trigger valueChanged
    emit elementValueChanged();
}


void QuMultipleResponse::setFromFields()
{
    fieldValueChanged();
}


void QuMultipleResponse::fieldValueChanged()
{
    bool need_more = nTrueAnswers() < minimumAnswers();
    for (int i = 0; i < m_items.size(); ++i) {
        FieldRefPtr fieldref = m_items.at(i).fieldref();
        QVariant value = fieldref->value();
        QPointer<BooleanWidget> w = m_widgets.at(i);
        if (!w) {
            qCritical() << Q_FUNC_INFO << "- defunct pointer!";
            continue;
        }
        if (!value.isNull() && value.toBool()) {
            // true
            w->setState(BooleanWidget::State::True);
        } else {
            // null or false (both look like blanks)
            w->setState(need_more ? BooleanWidget::State::NullRequired
                                  : BooleanWidget::State::Null);
            // We ignore mandatory properties on the fieldref, since we have a
            // minimum/maximum specified for them collectively.
            // Then we override missingInput() so that the QuPage uses our
            // information, not the fieldref information.
        }
    }
}


FieldRefPtrList QuMultipleResponse::fieldrefs() const
{
    FieldRefPtrList fieldrefs;
    for (auto item : m_items) {
        fieldrefs.append(item.fieldref());
    }
    return fieldrefs;
}


int QuMultipleResponse::minimumAnswers() const
{
    if (m_minimum_answers < 0) {
        return 1;
    }
    return qMax(1, m_minimum_answers);
}


int QuMultipleResponse::maximumAnswers() const
{
    if (m_maximum_answers < 0) {  // will never be exactly zero; see setter
        return m_items.size();
    }
    return qMin(m_items.size(), m_maximum_answers);
}


QString QuMultipleResponse::defaultInstruction() const
{
    int minimum = minimumAnswers();
    int maximum = maximumAnswers();
    if (minimum == maximum) {
        return QString("Choose %1:").arg(minimum);
    }
    if (m_minimum_answers < 0) {
        return QString("Choose up to %1:").arg(maximum);
    }
    if (m_maximum_answers < 0) {
        return QString("Choose %1 or more:").arg(minimum);
    }
    return QString("Choose %1–%2:").arg(minimum).arg(maximum);
}


bool QuMultipleResponse::validIndex(int index)
{
    return index >= 0 && index < m_items.size();
}


int QuMultipleResponse::nTrueAnswers() const
{
    int n = 0;
    for (auto item : m_items) {
        QVariant value = item.fieldref()->value();
        if (!value.isNull() && value.toBool()) {
            n += 1;
        }
    }
    return n;
}


bool QuMultipleResponse::missingInput() const
{
    return nTrueAnswers() < minimumAnswers();
}
