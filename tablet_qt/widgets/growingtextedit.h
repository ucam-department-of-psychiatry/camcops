#pragma once
#include <QTextEdit>


class GrowingTextEdit : public QTextEdit
{
    // see http://stackoverflow.com/questions/11677499
    // http://stackoverflow.com/questions/3050537
    // http://stackoverflow.com/questions/1153714
    // http://www.qtcentre.org/threads/9840-QTextEdit-auto-resize
    // http://stackoverflow.com/questions/11851020
    Q_OBJECT
public:
    GrowingTextEdit(QWidget* parent = nullptr);
    GrowingTextEdit(const QString& text, QWidget* parent = nullptr);
    virtual ~GrowingTextEdit();
    void setAutoResize(bool auto_resize);
    virtual QSize sizeHint() const override;
protected:
    void commonConstructor();
protected slots:
    void contentsChanged();
protected:
    bool m_auto_resize;
    Qt::Orientations m_fitted_orientations;
    int m_fitted_width;
    int m_fitted_height;
};
