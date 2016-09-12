#pragma once
#include <QList>
#include <QString>
#include "diagnosticcode.h"

class CamcopsApp;


class DiagnosticCodeSet
{
public:
    static const int INVALID;
public:
    DiagnosticCodeSet(CamcopsApp& app, const QString& setname,
                      const QString& root_title);
    QString description(int index) const;
    QString description(const QString& code) const;
    bool isValidIndex(int index) const;
    int firstIndexFromCode(const QString& code) const;
    bool hasCode(const QString& code);
    int addCode(int parent_index,
                const QString& code,
                const QString& description,
                bool selectable = true,
                bool show_code_in_full_name = true);  // returns index
    int size() const;
    const DiagnosticCode* at(int index) const;
    QList<const DiagnosticCode*> children(int index) const;
    int parentIndexOf(int index) const;
    QString title() const;
protected:
    QString xstring(const QString& stringname) const;
protected:
    CamcopsApp& m_app;
    QString m_setname;
    QList<DiagnosticCode> m_codes;

public:
    friend QDebug operator<<(QDebug debug, const DiagnosticCodeSet& d);
};
