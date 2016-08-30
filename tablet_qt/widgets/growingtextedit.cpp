#include "growingtextedit.h"
// #include <QDebug>


GrowingTextEdit::GrowingTextEdit(QWidget* parent) :
    QTextEdit(parent)
{
    commonConstructor();
}


GrowingTextEdit::GrowingTextEdit(const QString& text, QWidget* parent) :
    QTextEdit(text, parent)
{
    commonConstructor();
}


void GrowingTextEdit::commonConstructor()
{
    m_auto_resize = true;

    connect(document(), &QTextDocument::contentsChanged,
            this, &GrowingTextEdit::contentsChanged);

    QSizePolicy sp(QSizePolicy::Expanding, QSizePolicy::Fixed);
    setSizePolicy(sp);
}


GrowingTextEdit::~GrowingTextEdit()
{
}


void GrowingTextEdit::setAutoResize(bool auto_resize)
{
    m_auto_resize = auto_resize;
}


QSize GrowingTextEdit::sizeHint() const
{
    QSize size_hint;
    if (m_auto_resize) {
        size_hint = document()->size().toSize();
    } else {
        size_hint = QTextEdit::sizeHint();
    }
    // qDebug() << Q_FUNC_INFO << "-" << size_hint;
    return size_hint;
}


void GrowingTextEdit::contentsChanged()
{
    // qDebug() << Q_FUNC_INFO;
    document()->setTextWidth(viewport()->width());
    updateGeometry();
}

// The final piece of the puzzle is that the Questionnaire's scroll area
// needs to resize itself when the widget sizes change.
// That requires:
//      http://doc.qt.io/qt-5.7/qscrollarea.html#widgetResizable-prop
// ... and (in VerticalScrollArea) a call to updateGeometry() when its widget
// size changes, it seems.
