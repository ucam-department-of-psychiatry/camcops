#pragma once
#include <QString>


class McqGridSubtitle
{
    // Structure to describe a subtitle in one of the MCQ grid variants.

public:
    McqGridSubtitle(int pos, const QString& string,
                    bool repeat_options = true);
    int pos() const;
    QString string() const;
    bool repeatOptions() const;
protected:
    int m_pos;  // e.g. index at (before) which to place e.g. subtitle
    QString m_string;
    bool m_repeat_options;
};
