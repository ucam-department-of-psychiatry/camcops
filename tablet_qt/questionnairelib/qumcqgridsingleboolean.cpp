#include "qumcqgridsingleboolean.h"
#include <QGridLayout>
#include "widgets/booleanwidget.h"
#include "widgets/labelwordwrapwide.h"
#include "mcqfunc.h"
#include "questionnaire.h"


QuMCQGridSingleBoolean::QuMCQGridSingleBoolean(
        QList<QuestionWithTwoFields> questions_with_fields,
        const NameValueOptions& mcq_options,
        const QString& boolean_text) :
    m_boolean_left(false),
    m_questions_with_fields(questions_with_fields),
    m_mcq_options(mcq_options),
    m_boolean_text(boolean_text),
    m_question_width(-1),
    m_boolean_width(-1),
    m_expand(false)
{
    m_mcq_options.validateOrDie();
    // each QuestionWithTwoFields will have asserted on construction

    for (int qi = 0; qi < m_questions_with_fields.size(); ++qi) {
        FieldRefPtr mcq_fieldref = m_questions_with_fields.at(qi).firstFieldRef();
        connect(mcq_fieldref.data(), &FieldRef::valueChanged,
                std::bind(&QuMCQGridSingleBoolean::mcqFieldValueChanged,
                          this, qi, std::placeholders::_1));
        connect(mcq_fieldref.data(), &FieldRef::mandatoryChanged,
                std::bind(&QuMCQGridSingleBoolean::mcqFieldValueChanged,
                          this, qi, std::placeholders::_1));

        FieldRefPtr bool_fieldref = m_questions_with_fields.at(qi).secondFieldRef();
        connect(bool_fieldref.data(), &FieldRef::valueChanged,
                std::bind(&QuMCQGridSingleBoolean::booleanFieldValueChanged,
                          this, qi, std::placeholders::_1));
        connect(bool_fieldref.data(), &FieldRef::mandatoryChanged,
                std::bind(&QuMCQGridSingleBoolean::booleanFieldValueChanged,
                          this, qi, std::placeholders::_1));
    }
}


QuMCQGridSingleBoolean* QuMCQGridSingleBoolean::setBooleanLeft(
        bool boolean_left)
{
    m_boolean_left = boolean_left;
    return this;
}


QuMCQGridSingleBoolean* QuMCQGridSingleBoolean::setWidth(int question_width,
                                                  QList<int> mcq_option_widths,
                                                  int boolean_width)
{
    if (mcq_option_widths.size() != m_mcq_options.size()) {
        qWarning() << Q_FUNC_INFO << "Bad mcq_option_widths; command ignored";
        return this;
    }
    m_question_width = question_width;
    m_mcq_option_widths = mcq_option_widths;
    m_boolean_width = boolean_width;
    return this;
}


QuMCQGridSingleBoolean* QuMCQGridSingleBoolean::setTitle(const QString &title)
{
    m_title = title;
    return this;
}


QuMCQGridSingleBoolean* QuMCQGridSingleBoolean::setSubtitles(
        QList<McqGridSubtitle> subtitles)
{
    m_subtitles = subtitles;
    return this;
}


QuMCQGridSingleBoolean* QuMCQGridSingleBoolean::setExpand(bool expand)
{
    m_expand = expand;
    return this;
}


void QuMCQGridSingleBoolean::setFromFields()
{
    for (int qi = 0; qi < m_questions_with_fields.size(); ++qi) {
        mcqFieldValueChanged(
                    qi, m_questions_with_fields.at(qi).firstFieldRef().data());
        booleanFieldValueChanged(
                    qi, m_questions_with_fields.at(qi).secondFieldRef().data());
    }
}


int QuMCQGridSingleBoolean::mcqColnum(int value_index) const
{
    return (m_boolean_left ? 4 : 2) + value_index;
}


int QuMCQGridSingleBoolean::booleanColnum() const
{
    return m_boolean_left ? 2 : (3 + m_mcq_options.size());
}


int QuMCQGridSingleBoolean::spacercol(bool first) const
{
    return first ? 1 : ((m_boolean_left ? mcqColnum(0) : booleanColnum()) - 1);
}


void QuMCQGridSingleBoolean::addOptions(QGridLayout* grid, int row)
{
    for (int i = 0; i < m_mcq_options.size(); ++i) {
        McqFunc::addOption(grid, row, mcqColnum(i), m_mcq_options.at(i).name());
    }
    McqFunc::addOption(grid, row, booleanColnum(), m_boolean_text);
}


QPointer<QWidget> QuMCQGridSingleBoolean::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    m_mcq_widgets.clear();
    m_boolean_widgets.clear();

    QGridLayout* grid = new QGridLayout();
    grid->setHorizontalSpacing(UiConst::MCQGRID_HSPACING);
    grid->setVerticalSpacing(UiConst::MCQGRID_VSPACING);

    int n_subtitles = m_subtitles.size();
    int n_rows = 1 + n_subtitles + m_questions_with_fields.size();
    int n_cols = m_mcq_options.size() + 4;
    Qt::Alignment response_align = Qt::AlignCenter | Qt::AlignVCenter;
    int row = 0;
    int n_options = m_mcq_options.size();

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
        QList<QPointer<BooleanWidget>> question_widgets;
        for (int vi = 0; vi < n_options; ++vi) {
            QPointer<BooleanWidget> w = new BooleanWidget();
            w->setAppearance(BooleanWidget::Appearance::Radio);
            w->setReadOnly(read_only);
            if (!read_only) {
                connect(w, &BooleanWidget::clicked,
                        std::bind(&QuMCQGridSingleBoolean::mcqClicked,
                                  this, qi, vi));
            }
            grid->addWidget(w, row, mcqColnum(vi), response_align);
            question_widgets.append(w);
        }
        m_mcq_widgets.append(question_widgets);

        QPointer<BooleanWidget> bw = new BooleanWidget();
        bw->setAppearance(BooleanWidget::Appearance::CheckRed);
        bw->setReadOnly(read_only);
        if (!read_only) {
            connect(bw, &BooleanWidget::clicked,
                    std::bind(&QuMCQGridSingleBoolean::booleanClicked,
                              this, qi));
        }
        grid->addWidget(bw, row, booleanColnum(), response_align);
        m_boolean_widgets.append(bw);

        ++row;  // new row after question/response widgets
    }

    // Set widths, if asked
    if (m_question_width > 0 &&
            m_mcq_option_widths.size() == m_mcq_options.size()) {
        grid->setColumnStretch(0, m_question_width);
        for (int i = 0; i < m_mcq_option_widths.size(); ++i) {
            grid->setColumnStretch(mcqColnum(i), m_mcq_option_widths.at(i));
        }
        grid->setColumnStretch(booleanColnum(), m_boolean_width);
    }

    // Vertical lines
    McqFunc::addVerticalLine(grid, spacercol(true), n_rows);
    McqFunc::addVerticalLine(grid, spacercol(false), n_rows);

    QPointer<QWidget> widget = new QWidget();
    widget->setLayout(grid);
    widget->setObjectName("mcq_grid_single_boolean");
    if (!m_expand) {
        widget->setSizePolicy(QSizePolicy::Maximum, QSizePolicy::Maximum);
    }

    setFromFields();

    return widget;
}


FieldRefPtrList QuMCQGridSingleBoolean::fieldrefs() const
{
    FieldRefPtrList refs;
    for (auto q : m_questions_with_fields) {
        refs.append(q.firstFieldRef());
        refs.append(q.secondFieldRef());
    }
    return refs;
}


void QuMCQGridSingleBoolean::mcqClicked(int question_index, int value_index)
{
    if (question_index < 0 ||
            question_index >= m_questions_with_fields.size()) {
        qWarning() << Q_FUNC_INFO << "Bad question_index:" << question_index;
        return;
    }
    if (!m_mcq_options.validIndex(value_index)) {
        qWarning() << Q_FUNC_INFO << "- out of range";
        return;
    }
    QVariant newvalue = m_mcq_options.value(value_index);
    FieldRefPtr fieldref = m_questions_with_fields.at(question_index)
            .firstFieldRef();
    fieldref->setValue(newvalue);  // Will trigger valueChanged
    emit elementValueChanged();
}


void QuMCQGridSingleBoolean::booleanClicked(int question_index)
{
    if (question_index < 0 ||
            question_index >= m_questions_with_fields.size()) {
        qWarning() << Q_FUNC_INFO << "Bad question_index:" << question_index;
        return;
    }
    FieldRefPtr fieldref = m_questions_with_fields.at(question_index)
            .secondFieldRef();
    McqFunc::toggleBooleanField(fieldref.data());
    emit elementValueChanged();
}


void QuMCQGridSingleBoolean::mcqFieldValueChanged(int question_index,
                                                  const FieldRef* fieldref)
{
    if (question_index < 0 ||
            question_index >= m_questions_with_fields.size() ||
            question_index >= m_mcq_widgets.size()) {
        qWarning() << Q_FUNC_INFO << "Bad question_index:" << question_index;
        return;
    }
    const QList<QPointer<BooleanWidget>>& question_widgets = m_mcq_widgets.at(
                question_index);

    McqFunc::setResponseWidgets(m_mcq_options, question_widgets, fieldref);
}


void QuMCQGridSingleBoolean::booleanFieldValueChanged(int question_index,
                                                      const FieldRef* fieldref)
{
    if (question_index < 0 ||
            question_index >= m_questions_with_fields.size() ||
            question_index >= m_boolean_widgets.size()) {
        qWarning() << Q_FUNC_INFO << "Bad question_index:" << question_index;
        return;
    }
    QPointer<BooleanWidget> bw = m_boolean_widgets.at(question_index);

    bw->setValue(fieldref->value(), fieldref->mandatory());
}
