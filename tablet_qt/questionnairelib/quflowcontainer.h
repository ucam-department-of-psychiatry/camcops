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

#pragma once
#include "questionnairelib/qusequencecontainerbase.h"

class QuFlowContainer : public QuSequenceContainerBase
{
    // Allows the arrangements of other elements into a horizontal
    // but flowing layout. It uses FlowLayoutHfw (q.v.).

    Q_OBJECT

public:
    // Plain constructor
    QuFlowContainer(QObject* parent = nullptr);

    // Construct and add elements
    QuFlowContainer(
        const QVector<QuElementPtr>& elements, QObject* parent = nullptr
    );
    QuFlowContainer(
        std::initializer_list<QuElementPtr> elements, QObject* parent = nullptr
    );
    QuFlowContainer(
        std::initializer_list<QuElement*> elements, QObject* parent = nullptr
    );

protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire
    ) override;
};
