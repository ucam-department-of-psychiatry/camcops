#include "qumcqgriddouble.h"
#include <QGridLayout>
#include "widgets/booleanwidget.h"
#include "widgets/labelwordwrapwide.h"
#include "mcqfunc.h"
#include "questionnaire.h"


QuMCQGridDouble::QuMCQGridDouble(
        QList<QuestionWithTwoFields> questions_with_fields,
        const NameValueOptions& options1,
        const NameValueOptions& options2) :
    m_questions_with_fields(questions_with_fields),
    m_options1(options1),
    m_options2(options2),
    m_question_width(-1),
    m_expand(false)
{
    m_options1.validateOrDie();
    m_options2.validateOrDie();
    // each QuestionWithTwoFields will have asserted on construction

    for (bool first : {true, false}) {
        for (int qi = 0; qi < m_questions_with_fields.size(); ++qi) {
            FieldRefPtr fieldref = m_questions_with_fields.at(qi).fieldref(first);
            connect(fieldref.data(), &FieldRef::valueChanged,
                    std::bind(&QuMCQGridDouble::fieldValueChanged,
                              this, qi, first, std::placeholders::_1));
            connect(fieldref.data(), &FieldRef::mandatoryChanged,
                    std::bind(&QuMCQGridDouble::fieldValueChanged,
                              this, qi, first, std::placeholders::_1));
        }
    }
}


QuMCQGridDouble* QuMCQGridDouble::setWidth(int question_width,
                                           QList<int> option1_widths,
                                           QList<int> option2_widths)
{
    if (option1_widths.size() != m_options1.size()) {
        qWarning() << Q_FUNC_INFO << "Bad option1_widths; command ignored";
        return this;
    }
    if (option2_widths.size() != m_options2.size()) {
        qWarning() << Q_FUNC_INFO << "Bad option2_widths; command ignored";
        return this;
    }
    m_question_width = question_width;
    m_option1_widths = option1_widths;
    m_option2_widths = option2_widths;
    return this;
}


QuMCQGridDouble* QuMCQGridDouble::setTitle(const QString &title)
{
    m_title = title;
    return this;
}


QuMCQGridDouble* QuMCQGridDouble::setSubtitles(QList<McqGridSubtitle> subtitles)
{
    m_subtitles = subtitles;
    return this;
}


QuMCQGridDouble* QuMCQGridDouble::setExpand(bool expand)
{
    m_expand = expand;
    return this;
}


void QuMCQGridDouble::setFromFields()
{
    for (bool first : {true, false}) {
        for (int qi = 0; qi < m_questions_with_fields.size(); ++qi) {
            fieldValueChanged(
                        qi, first,
                        m_questions_with_fields.at(qi).fieldref(first).data());
        }
    }
}


int QuMCQGridDouble::colnum(bool first_field, int value_index) const
{
    // See below
    int base = first_field ? 2 : (3 + m_options1.size());
    return base + value_index;
}


int QuMCQGridDouble::spacercol(bool first_field) const
{
    return first_field ? 1 : (2 + m_options1.size());
}


void QuMCQGridDouble::addOptions(QGridLayout* grid, int row)
{
    for (bool first_field : {true, false}) {
        const NameValueOptions& opts = first_field ? m_options1 : m_options2;
        for (int i = 0; i < opts.size(); ++i) {
            McqFunc::addOption(grid, row, colnum(first_field, i),
                                   opts.at(i).name());
        }
    }
}


QPointer<QWidget> QuMCQGridDouble::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    m_widgets1.clear();
    m_widgets2.clear();

    // As per QuMCQGrid

    QGridLayout* grid = new QGridLayout();
    grid->setHorizontalSpacing(UiConst::MCQGRID_HSPACING);
    grid->setVerticalSpacing(UiConst::MCQGRID_VSPACING);

    int n_subtitles = m_subtitles.size();
    int n_rows = 1 + n_subtitles + m_questions_with_fields.size();
    int n_cols = m_options1.size() + m_options2.size() + 3;
    Qt::Alignment response_align = Qt::AlignCenter | Qt::AlignVCenter;
    int row = 0;

    // First column: titles, subtitles, questions
    // Then vertical break
    // Then m_options1
    // Then vertical break
    // Then m_options2

    // I note in passing:
    // http://stackoverflow.com/questions/25101085/style-sheet-is-appliped-to-the-cells-in-qgridlayout-instead-of-the-parent-contai

    // Title row
    McqFunc::addOptionBackground(grid, row, 0, n_cols);
    McqFunc::addTitle(grid, row, m_title);
    addOptions(grid, row);
    ++row;  // new row after title/option text

    // Main question rows (with any preceding subtitles)
    for (int qi = 0; qi < m_questions_with_fields.size(); ++qi) {

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
                                 m_questions_with_fields.at(qi).question());

        // The response widgets
        for (bool first : {true, false}) {
            const NameValueOptions& opts = first ? m_options1 : m_options2;
            int n_options = opts.size();
            QList<QList<QPointer<BooleanWidget>>>& widgets =
                    first ? m_widgets1 : m_widgets2;
            QList<QPointer<BooleanWidget>> question_widgets;
            for (int vi = 0; vi < n_options; ++vi) {
                QPointer<BooleanWidget> w = new BooleanWidget();
                w->setAppearance(BooleanWidget::Appearance::Radio);
                w->setReadOnly(read_only);
                if (!read_only) {
                    connect(w, &BooleanWidget::clicked,
                            std::bind(&QuMCQGridDouble::clicked,
                                      this, qi, first, vi));
                }
                grid->addWidget(w, row, colnum(first, vi), response_align);

                question_widgets.append(w);
            }
            widgets.append(question_widgets);
        }

        ++row;  // new row after question/response widgets
    }

    // Set widths, if asked
    if (m_question_width > 0 &&
            m_option1_widths.size() == m_options1.size() &&
            m_option2_widths.size() == m_options2.size()) {
        grid->setColumnStretch(0, m_question_width);
        for (bool first : {true, false}) {
            QList<int>& widths = first ? m_option1_widths : m_option2_widths;
            for (int i = 0; i < widths.size(); ++i) {
                grid->setColumnStretch(colnum(first, i), widths.at(i));
            }
        }
    }

    // Vertical lines
    McqFunc::addVerticalLine(grid, spacercol(true), n_rows);
    McqFunc::addVerticalLine(grid, spacercol(false), n_rows);

    QPointer<QWidget> widget = new QWidget();
    widget->setLayout(grid);
    widget->setObjectName("mcq_grid_double");
    if (!m_expand) {
        widget->setSizePolicy(QSizePolicy::Maximum, QSizePolicy::Maximum);
    }

    setFromFields();

    return widget;
}


FieldRefPtrList QuMCQGridDouble::fieldrefs() const
{
    FieldRefPtrList refs;
    for (auto q : m_questions_with_fields) {
        refs.append(q.firstFieldRef());
        refs.append(q.secondFieldRef());
    }
    return refs;
}


void QuMCQGridDouble::clicked(int question_index, bool first_field,
                              int value_index)
{
    const NameValueOptions& opts = first_field ? m_options1 : m_options2;
    if (question_index < 0 ||
            question_index >= m_questions_with_fields.size()) {
        qWarning() << Q_FUNC_INFO << "Bad question_index:" << question_index;
        return;
    }
    if (!opts.validIndex(value_index)) {
        qWarning() << Q_FUNC_INFO << "- out of range";
        return;
    }
    QVariant newvalue = opts.value(value_index);
    FieldRefPtr fieldref = m_questions_with_fields.at(question_index)
            .fieldref(first_field);
    bool changed = fieldref->setValue(newvalue);  // Will trigger valueChanged
    if (changed) {
        emit elementValueChanged();
    }
}


void QuMCQGridDouble::fieldValueChanged(int question_index, bool first_field,
                                        const FieldRef* fieldref)
{
    const NameValueOptions& opts = first_field ? m_options1 : m_options2;
    QList<QList<QPointer<BooleanWidget>>>& widgets = first_field ? m_widgets1
                                                                 : m_widgets2;
    if (question_index < 0 ||
            question_index >= m_questions_with_fields.size() ||
            question_index >= widgets.size()) {
        qWarning() << Q_FUNC_INFO << "Bad question_index:" << question_index;
        return;
    }
    const QList<QPointer<BooleanWidget>>& question_widgets = widgets.at(
                question_index);

    McqFunc::setResponseWidgets(opts, question_widgets, fieldref);
}
