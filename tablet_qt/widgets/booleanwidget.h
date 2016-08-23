#pragma once
#include "imagebutton.h"


class BooleanWidget : public ImageButton
{
    // - Encapsulates a widget that can take a variety of appearances, but
    //   embodies some or all of the states true, false, null (not required),
    //   null (required).
    // - Main signal is: clicked
    // - RESIST the temptation to have this widget do value logic.
    //   That's the job of its owner.

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
    };

public:
    BooleanWidget(QWidget* parent = nullptr);
    // Used at construction time:
    void setReadOnly(bool read_only = false);
    void setSize(bool big = false);
    void setAppearance(BooleanWidget::Appearance appearance);
    // Used live:
    void setState(BooleanWidget::State state);
    void setValue(const QVariant& value, bool mandatory,
                  bool disabled = false);
protected:
    bool m_read_only;
    bool m_big;
    State m_state;
    Appearance m_appearance;
};
