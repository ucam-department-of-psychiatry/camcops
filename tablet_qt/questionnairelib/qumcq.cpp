/*
    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#include "qumcq.h"
#include <QVBoxLayout>
#include <QWidget>
#include "common/cssconst.h"
#include "lib/uifunc.h"
#include "questionnairelib/mcqfunc.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "widgets/booleanwidget.h"
#include "widgets/clickablelabelwordwrapwide.h"
#include "widgets/flowlayout.h"
#include "widgets/heightforwidthlayoutcontainer.h"
#include "widgets/labelwordwrapwide.h"


QuMCQ::QuMCQ(FieldRefPtr fieldref, const NameValueOptions& options) :
    m_fieldref(fieldref),
    m_options(options),
    m_randomize(false),
    m_show_instruction(false),
    m_horizontal(false),
    m_as_text_button(false),
    m_bold(false)
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


QuMCQ* QuMCQ::setBold(bool bold)
{
    m_bold = bold;
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
    QPointer<QWidget> mainwidget;
    QLayout* mainlayout;
    if (m_horizontal) {
        mainwidget = new HeightForWidthLayoutContainer();
        mainlayout = new FlowLayout();
    } else {
        mainwidget = new QWidget();
        mainwidget->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
        mainlayout = new QVBoxLayout();
    }
    mainlayout->setContentsMargins(UiConst::NO_MARGINS);
    mainwidget->setLayout(mainlayout);
    // QGridLayout, but not QVBoxLayout or QHBoxLayout, can use addChildLayout;
    // the latter use addWidget.
    // FlowLayout is better than QHBoxLayout.

    for (int i = 0; i < m_options.size(); ++i) {
        const NameValuePair& nvp = m_options.at(i);

        // MCQ touch-me widget
        QPointer<BooleanWidget> w = new BooleanWidget();
        w->setReadOnly(read_only);
        w->setAppearance(m_as_text_button ? BooleanWidget::Appearance::Text
                                          : BooleanWidget::Appearance::Radio);
        if (m_as_text_button) {
            w->setText(nvp.name());
            w->setBold(m_bold);
        }
        if (!read_only) {
            // Safe object lifespan signal: can use std::bind
            connect(w, &BooleanWidget::clicked,
                    std::bind(&QuMCQ::clicked, this, i));
        }
        m_widgets.append(w);

        if (m_as_text_button) {
            mainlayout->addWidget(w);
            mainlayout->setAlignment(w, Qt::AlignTop);
        } else {
            // MCQ option label
            // Even in a horizontal layout, encapsulating widget/label pairs
            // prevents them being split apart.
            QWidget* itemwidget = new QWidget();
            ClickableLabelWordWrapWide* namelabel =
                    new ClickableLabelWordWrapWide(nvp.name());
            namelabel->setEnabled(!read_only);
            int fontsize = questionnaire->fontSizePt(UiConst::FontSize::Normal);
            bool italic = false;
            QString css = UiFunc::textCSS(fontsize, m_bold, italic);
            namelabel->setStyleSheet(css);

            if (!read_only) {
                // Safe object lifespan signal: can use std::bind
                connect(namelabel, &ClickableLabelWordWrapWide::clicked,
                        std::bind(&QuMCQ::clicked, this, i));
            }
            QHBoxLayout* itemlayout = new QHBoxLayout();
            itemlayout->setContentsMargins(UiConst::NO_MARGINS);
            itemwidget->setLayout(itemlayout);
            itemlayout->addWidget(w);
            itemlayout->addWidget(namelabel);
            itemlayout->setAlignment(w, Qt::AlignTop);
            itemlayout->setAlignment(namelabel, Qt::AlignVCenter);  // different
            itemlayout->addStretch();

            mainlayout->addWidget(itemwidget);
            mainlayout->setAlignment(itemwidget, Qt::AlignTop);
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
        LabelWordWrapWide* instructions = new LabelWordWrapWide(tr("Pick one:"));
        instructions->setObjectName(CssConst::MCQ_INSTRUCTION);
        layout_w_instr->addWidget(instructions);
        layout_w_instr->addWidget(mainwidget);
        QPointer<QWidget> widget_w_instr = new QWidget();
        widget_w_instr->setLayout(layout_w_instr);
        widget_w_instr->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Maximum);
        final_widget = widget_w_instr;
    } else {
        final_widget = mainwidget;
    }

    setFromField();

    return final_widget;
}


void QuMCQ::clicked(int index)
{
    if (!m_options.validIndex(index)) {
        qWarning() << Q_FUNC_INFO << "- out of range";
        return;
    }
    QVariant newvalue = m_options.value(index);
    bool changed = m_fieldref->setValue(newvalue);  // Will trigger valueChanged
    if (changed) {
        emit elementValueChanged();
    }
}


void QuMCQ::setFromField()
{
    fieldValueChanged(m_fieldref.data());
}


void QuMCQ::fieldValueChanged(const FieldRef* fieldref)
{
    McqFunc::setResponseWidgets(m_options, m_widgets, fieldref);
}


FieldRefPtrList QuMCQ::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}
