#include "diagnosticcodeset.h"
#include "common/camcopsapp.h"

const int DiagnosticCodeSet::INVALID = -1;
const QString BAD_STRING = "[bad_string]";


DiagnosticCodeSet::DiagnosticCodeSet(CamcopsApp* app, const QString& setname) :
    m_app(app),
    m_setname(setname)
{
    DiagnosticCode root("", "[root node]", INVALID, 0, false);
    m_codes.append(root);  // will have index 0
}


QString DiagnosticCodeSet::description(int index) const
{
    if (!m_app || !isValidIndex(index)) {
        return BAD_STRING;
    }
    return m_codes[index].description();
}



QString DiagnosticCodeSet::description(const QString& code) const
{
    int index = firstIndexFromCode(code);
    return description(index);
}


bool DiagnosticCodeSet::isValidIndex(int index) const
{
    return index >= 0 && index < m_codes.size();
}


int DiagnosticCodeSet::firstIndexFromCode(const QString& code) const
{
    int n = m_codes.size();
    for (int i = 0; i < n; ++i) {
        if (m_codes[i].code() == code) {
            return i;
        }
    }
    return INVALID;
}


int DiagnosticCodeSet::addCode(int parent_index, const QString& code,
                               const QString& description, bool selectable,
                               bool show_code_in_full_name)
{
    if (!isValidIndex(parent_index)) {
        return INVALID;
    }
    DiagnosticCode& parent = m_codes[parent_index];
    DiagnosticCode c(code, description,
                     parent_index, parent.depth() + 1, selectable,
                     show_code_in_full_name);
    m_codes.append(c);
    int new_index = m_codes.size() - 1;
    parent.addChildIndex(new_index);
    return new_index;
}


QDebug operator<<(QDebug debug, const DiagnosticCodeSet& d)
{
    debug << "DiagnosticCodeSet: m_setname:" << d.m_setname << "\n";
    int n = d.m_codes.size();
    for (int i = 0; i < n; ++i) {
        const DiagnosticCode& dc = d.m_codes[i];
        debug.nospace()
                << "... " << i
                << ": " << dc.code()
                << " (" << dc.description()
                << ") [depth " << dc.depth()
                << ", parent " << dc.parentIndex()
                << ", children " << dc.children()
                << "]\n";
    }
    debug << "... end\n";
    return debug;
}


QString DiagnosticCodeSet::xstring(const QString& stringname) const
{
    if (!m_app) {
        return BAD_STRING;
    }
    return m_app->xstring(m_setname, stringname);
}
