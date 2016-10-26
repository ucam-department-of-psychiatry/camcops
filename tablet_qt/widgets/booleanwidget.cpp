#include "booleanwidget.h"
#include <QDebug>
#include <QPainter>
#include <QVariant>
#include <QVBoxLayout>
#include "common/uiconstants.h"
#include "lib/uifunc.h"
#include "widgets/clickablelabelwordwrapwide.h"
#include "widgets/imagebutton.h"

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
    QAbstractButton(parent),
    m_read_only(false),
    m_big(true),
    m_appearance(Appearance::CheckRed),
    m_as_image(true),
    m_state(State::Null)
{
    m_imagebutton = new ImageButton();
    m_textbutton = new ClickableLabelWordWrapWide();
    m_layout = new QVBoxLayout();
    m_layout->setContentsMargins(UiConst::NO_MARGINS);
    m_layout->addWidget(m_imagebutton);
    m_layout->addWidget(m_textbutton);
    setLayout(m_layout);

    connect(m_imagebutton, &ImageButton::clicked,
            this, &BooleanWidget::clicked);
    connect(m_textbutton, &ClickableLabelWordWrapWide::clicked,
            this, &BooleanWidget::clicked);

    // setObjectName("boolean_widget");
    updateWidget();
}


void BooleanWidget::setReadOnly(bool read_only)
{
    if (read_only != m_read_only) {
        m_read_only = read_only;
        updateWidget();
    }
}


void BooleanWidget::setSize(bool big)
{
    if (big != m_big) {
        m_big = big;
        updateWidget();
    }
}


void BooleanWidget::setAppearance(BooleanWidget::Appearance appearance)
{
    if (appearance != m_appearance) {
        m_appearance = appearance;
        m_as_image = (appearance != Appearance::Text);
        updateWidget();
    }
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
    if (state != m_state) {
        m_state = state;
        updateWidget();
    }
}


void BooleanWidget::updateWidget()
{
    QString img;
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
        // http://wiki.qt.io/DynamicPropertiesAndStylesheets
        {
            QString property = "state";
            switch (m_state) {
            case State::Disabled:
                UiFunc::setProperty(this, property, "disabled");
                break;
            case State::Null:
                UiFunc::setProperty(this, property, "null");
                break;
            case State::NullRequired:
                UiFunc::setProperty(this, property, "nullrequired");
                break;
            case State::False:
                UiFunc::setProperty(this, property, "false");
                break;
            case State::True:
                UiFunc::setProperty(this, property, "true");
                break;
            }
            setProperty("readonly", UiFunc::cssBoolean(m_read_only));
        }
        break;
    }
    if (m_as_image) {
        m_imagebutton->setVisible(true);
        m_textbutton->setVisible(false);
        m_imagebutton->setImageSize(m_big ? UiConst::ICONSIZE : UiConst::SMALL_ICONSIZE);
        m_imagebutton->setImages(img, true, false, false, false, m_read_only);
        // ... don't alter unpressed images
        // ... FOR NOW, put pressed marker on top (as PNGs are not transparent
        //     inside the check boxes etc.)
        setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    } else {  // Text
        m_imagebutton->setVisible(false);
        m_textbutton->setVisible(true);
        setSizePolicy(UiFunc::horizMaximumHFWPolicy());
        // One of these is probably unnecessary:
        UiFunc::repolish(this);
        // UiFunc::repolish(m_textbutton);
    }
    updateGeometry();
}


void BooleanWidget::setText(const QString& text)
{
    qDebug() << Q_FUNC_INFO << text;
    m_textbutton->setText(text);
    updateGeometry();
}


void BooleanWidget::paintEvent(QPaintEvent* e)
{
    Q_UNUSED(e);
    /*
    // To draw child widgets explicitly, use render (since paintEvent is
    // protected).
    // http://stackoverflow.com/questions/18042969
    QPainter painter(this);
    if (m_as_image) {
        m_imagebutton->render(&painter);
    } else {
        m_textbutton->render(&painter);
    }
    // However, our child widgets draw themselves anyway.
    // We just have to implement this function somehow as QAbstractButton is
    // an abstract base class.
    */
}


QSize BooleanWidget::sizeHint() const
{
    // Can ignore layout margins because we've forced them to zero.
    return m_as_image ? m_imagebutton->sizeHint() : m_textbutton->sizeHint();
}


QSize BooleanWidget::minimumSizeHint() const
{
    // Can ignore layout margins because we've forced them to zero.
    return m_as_image ? m_imagebutton->minimumSizeHint()
                      : m_textbutton->minimumSizeHint();
}
