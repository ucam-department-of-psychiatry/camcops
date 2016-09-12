#include "diagnosticcode.h"
#include "common/camcopsapp.h"
#include "diagnosticcodeset.h"


DiagnosticCode::DiagnosticCode(const QString& code, const QString& description,
                               DiagnosticCode* parent,
                               int depth, bool selectable,
                               bool show_code_in_full_name) :
    m_parent(parent),
    m_code(code),
    m_description(description),
    m_depth(depth),
    m_selectable(selectable),
    m_show_code_in_full_name(show_code_in_full_name)
{
}

DiagnosticCode::~DiagnosticCode()
{
    qDeleteAll(m_children);
}


void DiagnosticCode::appendChild(DiagnosticCode* child)
{
    m_children.append(child);
}


DiagnosticCode* DiagnosticCode::child(int row) const
{
    return m_children.value(row);  // will give nullptr if row out of bounds
}


DiagnosticCode* DiagnosticCode::parent() const
{
    return m_parent;
}


int DiagnosticCode::childCount() const
{
    return m_children.size();  // count() or size()
}


int DiagnosticCode::descendantCount() const
{
    int n = 0;
    for (auto c : m_children) {
        n += 1 + c->descendantCount();
    }
    return n;
}


int DiagnosticCode::columnCount() const
{
    return 3;
}


int DiagnosticCode::row() const
{
    if (m_parent) {
        return m_parent->m_children.indexOf(
                    const_cast<DiagnosticCode*>(this));
    }
    return 0;
}


QVariant DiagnosticCode::data(int column) const
{
    switch (column) {
    case COLUMN_CODE:
    default:
        return code();
    case COLUMN_DESCRIPTION:
        return description();
    case COLUMN_FULLNAME:
        return fullname();
    }
}


QString DiagnosticCode::code() const
{
    return m_code;
}


int DiagnosticCode::depth() const
{
    return m_depth;
}


bool DiagnosticCode::selectable() const
{
    return m_selectable;
}


bool DiagnosticCode::hasChildren() const
{
    return childCount() > 0;
}


QString DiagnosticCode::description() const
{
    return m_description;
}


QString DiagnosticCode::fullname() const
{
    if (m_show_code_in_full_name) {
        return QString("%1: %2").arg(m_code).arg(m_description);
    }
    return m_description;
}


QDebug operator<<(QDebug debug, const DiagnosticCode& dc)
{
    for (int i = 0; i < dc.depth(); ++i) {
        debug.nospace() << "... ";
    }
    debug.nospace()
            << dc.code()
            << " (" << dc.description()
            << ") [depth " << dc.depth()
            << "]\n";
    for (auto c : dc.m_children) {
        debug << *c;
    }
    return debug;
}
