/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#include "qumcq.h"

#include <QWidget>

#include "common/cssconst.h"
#include "layouts/flowlayouthfw.h"
#include "layouts/layouts.h"
#include "lib/uifunc.h"
#include "questionnairelib/mcqfunc.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "widgets/basewidget.h"
#include "widgets/booleanwidget.h"
#include "widgets/clickablelabelwordwrapwide.h"
#include "widgets/labelwordwrapwide.h"

QuMcq::QuMcq(
    FieldRefPtr fieldref,
    const NameValueOptions& options,
    const QStringList* label_styles,
    QObject* parent
) :
    QuElement(parent),
    m_fieldref(fieldref),
    m_options(options),
    m_randomize(false),
    m_show_instruction(false),
    m_horizontal(false),
    m_as_text_button(false),
    m_bold(false)
{
    m_options.validateOrDie();
    if (label_styles) {
        m_label_styles = *label_styles;
        Q_ASSERT(m_label_styles.size() == m_options.size());
    }

    Q_ASSERT(m_fieldref);
    connect(
        m_fieldref.data(),
        &FieldRef::valueChanged,
        this,
        &QuMcq::fieldValueChanged
    );
    connect(
        m_fieldref.data(),
        &FieldRef::mandatoryChanged,
        this,
        &QuMcq::fieldValueChanged
    );
}

QuMcq* QuMcq::setRandomize(const bool randomize)
{
    m_randomize = randomize;
    return this;
}

QuMcq* QuMcq::setShowInstruction(const bool show_instruction)
{
    m_show_instruction = show_instruction;
    return this;
}

QuMcq* QuMcq::setHorizontal(const bool horizontal)
{
    m_horizontal = horizontal;
    return this;
}

QuMcq* QuMcq::setAsTextButton(const bool as_text_button)
{
    m_as_text_button = as_text_button;
    return this;
}

QuMcq* QuMcq::setBold(const bool bold)
{
    m_bold = bold;
    return this;
}

bool QuMcq::setOptionNames(const NameValueOptions& options)
{
    if (m_randomize || !options.valuesMatch(m_options)) {
        qWarning() << Q_FUNC_INFO
                   << "Attempt to change to incompatible options; prohibited";
        return false;
    }
    m_options = options;

    // Dynamic changes, if required:
    const int s = m_options.size();
    if (s > m_boolean_widgets.size() || s > m_label_widgets.size()) {
        // Widgets not yet created.
        return true;
    }
    for (int i = 0; i < s; ++i) {
        const QString& text = m_options.nameFromIndex(i);
        QPointer<BooleanWidget> bw = m_boolean_widgets[i];
        if (bw) {
            bw->setText(text);
        }
        QPointer<ClickableLabelWordWrapWide> lw = m_label_widgets[i];
        if (lw) {
            lw->setText(text);
        }
    }

    return true;
}

QPointer<QWidget> QuMcq::makeWidget(Questionnaire* questionnaire)
{
    // Clear old stuff (BEWARE: "empty()" = "isEmpty()" != "clear()")
    m_boolean_widgets.clear();
    m_label_widgets.clear();

    // Randomize?
    if (m_randomize) {
        m_options.shuffle();
    }

    const bool read_only = questionnaire->readOnly();

    // Actual MCQ: widget containing {widget +/- label} for each option
    QPointer<QWidget> mainwidget = new BaseWidget();
    QLayout* mainlayout;
    if (m_horizontal) {
        mainlayout = new FlowLayoutHfw();
    } else {
        mainlayout = new VBoxLayout();
    }
    mainlayout->setContentsMargins(uiconst::NO_MARGINS);
    mainwidget->setLayout(mainlayout);
    // QGridLayout, but not QVBoxLayout or QHBoxLayout, can use addChildLayout;
    // the latter use addWidget.
    // FlowLayout is better than QHBoxLayout.

    for (int position = 0; position < m_options.size(); ++position) {
        const NameValuePair& nvp = m_options.atPosition(position);

        // MCQ touch-me widget
        QPointer<BooleanWidget> w = new BooleanWidget();
        w->setReadOnly(read_only);
        w->setAppearance(
            m_as_text_button ? BooleanWidget::Appearance::Text
                             : BooleanWidget::Appearance::Radio
        );
        if (m_as_text_button) {
            w->setText(nvp.name());
            w->setBold(m_bold);
        }
        if (!read_only) {
            // Safe object lifespan signal: can use std::bind
            connect(
                w,
                &BooleanWidget::clicked,
                std::bind(&QuMcq::clicked, this, position)
            );
        }
        m_boolean_widgets.append(w);

        if (m_as_text_button) {
            mainlayout->addWidget(w);
            mainlayout->setAlignment(w, Qt::AlignTop);
            m_label_widgets.append(nullptr);
        } else {
            // MCQ option label
            // Even in a horizontal layout, encapsulating widget/label pairs
            // prevents them being split apart.
            auto itemwidget = new QWidget();
            auto namelabel = new ClickableLabelWordWrapWide(nvp.name());
            m_label_widgets.append(namelabel);
            namelabel->setEnabled(!read_only);
            const int fontsize
                = questionnaire->fontSizePt(uiconst::FontSize::Normal);
            const bool italic = false;
            QString css = uifunc::textCSS(fontsize, m_bold, italic);

            if (!m_label_styles.isEmpty()) {
                const int index = m_options.indexFromPosition(position);
                css += m_label_styles[index];
            }

            namelabel->setStyleSheet(css);

            if (!read_only) {
                // Safe object lifespan signal: can use std::bind
                connect(
                    namelabel,
                    &ClickableLabelWordWrapWide::clicked,
                    std::bind(&QuMcq::clicked, this, position)
                );
            }
            auto itemlayout = new HBoxLayout();
            itemlayout->setContentsMargins(uiconst::NO_MARGINS);
            itemwidget->setLayout(itemlayout);
            itemlayout->addWidget(w, 0, Qt::AlignTop);
            itemlayout->addWidget(namelabel, 0, Qt::AlignVCenter);
            // ... different
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
        auto layout_w_instr = new VBoxLayout();
        layout_w_instr->setContentsMargins(uiconst::NO_MARGINS);
        auto instructions = new LabelWordWrapWide(tr("Pick one:"));
        instructions->setObjectName(cssconst::MCQ_INSTRUCTION);
        layout_w_instr->addWidget(instructions);
        layout_w_instr->addWidget(mainwidget);
        QPointer<QWidget> widget_w_instr = new BaseWidget();
        widget_w_instr->setLayout(layout_w_instr);
        widget_w_instr->setSizePolicy(
            QSizePolicy::Preferred, QSizePolicy::Maximum
        );
        final_widget = widget_w_instr;
    } else {
        final_widget = mainwidget;
    }

    setFromField();

    return final_widget;
}

void QuMcq::clicked(const int position)
{
    if (!m_options.validIndex(position)) {
        qWarning() << Q_FUNC_INFO << "- out of range";
        return;
    }
    const QVariant newvalue = m_options.valueFromPosition(position);
    const bool changed = m_fieldref->setValue(newvalue);
    // ... Will trigger valueChanged
    if (changed) {
        emit elementValueChanged();
    }
}

void QuMcq::setFromField()
{
    fieldValueChanged(m_fieldref.data());
}

void QuMcq::fieldValueChanged(const FieldRef* fieldref)
{
    mcqfunc::setResponseWidgets(m_options, m_boolean_widgets, fieldref);
}

FieldRefPtrList QuMcq::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}
