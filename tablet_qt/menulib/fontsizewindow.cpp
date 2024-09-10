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

#include "fontsizewindow.h"

#include <QMap>
#include <QString>

#include "common/aliases_camcops.h"
#include "common/uiconst.h"
#include "common/varconst.h"
#include "core/camcopsapp.h"
#include "db/fieldref.h"
#include "lib/stringfunc.h"
#include "questionnairelib/qubutton.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/quslider.h"
#include "questionnairelib/qutext.h"
#include "widgets/openablewidget.h"


// For font size settings:
const QString TAG_NORMAL("Normal");
const QString TAG_BIG("Big");
const QString TAG_HEADING("Heading");
const QString TAG_TITLE("Title");
const QString TAG_MENUS("Menus");
const QString alphabet(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ "
    "abcdefghijklmnopqrstuvwxyz "
    "0123456789"
);
const QMap<QString, uiconst::FontSize> FONT_SIZE_MAP{
    {TAG_NORMAL, uiconst::FontSize::Normal},
    {TAG_BIG, uiconst::FontSize::Big},
    {TAG_HEADING, uiconst::FontSize::Heading},
    {TAG_TITLE, uiconst::FontSize::Title},
    {TAG_MENUS, uiconst::FontSize::Menus},
};

FontSizeWindow::FontSizeWindow(CamcopsApp& app) :
    m_app(app),
    m_fontsize_questionnaire(nullptr)
{
    m_fontsize_fr
        = m_app.storedVarFieldRef(varconst::QUESTIONNAIRE_SIZE_PERCENT, true);
}

OpenableWidget* FontSizeWindow::editor()
{
    // ------------------------------------------------------------------------
    // Font size
    // ------------------------------------------------------------------------

    const int fs_min = 70;
    const int fs_max = 300;
    const int fs_slider_step = 1;
    const int fs_slider_tick_interval = 10;
    QMap<int, QString> ticklabels;
    for (int i = fs_min; i <= fs_max; i += fs_slider_tick_interval) {
        ticklabels[i] = QString("%1").arg(i);
    }

    const QString font_heading(tr("Questionnaire font size"));
    const QString font_prompt1(
        tr("Set the font size, as a percentage of the default.")
    );
    const QString font_explan(
        tr("Changes take effect when a screen is reloaded.")
    );
    const QString font_prompt2(tr("You can type it in:"));
    const QString font_prompt3(tr("... or set it with a slider:"));

    QuPagePtr page(new QuPage{
        new QuHeading(font_heading),
        new QuText(stringfunc::makeTitle(font_prompt1)),
        new QuText(font_explan),
        questionnairefunc::defaultGridRawPointer(
            {
                {font_prompt2,
                 new QuLineEditInteger(m_fontsize_fr, fs_min, fs_max)},
            },
            1,
            1
        ),
        new QuText(font_prompt3),
        (new QuSlider(m_fontsize_fr, fs_min, fs_max, fs_slider_step))
            ->setTickInterval(fs_slider_tick_interval)
            ->setTickPosition(QSlider::TicksBothSides)
            ->setTickLabels(ticklabels)
            ->setTickLabelPosition(QSlider::TicksAbove),
        new QuButton(
            tr("Reset to 100%"),
            [this]() {
                resetFontSize();
            }
        ),
        (new QuText(demoText(TAG_NORMAL, uiconst::FontSize::Normal)))
            ->addTag(TAG_NORMAL),
        (new QuText(demoText(TAG_BIG, uiconst::FontSize::Big)))
            ->addTag(TAG_BIG),
        (new QuText(demoText(TAG_HEADING, uiconst::FontSize::Heading)))
            ->addTag(TAG_HEADING),
        (new QuText(demoText(TAG_TITLE, uiconst::FontSize::Title)))
            ->addTag(TAG_TITLE),
        (new QuText(demoText(TAG_MENUS, uiconst::FontSize::Menus)))
            ->addTag(TAG_MENUS),
    });

    connect(
        m_fontsize_fr.data(),
        &FieldRef::valueChanged,
        this,
        &FontSizeWindow::fontSizeChanged,
        Qt::UniqueConnection
    );

    setUpPage(page);
    // ------------------------------------------------------------------------
    // Final setup
    // ------------------------------------------------------------------------

    m_fontsize_questionnaire = new Questionnaire(m_app, {page});
    m_fontsize_questionnaire->setFinishButtonIconToTick();
    connect(
        m_fontsize_questionnaire,
        &Questionnaire::completed,
        this,
        &FontSizeWindow::fontSettingsSaved
    );
    connect(
        m_fontsize_questionnaire,
        &Questionnaire::cancelled,
        this,
        &FontSizeWindow::fontSettingsCancelled
    );
    connect(
        m_fontsize_questionnaire,
        &Questionnaire::pageAboutToOpen,
        this,
        &FontSizeWindow::fontSizeChanged
    );

    return m_fontsize_questionnaire;
}

void FontSizeWindow::setUpPage(QuPagePtr page)
{
    page->setTitle(getPageTitle());
    page->setType(QuPage::PageType::Config);
}

QString FontSizeWindow::getPageTitle()
{
    return tr("Set questionnaire font size");
}

void FontSizeWindow::resetFontSize()
{
    if (!m_fontsize_fr) {
        return;
    }
    m_fontsize_fr->setValue(100);
}

void FontSizeWindow::fontSizeChanged()
{
    // Slightly nasty code.
    if (!m_fontsize_questionnaire || !m_fontsize_fr) {
        return;
    }
    QuPage* page = m_fontsize_questionnaire->currentPagePtr();
    if (!page) {
        return;
    }
    const double current_pct = m_fontsize_fr->valueDouble();
    QMapIterator<QString, uiconst::FontSize> i(FONT_SIZE_MAP);
    while (i.hasNext()) {
        i.next();
        QString tag = i.key();
        uiconst::FontSize fontsize_type = i.value();
        for (auto e : page->elementsWithTag(tag)) {
            int fontsize_pt = m_app.fontSizePt(fontsize_type, current_pct);
            QString text = demoText(tag, fontsize_type);
            // Here's the slightly nasty bit:
            QuText* textelement = dynamic_cast<QuText*>(e);
            if (!textelement) {
                continue;
            }
            textelement->forceFontSize(fontsize_pt, false);
            textelement->setText(text);
        }
    }
}

void FontSizeWindow::fontSettingsSaved()
{
    m_app.saveCachedVars();
    m_fontsize_questionnaire = nullptr;
    // Trigger reloading of reload CSS to SettingsMenu and MainMenu:
    m_app.fontSizeChanged();
}

void FontSizeWindow::fontSettingsCancelled()
{
    m_app.clearCachedVars();
    m_fontsize_questionnaire = nullptr;
}

QString FontSizeWindow::demoText(
    const QString& text, const uiconst::FontSize fontsize_type
) const
{
    if (!m_fontsize_fr) {
        return "?";
    }
    const double current_pct = m_fontsize_fr->valueDouble();
    const int font_size_pt = m_app.fontSizePt(fontsize_type, current_pct);
    return QString("%1 [%2 pt] %3")
        .arg(tr(qPrintable(text)))
        .arg(font_size_pt)
        .arg(alphabet);
}
