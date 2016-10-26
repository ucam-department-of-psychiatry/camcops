#pragma once
#include <QAbstractButton>
class ClickableLabelWordWrapWide;
class ImageButton;
class QVBoxLayout;


class BooleanWidget : public QAbstractButton
{
    // - Encapsulates a widget that can take a variety of appearances, but
    //   embodies some or all of the states true, false, null (not required),
    //   null (required).
    // - Can display as an image or a text button. Because those things don't
    //   play nicely together, owns widgets rather than inheriting.
    // - Main signal is: clicked
    // - RESIST the temptation to have this widget do value logic.
    //   That's the job of its owner.

    // - DON'T try multiple inheritance (inheriting from a custom ABC and
    //   a QObject). It just messes up ("can't convert to QObject", when
    //   access is from ABC pointer; etc.).

    Q_OBJECT
public:
    enum class State {
        Disabled,
        Null,
        NullRequired,
        False,
        True,
    };
    enum class Appearance {
        CheckBlack,
        CheckRed,
        Radio,
        Text,
    };
public:
    BooleanWidget(QWidget* parent = nullptr);
    // Used at construction time:
    virtual void setReadOnly(bool read_only = false);
    void setSize(bool big = false);
    void setAppearance(BooleanWidget::Appearance appearance);
    // Used live:
    void setState(BooleanWidget::State state);
    void setValue(const QVariant& value, bool mandatory,
                  bool disabled = false);
    void setText(const QString& text);

    virtual QSize sizeHint() const override;
    virtual QSize minimumSizeHint() const override;
protected:
    virtual void paintEvent(QPaintEvent* e) override;
    void updateWidget();
protected:
    bool m_read_only;
    bool m_big;
    Appearance m_appearance;
    bool m_as_image;
    State m_state;
    ImageButton* m_imagebutton;
    ClickableLabelWordWrapWide* m_textbutton;
    QVBoxLayout* m_layout;
};
