#pragma once
#include <QLabel>


class ClickableLabel : public QLabel
{
    // Label that responds to clicks.
    // - Multiple inheritance doesn't play nicely with Qt.
    // - So, could inherit from QAbstractButton and implement QLabel functions.
    //   However, QLabel has some complex code for word-wrapping.
    // - Or the reverse: inherit from QLabel and implement
    //   QAbstractButton::mousePressEvent functionality (and all associated
    //   code). But even that is relatively fancy.
    // - Or use an event monitor: label with a monitor attached, e.g.
    //   http://stackoverflow.com/questions/32018941/qt-qlabel-click-event
    // - Or use ownership: label that contains a button, or button that
    //   contains a label.
    //   http://stackoverflow.com/questions/8960233
    // *** TRY INHERITING FROM QABSTRACTBUTTON.

    Q_OBJECT
public:
    ClickableLabel(const QString& text = "", QWidget* parent = nullptr);
    void setClickable(bool clickable);
signals:
    void pressed();
    void released();
    void clicked();
protected:
    virtual bool hitButton(const QPoint &pos) const;
    virtual void mousePressEvent(QMouseEvent* event);
    virtual void mouseReleaseEvent(QMouseEvent* event);
    virtual void mouseMoveEvent(QMouseEvent* event);
protected:
    bool m_clickable;
    bool m_down;
};
