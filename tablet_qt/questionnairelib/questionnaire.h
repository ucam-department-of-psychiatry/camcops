/*
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

#pragma once

// #define QUESTIONAIRE_USE_HFW_LAYOUT  // bad; contained scroll area gets too short

#include <initializer_list>
#include <QList>
#include <QPointer>
#include <QSharedPointer>
#include "common/aliases_camcops.h"
#include "common/uiconst.h"  // for FontSize
#include "layouts/layouts.h"
#include "questionnairelib/qupage.h"
#include "widgets/openablewidget.h"

class CamcopsApp;
class QuestionnaireHeader;
class QVBoxLayout;
class QWidget;


class Questionnaire : public OpenableWidget
{
    // Master class controlling a questionnaire.

    Q_OBJECT
public:
    // Constructors
    Questionnaire(CamcopsApp& app);
    Questionnaire(CamcopsApp& app, const QVector<QuPagePtr>& pages);
    Questionnaire(CamcopsApp& app, std::initializer_list<QuPagePtr> pages);

    // Information about the questionnaire
    bool readOnly() const;
    int currentPageIndex() const;
    int currentPageNumOneBased() const;
    int nPages() const;

    // Build widgets when the Questionnaire is displayed
    virtual void build() override;

    // Set attributes about the questionnaire
    void setType(QuPage::PageType type);
    void setReadOnly(bool read_only = true);
    void setJumpAllowed(bool jump_allowed = true);
    void setWithinChain(bool within_chain = true);
    void setFinishButtonIcon(const QString& base_filename);
    void setFinishButtonIconToTick();

    // Add pages
    virtual void addPage(const QuPagePtr& page);

    // Get page information
    QuPage* currentPagePtr() const;
    QuPage* pagePtr(int index) const;
    QVector<QuPage*> getPages(bool current_page_only,
                              const QString& page_tag = "");

    // Alter pages
    void setPageSkip(int page, bool skip, bool reset_buttons = true);
    void setPageSkip(const QString& page_tag, bool skip,
                     bool reset_buttons = true);
    virtual void deletePage(int index);
    void movePageBackwards(int index);
    void movePageForwards(int index);

    // Get element information
    QVector<QuElement*> getElementsByTag(const QString& tag,
                                         bool current_page_only = true,
                                         const QString& page_tag = "");
    QuElement* getFirstElementByTag(const QString& tag,
                                    bool current_page_only = true,
                                    const QString& page_tag = "");

    // Alter elements
    void setVisibleByTag(const QString& tag, bool visible,
                         bool current_page_only = true,
                         const QString& page_tag = "");
    void refreshCurrentPage();
    virtual void goToPage(int index, bool allow_refresh = false);
    void debugLayout();

    // Advanced control
    void openSubWidget(OpenableWidget* widget);

    // Utility functions
    CamcopsApp& app() const;
    int fontSizePt(uiconst::FontSize fontsize) const;
    QString getSubstitutedCss(const QString& filename) const;

public slots:
    void resetButtons();

signals:
    void editStarted();
    void editFinished(bool aborted);
    void pageAboutToOpen();  // about to display page
    void cancelled();  // failure/cancel
    void completed();  // success/OK
    // and finished() is emitted with either; see OpenableWidget

protected:
    void commonConstructor();
    virtual void addFirstDynamicPage();
    virtual bool morePagesToGo() const;
    virtual void addAllAccessibleDynamicPages();
    void doFinish();
    void doCancel();
    void pageClosing();
    // Signal handling
    bool event(QEvent* e) override;
    void keyPressEvent(QKeyEvent* event);
    virtual void processNextClicked();
protected slots:
    void cancelClicked();
    void jumpClicked();
    void previousClicked();
    void nextClicked();
    void finishClicked();

protected:
    CamcopsApp& m_app;
    QVector<QuPagePtr> m_pages;
    QuPage::PageType m_type;
    bool m_read_only;
    bool m_jump_allowed;
    bool m_within_chain;

    bool m_built;
#ifdef QUESTIONAIRE_USE_HFW_LAYOUT
    QPointer<VBoxLayout> m_outer_layout;
    QPointer<VBoxLayout> m_mainlayout;
#else
    QPointer<QVBoxLayout> m_outer_layout;
    QPointer<QVBoxLayout> m_mainlayout;
#endif
    QPointer<QWidget> m_background_widget;
    QPointer<QuestionnaireHeader> m_p_header;
    int m_current_page_index;
    QString m_finish_button_icon_base_filename;
};
