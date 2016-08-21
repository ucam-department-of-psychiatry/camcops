#pragma once
#include <QSharedPointer>
#include <QWidget>


class OpenableWidget : public QWidget
{
    Q_OBJECT
public:
    OpenableWidget(QWidget* parent = nullptr);
    virtual void build();  // opportunity to do stuff between creation and opening
    virtual bool wantsFullscreen();
signals:
    void finished();
};
