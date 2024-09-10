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

#include "fontsizeanddpiwindow.h"

#include <QMap>
#include <QString>

#include "common/aliases_camcops.h"
#include "common/varconst.h"
#include "core/camcopsapp.h"
#include "db/fieldref.h"
#include "lib/stringfunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qugridcell.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qulineeditdouble.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/qutext.h"
#include "widgets/openablewidget.h"


const QString TAG_DPI_LOGICAL("dpi_logical");
const QString TAG_DPI_PHYSICAL("dpi_physical");

FontSizeAndDpiWindow::FontSizeAndDpiWindow(CamcopsApp& app) :
    FontSizeWindow(app)
{
    m_dpi_override_logical_fr
        = m_app.storedVarFieldRef(varconst::OVERRIDE_LOGICAL_DPI, false);
    m_dpi_override_logical_x_fr
        = m_app.storedVarFieldRef(varconst::OVERRIDE_LOGICAL_DPI_X, false);
    m_dpi_override_logical_y_fr
        = m_app.storedVarFieldRef(varconst::OVERRIDE_LOGICAL_DPI_Y, false);
    m_dpi_override_physical_fr
        = m_app.storedVarFieldRef(varconst::OVERRIDE_PHYSICAL_DPI, false);
    m_dpi_override_physical_x_fr
        = m_app.storedVarFieldRef(varconst::OVERRIDE_PHYSICAL_DPI_X, false);
    m_dpi_override_physical_y_fr
        = m_app.storedVarFieldRef(varconst::OVERRIDE_PHYSICAL_DPI_Y, false);
}

OpenableWidget* FontSizeAndDpiWindow::editor()
{
    auto questionnaire = FontSizeWindow::editor();

    dpiOverrideChanged();

    return questionnaire;
}

void FontSizeAndDpiWindow::setUpPage(QuPagePtr page)
{
    FontSizeWindow::setUpPage(page);

    // --------------------------------------------------------------------
    // DPI extras
    // --------------------------------------------------------------------
    const QString dpi_heading(tr("DPI settings"));
    const QString dpi_explanation(tr(
        "Dots per inch (DPI), or more accurately pixels per inch (PPI), "
        "are a measure of screen resolution. Higher-resolution monitors have "
        "higher DPI settings. In some circumstances, CamCOPS needs to know "
        "your screen's DPI settings accurately. If your operating system "
        "mis-reports them, you can override the system settings here."
    ));
    const QString dpi_restart(
        tr("These settings take effect when you restart CamCOPS.")
    );

    const QString logical_info(
        tr("Logical DPI settings are used for icon sizes and similar. "
           "You are unlikely to need to override these. "
           "Current system logical DPI:")
        + " " + m_app.qtLogicalDotsPerInch().description()
    );
    const QString override_log(tr("Override system logical DPI settings"));
    const QString override_log_x(tr("Logical DPI, X"));
    const QString override_log_y(tr("Logical DPI, Y"));

    const QString physical_info(
        tr("Physical DPI settings are used for absolute sizes "
           "(e.g. visual analogue scales). Override this for precise scaling "
           "if "
           "your system gets it slightly wrong. Current system physical DPI:")
        + " " + m_app.qtPhysicalDotsPerInch().description()
    );
    const QString override_phy(tr("Override system physical DPI settings"));
    const QString override_phy_x(tr("Physical DPI, X"));
    const QString override_phy_y(tr("Physical DPI, Y"));

    const double dpi_min = 50;
    // ... 67 realistic low end;
    //     https://en.wikipedia.org/wiki/Pixel_density
    const double dpi_max = 4000;
    // ... 3760 has been achieved;
    //     https://en.wikipedia.org/wiki/Pixel_density
    const QString dpi_hint(tr("Dots per inch (DPI), e.g. 96; range %1-%2")
                               .arg(dpi_min)
                               .arg(dpi_max));

    auto dpi_grid = new QuGridContainer();
    dpi_grid->setColumnStretch(0, 1);
    dpi_grid->setColumnStretch(1, 1);
    int row = 0;
    const Qt::Alignment labelalign = Qt::AlignRight | Qt::AlignTop;
    const int dpi_dp = 2;
    const bool dpi_allow_empty = true;
    dpi_grid->addCell(QuGridCell(new QuText(logical_info), row, 0, 1, 2));
    ++row;
    dpi_grid->addCell(QuGridCell(
        (new QuText(stringfunc::makeTitle(override_log)))
            ->setTextAlignment(labelalign),
        row,
        0
    ));
    dpi_grid->addCell(QuGridCell(
        (new QuMcq(m_dpi_override_logical_fr, CommonOptions::yesNoBoolean()))
            ->setHorizontal(true)
            ->setAsTextButton(true),
        row,
        1
    ));
    ++row;
    dpi_grid->addCell(QuGridCell(
        (new QuText(stringfunc::makeTitle(override_log_x)))
            ->setTextAlignment(labelalign)
            ->addTag(TAG_DPI_LOGICAL),
        row,
        0
    ));
    dpi_grid->addCell(QuGridCell(
        (new QuLineEditDouble(
             m_dpi_override_logical_x_fr,
             dpi_min,
             dpi_max,
             dpi_dp,
             dpi_allow_empty
         ))
            ->setHint(dpi_hint)
            ->addTag(TAG_DPI_LOGICAL),
        row,
        1
    ));
    ++row;
    dpi_grid->addCell(QuGridCell(
        (new QuText(stringfunc::makeTitle(override_log_y)))
            ->setTextAlignment(labelalign)
            ->addTag(TAG_DPI_LOGICAL),
        row,
        0
    ));
    dpi_grid->addCell(QuGridCell(
        (new QuLineEditDouble(
             m_dpi_override_logical_y_fr,
             dpi_min,
             dpi_max,
             dpi_dp,
             dpi_allow_empty
         ))
            ->setHint(dpi_hint)
            ->addTag(TAG_DPI_LOGICAL),
        row,
        1
    ));
    ++row;
    // --------------------------------------------------------------------
    dpi_grid->addCell(QuGridCell(new QuText(physical_info), row, 0, 1, 2));
    ++row;
    dpi_grid->addCell(QuGridCell(
        (new QuText(stringfunc::makeTitle(override_phy)))
            ->setTextAlignment(labelalign),
        row,
        0
    ));
    dpi_grid->addCell(QuGridCell(
        (new QuMcq(m_dpi_override_physical_fr, CommonOptions::yesNoBoolean()))
            ->setHorizontal(true)
            ->setAsTextButton(true),
        row,
        1
    ));
    ++row;
    dpi_grid->addCell(QuGridCell(
        (new QuText(stringfunc::makeTitle(override_phy_x)))
            ->setTextAlignment(labelalign)
            ->addTag(TAG_DPI_PHYSICAL),
        row,
        0
    ));
    dpi_grid->addCell(QuGridCell(
        (new QuLineEditDouble(
             m_dpi_override_physical_x_fr,
             dpi_min,
             dpi_max,
             dpi_dp,
             dpi_allow_empty
         ))
            ->setHint(dpi_hint)
            ->addTag(TAG_DPI_PHYSICAL),
        row,
        1
    ));
    ++row;
    dpi_grid->addCell(QuGridCell(
        (new QuText(stringfunc::makeTitle(override_phy_y)))
            ->setTextAlignment(labelalign)
            ->addTag(TAG_DPI_PHYSICAL),
        row,
        0
    ));
    dpi_grid->addCell(QuGridCell(
        (new QuLineEditDouble(
             m_dpi_override_physical_y_fr,
             dpi_min,
             dpi_max,
             dpi_dp,
             dpi_allow_empty
         ))
            ->setHint(dpi_hint)
            ->addTag(TAG_DPI_PHYSICAL),
        row,
        1
    ));

    connect(
        m_dpi_override_logical_fr.data(),
        &FieldRef::valueChanged,
        this,
        &FontSizeAndDpiWindow::dpiOverrideChanged,
        Qt::UniqueConnection
    );
    connect(
        m_dpi_override_physical_fr.data(),
        &FieldRef::valueChanged,
        this,
        &FontSizeAndDpiWindow::dpiOverrideChanged,
        Qt::UniqueConnection
    );

    page->addElements({
        new QuHeading(dpi_heading),
        new QuText(dpi_explanation),
        dpi_grid,
        new QuText(dpi_restart),
    });
}

QString FontSizeAndDpiWindow::getPageTitle()
{
    return tr("Set questionnaire font size and DPI settings");
}

void FontSizeAndDpiWindow::dpiOverrideChanged()
{
    if (!m_fontsize_questionnaire) {
        return;
    }
    const bool logical = m_dpi_override_logical_fr->valueBool();
    m_fontsize_questionnaire->setVisibleByTag(TAG_DPI_LOGICAL, logical);
    m_dpi_override_logical_x_fr->setMandatory(logical);
    m_dpi_override_logical_y_fr->setMandatory(logical);
    const bool physical = m_dpi_override_physical_fr->valueBool();
    m_fontsize_questionnaire->setVisibleByTag(TAG_DPI_PHYSICAL, physical);
    m_dpi_override_physical_x_fr->setMandatory(physical);
    m_dpi_override_physical_y_fr->setMandatory(physical);
}
