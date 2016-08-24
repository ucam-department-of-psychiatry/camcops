#include "booleanwidget.h"
#include <QVariant>
#include "common/uiconstants.h"
#include "lib/uifunc.h"

const QString CHECK_DISABLED = "check_disabled.png";
const QString CHECK_UNSELECTED = "check_unselected.png";
const QString CHECK_UNSELECTED_REQUIRED = "check_unselected_required.png";
const QString CHECK_FALSE_BLACK = "check_false_black.png";
const QString CHECK_FALSE_RED = "check_false_red.png";
const QString CHECK_TRUE_BLACK = "check_true_black.png";
const QString CHECK_TRUE_RED = "check_true_red.png";

const QString RADIO_DISABLED = "radio_disabled.png";
const QString RADIO_UNSELECTED = "radio_unselected.png";
const QString RADIO_UNSELECTED_REQUIRED = "radio_unselected_required.png";
const QString RADIO_SELECTED = "radio_selected.png";


BooleanWidget::BooleanWidget(QWidget* parent) :
    ImageButton(parent),
    m_read_only(false),
    m_big(true),
    m_appearance(Appearance::CheckRed),
    m_state(State::Null)
{
}


void BooleanWidget::setReadOnly(bool read_only)
{
    m_read_only = read_only;
}


void BooleanWidget::setSize(bool big)
{
    m_big = big;
}


void BooleanWidget::setAppearance(BooleanWidget::Appearance appearance)
{
    m_appearance = appearance;
}


void BooleanWidget::setValue(const QVariant& value, bool mandatory,
                             bool disabled)
{
    if (disabled) {
        setState(State::Disabled);
    } else if (value.isNull()) {
        setState(mandatory ? State::NullRequired : State::Null);
    } else if (value.toBool()) {
        setState(State::True);
    } else {
        setState(State::False);
    }
}


void BooleanWidget::setState(BooleanWidget::State state)
{
    m_state = state;
    QString img;
    bool as_image = true;
    switch (m_appearance) {
    case Appearance::CheckBlack:
        switch (m_state) {
        case State::Disabled:
            img = CHECK_DISABLED;
            break;
        case State::Null:
            img = CHECK_UNSELECTED;
            break;
        case State::NullRequired:
            img = CHECK_UNSELECTED_REQUIRED;
            break;
        case State::False:
            img = CHECK_FALSE_BLACK;
            break;
        case State::True:
            img = CHECK_TRUE_BLACK;
            break;
        }
        break;
    case Appearance::CheckRed:
    default:
        switch (m_state) {
        case State::Disabled:
            img = CHECK_DISABLED;
            break;
        case State::Null:
            img = CHECK_UNSELECTED;
            break;
        case State::NullRequired:
            img = CHECK_UNSELECTED_REQUIRED;
            break;
        case State::False:
            img = CHECK_FALSE_RED;
            break;
        case State::True:
            img = CHECK_TRUE_RED;
            break;
        }
        break;
    case Appearance::Radio:
        switch (m_state) {
        case State::Disabled:
            img = RADIO_DISABLED;
            break;
        case State::Null:
            img = RADIO_UNSELECTED;
            break;
        case State::NullRequired:
            img = RADIO_UNSELECTED_REQUIRED;
            break;
        case State::False:
            // not so meaningful
            img = RADIO_UNSELECTED;
            break;
        case State::True:
            img = RADIO_SELECTED;
            break;
        }
        break;
    case Appearance::Text:
        as_image = false;
        // *** set CSS
        break;
    }
    if (as_image) {
        setAsText(false);
        setImageSize(m_big ? UiConst::ICONSIZE : UiConst::SMALL_ICONSIZE);
        setImages(img, true, false, false, false, m_read_only);
        // ... don't alter unpressed images
        // ... FOR NOW, put pressed marker on top (as PNGs are not transparent
        //     inside the check boxes etc.)
    } else {
        setAsText(true);
    }
}
