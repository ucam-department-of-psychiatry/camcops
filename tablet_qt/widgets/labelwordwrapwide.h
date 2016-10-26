#pragma once
#include <QLabel>


class LabelWordWrapWide : public QLabel
{
    // Label that word-wraps its text, and prefers to be wide rather than tall.

    Q_OBJECT
public:
    explicit LabelWordWrapWide(const QString& text, QWidget* parent = nullptr);
    explicit LabelWordWrapWide(QWidget* parent = nullptr);
    void commonConstructor();
    virtual void resizeEvent(QResizeEvent* event) override;
    virtual QSize sizeHint() const override;
};
