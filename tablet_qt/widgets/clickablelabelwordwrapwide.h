#pragma once
#include <QPushButton>
class LabelWordWrapWide;
class QVBoxLayout;


class ClickableLabelWordWrapWide : public QPushButton
{
    Q_OBJECT
public:
    ClickableLabelWordWrapWide(const QString& text, QWidget* parent = nullptr);
    ClickableLabelWordWrapWide(QWidget* parent = nullptr);

    virtual void setTextFormat(Qt::TextFormat format);
    virtual void setWordWrap(bool on);
    virtual void setAlignment(Qt::Alignment alignment);
    virtual void setOpenExternalLinks(bool open);
    virtual void setText(const QString& text);

    virtual QSize sizeHint() const override;
    virtual QSize minimumSizeHint() const override;
    virtual void resizeEvent(QResizeEvent* event) override;
protected:
    void commonConstructor();
    QSize translateSize(const QSize& size) const;

protected:
    LabelWordWrapWide* m_label;
    QVBoxLayout* m_layout;
};
