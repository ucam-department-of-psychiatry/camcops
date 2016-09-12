#include "diagnosticcode.h"
#include <QDebug>
#include "common/camcopsapp.h"


DiagnosticCode::DiagnosticCode(int index,
                               const QString& code, const QString& description,
                               int parent_index, int depth, bool selectable,
                               bool show_code_in_full_name) :
    m_index(index),
    m_code(code),
    m_description(description),
    m_parent_index(parent_index),
    m_depth(depth),
    m_selectable(selectable),
    m_show_code_in_full_name(show_code_in_full_name)
{
}


int DiagnosticCode::index() const
{
    return m_index;
}


QString DiagnosticCode::code() const
{
    return m_code;
}


int DiagnosticCode::parentIndex() const
{
    return m_parent_index;
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
    return m_child_indexes.size() > 0;
}


QList<int> DiagnosticCode::childIndexes() const
{
    return m_child_indexes;
}


void DiagnosticCode::addChildIndex(int index)
{
    if (m_child_indexes.contains(index)) {
        qWarning() << Q_FUNC_INFO << "Attempt to add child index twice:"
                   << index;
        return;
    }
    m_child_indexes.append(index);
}


void DiagnosticCode::addChildIndexes(const QList<int> indexes)
{
    for (auto index : indexes) {
        addChildIndex(index);
    }
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
