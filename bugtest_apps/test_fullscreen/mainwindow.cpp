#include "mainwindow.h"
#include <QDebug>
#include <QStackedWidget>
#include <QVector>


const QVector<QPair<QString, bool>> WIDGET_DEFINITIONS{
    {"one, doesn't want fullscreen", false},
    {"two, wants fullscreen", true},
};


MainWindow::MainWindow(QWidget* parent) :
    QMainWindow(parent)
{
    m_p_hidden_stack = new QStackedWidget();  // no parent
    m_p_visible_stack = new QStackedWidget(this);
    setCentralWidget(m_p_visible_stack);

    for (auto text_fullscreen : WIDGET_DEFINITIONS) {
        const QString& text = text_fullscreen.first;
        const bool fullscreen = text_fullscreen.second;
        qDebug() << "Adding widget with text" << text
                 << "and fullscreen" << fullscreen;
        DisplayWidget* w = new DisplayWidget(text, fullscreen);
        openWidget(w);
    }
}


void MainWindow::openWidget(DisplayWidget* dw)
{
    // Connect widget signal
    connect(dw, &DisplayWidget::pleaseClose,
            this, &MainWindow::closeTopWidget);

    // Transfer any visible items (should be 0 or 1 of them!) to hidden stack
    while (m_p_visible_stack->count() > 0) {
        DisplayWidget* w = reinterpret_cast<DisplayWidget*>(
                    m_p_visible_stack->widget(m_p_visible_stack->count() - 1));
        if (w) {
            qDebug() << "Moving from visible to hidden:" << w->m_text;
            m_p_visible_stack->removeWidget(w);  // m_p_visible_stack still owns w
            m_p_hidden_stack->addWidget(w);  // m_p_hidden_stack now owns w
        }
    }

    int index = m_p_visible_stack->addWidget(dw);
    m_p_visible_stack->setCurrentIndex(index);
    // ... the stack takes over ownership.

    // Set the fullscreen state if the new widget wants it
    if (dw->m_fullscreen) {
        showFullScreen();
    }

    update();
}


void MainWindow::closeTopWidget()
{
    // Get rid of the top widget
    DisplayWidget* closing_widget = reinterpret_cast<DisplayWidget*>(
                m_p_visible_stack->currentWidget());
    qDebug() << "Closing widget with text" << closing_widget->m_text;
    m_p_visible_stack->removeWidget(closing_widget);
    closing_widget->deleteLater();

    // Restore the widget from the top of the hidden stack
    const int n_left = m_p_hidden_stack->count();
    if (n_left == 0) {
        qDebug() << "All widgets closed; closing window and exiting application";
        close();
        return;
    }
    DisplayWidget* opening_widget = reinterpret_cast<DisplayWidget*>(
                m_p_hidden_stack->widget(n_left - 1));
    qDebug() << "Moving from hidden to visible:" << opening_widget->m_text;
    m_p_hidden_stack->removeWidget(opening_widget);  // m_p_hidden_stack still owns opening_widget
    const int index = m_p_visible_stack->addWidget(opening_widget);  // m_p_window_stack now owns opening_widget
    m_p_visible_stack->setCurrentIndex(index);

    // Should we be leaving fullscreen mode?
    bool remaining_widget_wants_fullscreen = false;
    for (int i = 0; i < n_left; ++i) {
        DisplayWidget* dw = reinterpret_cast<DisplayWidget*>(m_p_visible_stack->widget(i));
        if (dw->m_fullscreen) {
            remaining_widget_wants_fullscreen = true;
            break;
        }
    }

    // Now the critical bit:
    if (!remaining_widget_wants_fullscreen) {
        showNormal();
    }
}
