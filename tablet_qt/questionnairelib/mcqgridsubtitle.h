#pragma once
#include <QString>


class McqGridSubtitle
{
    // Structure to describe a subtitle in one of the MCQ grid variants.
    // The subtitle goes in column 0.

public:
    McqGridSubtitle(int pos, const QString& string,
                    bool repeat_options = true);

    // Returns the index at (before) which to place the subtitle.
    int pos() const;

    // Returns the text to display.
    QString string() const;

    // Should we repeat the "options you can choose from" (in columns 1-) in
    // the same row as the subtitle?
    bool repeatOptions() const;

protected:
    int m_pos;
    QString m_string;
    bool m_repeat_options;
};
