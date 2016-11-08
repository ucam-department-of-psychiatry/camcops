#pragma once
#include <QValidator>


class StrictUInt64Validator : public QValidator
{
    Q_OBJECT
    Q_PROPERTY(int bottom READ bottom WRITE setBottom NOTIFY bottomChanged)
    Q_PROPERTY(int top READ top WRITE setTop NOTIFY topChanged)
public:
    StrictUInt64Validator(bool allow_empty = false, QObject* parent = nullptr);
    StrictUInt64Validator(quint64 bottom, quint64 top,
                          bool allow_empty = false,
                          QObject* parent = nullptr);
    virtual ~StrictUInt64Validator();

    QValidator::State validate(QString& input, int& pos) const override;

    void setBottom(quint64 bottom);
    void setTop(quint64 top);
    virtual void setRange(quint64 bottom, quint64 top);

    quint64 bottom() const { return b; }
    quint64 top() const { return t; }

signals:
    void bottomChanged(quint64 bottom);
    void topChanged(quint64 top);

private:
    Q_DISABLE_COPY(StrictUInt64Validator)

private:
    quint64 b;
    quint64 t;
    bool m_allow_empty;
};
