#pragma once
#include <QList>
#include <QPair>
#include <QSharedPointer>

class QuElement;
using QuElementPtr = QSharedPointer<QuElement>;
using GridRowDefinition = QPair<QString, QuElementPtr>;
using GridRowDefinitionRawPtr = QPair<QString, QuElement*>;
class QuGridCell;


namespace QuestionnaireFunc {

    // Make default grids: convenience functions for grid creation.
    // These functions take {string, element} pairs and make a grid like:
    //
    //              label1      element1
    //              label2      element2

    QuElement* defaultGridRawPointer(
        const QList<GridRowDefinition>& deflist,
        int left_column_span = 1,
        int right_column_span = 1,
        Qt::Alignment label_alignment = Qt::AlignRight | Qt::AlignTop,
        Qt::Alignment left_column_alignment = 0,
        Qt::Alignment right_column_alignment = 0);
    QuElementPtr defaultGrid(
        const QList<GridRowDefinition>& deflist,
        int left_column_span = 1,
        int right_column_span = 1,
        Qt::Alignment label_alignment = Qt::AlignRight | Qt::AlignTop,
        Qt::Alignment left_column_alignment = 0,
        Qt::Alignment right_column_alignment = 0);
    QuElementPtr defaultGrid(
        std::initializer_list<GridRowDefinition> defs,
        int left_column_span = 1,
        int right_column_span = 1,
        Qt::Alignment label_alignment = Qt::AlignRight | Qt::AlignTop,
        Qt::Alignment left_column_alignment = 0,
        Qt::Alignment right_column_alignment = 0);
    QuElement* defaultGridRawPointer(
        std::initializer_list<GridRowDefinitionRawPtr> defs,
        int left_column_span = 1,
        int right_column_span = 1,
        Qt::Alignment label_alignment = Qt::AlignRight | Qt::AlignTop,
        Qt::Alignment left_column_alignment = 0,
        Qt::Alignment right_column_alignment = 0);
}

// If you don't specify an alignment, the default behaviour of QGridLayout is
// to stretch the widget to the cell, which is generally good.
// If you specify an alignment like Qt::AlignRight | Qt::AlignTop, the widget
// "floats" within its grid cell (and is then aligned as you ask). This can
// make the widget look too small.
// To align text right *within* its widget is a different question.
