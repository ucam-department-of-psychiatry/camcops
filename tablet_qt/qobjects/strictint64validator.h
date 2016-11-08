#pragma once
#include <QValidator>


class StrictInt64Validator : public QValidator
{
    Q_OBJECT
    Q_PROPERTY(int bottom READ bottom WRITE setBottom NOTIFY bottomChanged)
    Q_PROPERTY(int top READ top WRITE setTop NOTIFY topChanged)
public:
    StrictInt64Validator(bool allow_empty = false, QObject* parent = nullptr);
    StrictInt64Validator(qint64 bottom, qint64 top, bool allow_empty = false,
                         QObject* parent = nullptr);
    virtual ~StrictInt64Validator();

    QValidator::State validate(QString& input, int& pos) const override;

    void setBottom(qint64 bottom);
    void setTop(qint64 top);
    virtual void setRange(qint64 bottom, qint64 top);

    qint64 bottom() const { return b; }
    qint64 top() const { return t; }

signals:
    void bottomChanged(qint64 bottom);
    void topChanged(qint64 top);

private:
    Q_DISABLE_COPY(StrictInt64Validator)

private:
    qint64 b;
    qint64 t;
    bool m_allow_empty;
};
