#include "htmlinfowindow.h"
#include <QLabel>
#include <QTextBrowser>
#include <QVBoxLayout>
#include "common/camcopsapp.h"
#include "common/cssconst.h"
#include "lib/filefunc.h"
#include "menulib/menuheader.h"
#include "widgets/labelwordwrapwide.h"

// http://doc.qt.io/qt-5/qtextbrowser.html


HtmlInfoWindow::HtmlInfoWindow(CamcopsApp& app, const QString& title,
                               const QString& filename, const QString& icon,
                               bool fullscreen) :
    m_app(app)
{
    setStyleSheet(m_app.getSubstitutedCss(UiConst::CSS_CAMCOPS_MENU));
    setObjectName(CssConst::MENU_WINDOW_OUTER_OBJECT);

    // Layouts
    QVBoxLayout* mainlayout = new QVBoxLayout();

    QVBoxLayout* dummy_layout = new QVBoxLayout();
    dummy_layout->setContentsMargins(UiConst::NO_MARGINS);
    setLayout(dummy_layout);
    QWidget* dummy_widget = new QWidget();
    dummy_widget->setObjectName(CssConst::MENU_WINDOW_BACKGROUND);
    dummy_layout->addWidget(dummy_widget);
    dummy_widget->setLayout(mainlayout);

    // Header
    MenuHeader* header = new MenuHeader(this, m_app, false, title, icon);
    mainlayout->addWidget(header);
    connect(header, &MenuHeader::backClicked,
            this, &HtmlInfoWindow::finished);

    // HTML
    if (FileFunc::fileExists(filename)) {
        QString html = FileFunc::textfileContents(filename);
        QTextBrowser* browser = new QTextBrowser();
        browser->setHtml(html);
        browser->setOpenExternalLinks(true);
        mainlayout->addWidget(browser);
        // It manages scrolling itself.
    } else {
        QLabel* label = new LabelWordWrapWide(tr("No such file") + ": " +
                                              filename);
        label->setObjectName(CssConst::WARNING);
        mainlayout->addWidget(label);
        mainlayout->addStretch();
    }

    // Fullscreen?
    setWantsFullscreen(fullscreen);
}
