#include "diagnosticcodeset.h"
#include "common/camcopsapp.h"

const int DiagnosticCodeSet::INVALID = -1;
const QString BAD_STRING = "[bad_string]";


DiagnosticCodeSet::DiagnosticCodeSet(CamcopsApp& app, const QString& setname,
                                     const QString& root_title) :
    m_app(app),
    m_setname(setname)
{
    // Add a special root code with an invalid parent index and an invalid code
    // (so don't use addCode):
    m_codes.append(DiagnosticCode(0, "", root_title, INVALID, 0, false, false));
}


QString DiagnosticCodeSet::title() const
{
    return m_codes.at(0).description();
}


QString DiagnosticCodeSet::description(int index) const
{
    if (!isValidIndex(index)) {
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
    if (code.isEmpty()) {
        return INVALID;
    }
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
        qWarning() << Q_FUNC_INFO << "invalid parent_index:" << parent_index;
        return INVALID;
    }
    if (code.isEmpty()) {
        qWarning() << Q_FUNC_INFO << "empty code; ignored";
        return INVALID;
    }
    int new_index = m_codes.size();
    DiagnosticCode& parent = m_codes[parent_index];
    DiagnosticCode c(new_index, code, description,
                     parent_index, parent.depth() + 1, selectable,
                     show_code_in_full_name);
    m_codes.append(c);
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
                << ", children " << dc.childIndexes()
                << "]\n";
    }
    debug << "... end\n";
    return debug;
}


QString DiagnosticCodeSet::xstring(const QString& stringname) const
{
    return m_app.xstring(m_setname, stringname);
}


QList<const DiagnosticCode*> DiagnosticCodeSet::children(int index) const
{
    QList<const DiagnosticCode*> codes;
    if (!isValidIndex(index)) {
        return codes;
    }
    const DiagnosticCode& dc = m_codes[index];
    for (int child_index : dc.childIndexes()) {
        codes.append(&m_codes[child_index]);
    }
    return codes;
}


const DiagnosticCode* DiagnosticCodeSet::at(int index) const
{
    if (!isValidIndex(index)) {
        return nullptr;
    }
    return &m_codes[index];
}


int DiagnosticCodeSet::parentIndexOf(int index) const
{
    if (!isValidIndex(index)) {
        return INVALID;
    }
    return m_codes[index].parentIndex();
}


int DiagnosticCodeSet::size() const
{
    return m_codes.size();
}
