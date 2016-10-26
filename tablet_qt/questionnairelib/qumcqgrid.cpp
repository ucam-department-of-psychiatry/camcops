#include "qumcqgrid.h"
#include <QGridLayout>
#include "questionnairelib/mcqfunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/booleanwidget.h"
#include "widgets/labelwordwrapwide.h"


QuMCQGrid::QuMCQGrid(QList<QuestionWithOneField> question_field_pairs,
                     const NameValueOptions& options) :
    m_question_field_pairs(question_field_pairs),
    m_options(options),
    m_question_width(-1),
    m_expand(false)
{
    m_options.validateOrDie();
    // each QuestionWithOneField will have asserted on construction

    for (int qi = 0; qi < m_question_field_pairs.size(); ++qi) {
        FieldRefPtr fieldref = m_question_field_pairs.at(qi).fieldref();
        connect(fieldref.data(), &FieldRef::valueChanged,
                std::bind(&QuMCQGrid::fieldValueChanged, this, qi,
                          std::placeholders::_1));
        connect(fieldref.data(), &FieldRef::mandatoryChanged,
                std::bind(&QuMCQGrid::fieldValueChanged, this, qi,
                          std::placeholders::_1));
    }
}


QuMCQGrid* QuMCQGrid::setWidth(int question_width, QList<int> option_widths)
{
    if (option_widths.size() != m_options.size()) {
        qWarning() << Q_FUNC_INFO << "Bad option_widths; command ignored";
        return this;
    }
    m_question_width = question_width;
    m_option_widths = option_widths;
    return this;
}


QuMCQGrid* QuMCQGrid::setTitle(const QString &title)
{
    m_title = title;
    return this;
}


QuMCQGrid* QuMCQGrid::setSubtitles(QList<McqGridSubtitle> subtitles)
{
    m_subtitles = subtitles;
    return this;
}


QuMCQGrid* QuMCQGrid::setExpand(bool expand)
{
    m_expand = expand;
    return this;
}


void QuMCQGrid::setFromFields()
{
    for (int qi = 0; qi < m_question_field_pairs.size(); ++qi) {
        fieldValueChanged(qi, m_question_field_pairs.at(qi).fieldref().data());
    }
}


int QuMCQGrid::colnum(int value_index) const
{
    return 2 + value_index;
}


void QuMCQGrid::addOptions(QGridLayout* grid, int row)
{
    for (int i = 0; i < m_options.size(); ++i) {
        McqFunc::addOption(grid, row, colnum(i),
                               m_options.at(i).name());
    }
}


QPointer<QWidget> QuMCQGrid::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    m_widgets.clear();

    /*
    - Labels, by default, have their text contents left-aligned and vertically
      centred. Use label->setAlignment().
      http://doc.qt.io/qt-5/qlabel.html#alignment-prop
    - That's fine for everything except headers, which we'd like bottom
      alignment for.
    - And top alignment for the main title.
    */

    QGridLayout* grid = new QGridLayout();
    grid->setHorizontalSpacing(UiConst::MCQGRID_HSPACING);
    grid->setVerticalSpacing(UiConst::MCQGRID_VSPACING);

    int n_subtitles = m_subtitles.size();
    int n_options = m_options.size();
    int n_rows = 1 + n_subtitles + m_question_field_pairs.size();
    int n_cols = m_options.size() + 2;
    Qt::Alignment response_align = McqFunc::response_widget_align;
    int row = 0;

    // First column: titles, subtitles, questions
    // Second and subsequent columns: options

    // Title row
    McqFunc::addOptionBackground(grid, row, 0, n_cols);
    McqFunc::addTitle(grid, row, m_title);
    addOptions(grid, row);
    ++row;  // new row after title/option text

    // Main question rows (with any preceding subtitles)
    // qi: question index
    // s: subtitle index
    // vi: value index
    for (int qi = 0; qi < m_question_field_pairs.size(); ++qi) {

        // Any preceding subtitles?
        for (int s = 0; s < n_subtitles; ++s) {
            const McqGridSubtitle& sub = m_subtitles.at(s);
            if (sub.pos() == qi) {
                // Yes. Add a subtitle row.
                McqFunc::addOptionBackground(grid, row, 0, n_cols);
                McqFunc::addSubtitle(grid, row, sub.string());
                if (sub.repeatOptions()) {
                    addOptions(grid, row);
                }
                ++row;  // new row after subtitle
            }
        }

        // The question
        McqFunc::addQuestion(grid, row,
                                 m_question_field_pairs.at(qi).question());

        // The response widgets
        QList<QPointer<BooleanWidget>> question_widgets;
        for (int vi = 0; vi < n_options; ++vi) {
            QPointer<BooleanWidget> w = new BooleanWidget();
            w->setAppearance(BooleanWidget::Appearance::Radio);
            w->setReadOnly(read_only);
            if (!read_only) {
                connect(w, &BooleanWidget::clicked,
                        std::bind(&QuMCQGrid::clicked, this, qi, vi));
            }
            grid->addWidget(w, row, colnum(vi), response_align);
            question_widgets.append(w);
        }
        m_widgets.append(question_widgets);

        ++row;  // new row after question/response widgets
    }

    // Set widths, if asked
    if (m_question_width > 0 && m_option_widths.size() == m_options.size()) {
        grid->setColumnStretch(0, m_question_width);
        for (int i = 0; i < n_options; ++i) {
            grid->setColumnStretch(colnum(i), m_option_widths.at(i));
        }
    }

    // Vertical lines
    McqFunc::addVerticalLine(grid, 1, n_rows);

    QPointer<QWidget> widget = new QWidget();
    widget->setLayout(grid);
    widget->setObjectName("mcq_grid");
    if (m_expand) {
        widget->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Maximum);
    } else {
        widget->setSizePolicy(QSizePolicy::Maximum, QSizePolicy::Maximum);
    }

    setFromFields();

    return widget;
}


FieldRefPtrList QuMCQGrid::fieldrefs() const
{
    FieldRefPtrList refs;
    for (auto q : m_question_field_pairs) {
        refs.append(q.fieldref());
    }
    return refs;
}


void QuMCQGrid::clicked(int question_index, int value_index)
{
    if (question_index < 0 || question_index >= m_question_field_pairs.size()) {
        qWarning() << Q_FUNC_INFO << "Bad question_index:" << question_index;
        return;
    }
    if (!m_options.validIndex(value_index)) {
        qWarning() << Q_FUNC_INFO << "- out of range";
        return;
    }
    QVariant newvalue = m_options.value(value_index);
    FieldRefPtr fieldref = m_question_field_pairs.at(question_index).fieldref();
    fieldref->setValue(newvalue);  // Will trigger valueChanged
    emit elementValueChanged();
}


void QuMCQGrid::fieldValueChanged(int question_index, const FieldRef* fieldref)
{
    if (question_index < 0 ||
            question_index >= m_question_field_pairs.size() ||
            question_index >= m_widgets.size()) {
        qWarning() << Q_FUNC_INFO << "Bad question_index:" << question_index;
        return;
    }
    const QList<QPointer<BooleanWidget>>& question_widgets = m_widgets.at(
                question_index);

    McqFunc::setResponseWidgets(m_options, question_widgets, fieldref);
}
