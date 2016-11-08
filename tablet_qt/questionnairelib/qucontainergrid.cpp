// #define DEBUG_GRID_CREATION

#include "qucontainergrid.h"
#include <QDebug>
#include <QGridLayout>
#include <QWidget>
#ifdef DEBUG_GRID_CREATION
#include "common/cssconst.h"
#endif
#include "questionnairelib/questionnaire.h"
#include "lib/layoutdumper.h"


/*

MAKING COLUMN WIDTHS EQUAL

-   Prototypical problem with QGridLayout:

    widget1: fixed          widget2: expanding
    setColumnStretch(1)     setColumnStretch(1)
    |--------------------|  |---------------------------------------------|

    ... same stretch, different widths.
    I think that QGridLayout stretches any *spare* in proportion to
    setColumnStretch.

    http://doc.qt.io/qt-5.7/qgridlayout.html#details

    ... "If you want two columns to have the same width, you must set their
    minimum widths and stretch factors to be the same yourself. You do this
    using setColumnMinimumWidth() and setColumnStretch()."

What does not work properly:

-   widget->setMinimumWidth(1);
    grid->setColumnStretch(column, 1);

-   Encapsulating widget/layout so we can add a stretch, in case (for
    example) our left-hand cells have widgets with horizontal size
    policy Maximum, and the right-hand cells have Expanding; then the
    widgets' policies override our desired grid setColumnStretch()
    parameters.
        QWidget* cell_widget = new QWidget();
        QHBoxLayout* cell_layout = new QHBoxLayout();
        cell_layout->setContentsMargins(UiConst::NO_MARGINS);
        cell_widget->setLayout(cell_layout);
        QPointer<QWidget> w = e->widget(questionnaire);
        cell_layout->addWidget(w);
        cell_layout->addStretch();
        // ... then add the layout to the grid

-   Setting widget's size policy like:

        QSizePolicy sp = w->sizePolicy();
        sp.setHorizontalStretch(1);
        w->setSizePolicy(sp);

    Compare https://stackoverflow.com/questions/27808440/how-to-make-qt-grid-layout-auto-size-column-widths
    ... not sure you can just modify the returned size policy directly, though!
    sizePolicy() returns QSizePolicy, not a reference or pointer.

-   Notes:

    -   QGridLayoutPrivate::addData uses the widget's
        horizontalStretch() [via QGridBox::hStretch()] only if no grid column
        stretch is applied.

-   What does work:

    // force widget's horizontal size policy to expanding
    grid->setColumnMinimumWidth(1);
    grid->setColumnStretch(1);

*/


QuContainerGrid::QuContainerGrid()
{
    commonConstructor();
}


QuContainerGrid::QuContainerGrid(const QList<QuGridCell>& cells) :
    m_cells(cells)
{
    commonConstructor();
}


QuContainerGrid::QuContainerGrid(std::initializer_list<QuGridCell> cells) :
    m_cells(cells)
{
    commonConstructor();
}


void QuContainerGrid::commonConstructor()
{
    m_fixed_grid = true;
}


QuContainerGrid* QuContainerGrid::addCell(const QuGridCell& cell)
{
    m_cells.append(cell);
    return this;
}


QuContainerGrid* QuContainerGrid::setColumnStretch(int column, int stretch)
{
    m_column_stretch[column] = stretch;
    return this;
}


QuContainerGrid* QuContainerGrid::setFixedGrid(bool fixed_grid)
{
    m_fixed_grid = fixed_grid;
    return this;
}


QPointer<QWidget> QuContainerGrid::makeWidget(Questionnaire* questionnaire)
{
    QPointer<QWidget> widget = new QWidget();
#ifdef DEBUG_GRID_CREATION
    qDebug() << Q_FUNC_INFO;
    qDebug() << "... m_fixed_grid =" << m_fixed_grid;
    widget->setObjectName(CssConst::DEBUG_GREEN);
#endif
    QGridLayout* grid = new QGridLayout();
    grid->setContentsMargins(UiConst::NO_MARGINS);
    widget->setLayout(grid);
    for (auto c : m_cells) {
        QuElementPtr e = c.element;
        QPointer<QWidget> w = e->widget(questionnaire);

#ifdef DEBUG_GRID_CREATION
        w->setObjectName(CssConst::DEBUG_RED);
        qDebug() << "... cell:" << c;
#endif
        if (m_fixed_grid) {
            // Set widget to horizontal expanding
            QSizePolicy sp = w->sizePolicy();
            sp.setHorizontalPolicy(QSizePolicy::Expanding);
            w->setSizePolicy(sp);

            // Set column minimum width, and column stretch (may be modified
            // below).
            grid->setColumnMinimumWidth(c.column, 1);
            grid->setColumnStretch(c.column, 1);
        }
#ifdef DEBUG_GRID_CREATION
        {
            QSizePolicy sp = w->sizePolicy();
            qDebug().noquote() << "... ... widget sizePolicy():"
                               << LayoutDumper::toString(sp);
        }
#endif
        grid->addWidget(w, c.row, c.column,
                        c.row_span, c.column_span, c.alignment);
    }
    QMapIterator<int, int> it(m_column_stretch);
    while (it.hasNext()) {
        it.next();
        int column = it.key();
        int stretch = it.value();
#ifdef DEBUG_GRID_CREATION
        qDebug().nospace() << "... setColumnStretch(" << column
                           << "," << stretch << ")";
#endif
        grid->setColumnStretch(column, stretch);
    }

    return widget;
}


QList<QuElementPtr> QuContainerGrid::subelements() const
{
    QList<QuElementPtr> elements;
    for (auto cell : m_cells) {
        elements.append(cell.element);
    }
    return elements;
}
