#include "diagnosticcodeset.h"
#include "common/camcopsapp.h"

const QString BAD_STRING("[bad_string]");


DiagnosticCodeSet::DiagnosticCodeSet(const CamcopsApp& app,
                                     const QString& setname,
                                     const QString& title,  QObject* parent) :
    QAbstractItemModel(parent),
    m_app(app),
    m_setname(setname),
    m_title(title),
    m_root_item(nullptr)
{
    m_root_item = new DiagnosticCode("", "", nullptr, 0, false, false);
}


DiagnosticCodeSet::~DiagnosticCodeSet()
{
    delete m_root_item;
}


QModelIndex DiagnosticCodeSet::index(int row, int column,
                                     const QModelIndex& parent_index) const
{
    if (!hasIndex(row, column, parent_index)) {
        return QModelIndex();
    }

    DiagnosticCode* parent_item;
    if (!parent_index.isValid()) {
        parent_item = m_root_item;
    } else {
        parent_item = static_cast<DiagnosticCode*>(
                    parent_index.internalPointer());
    }

    DiagnosticCode* child_item = parent_item->child(row);
    if (child_item) {
        return createIndex(row, column, child_item);
    } else {
        return QModelIndex();
    }
}


QModelIndex DiagnosticCodeSet::parent(const QModelIndex& index) const
{
    if (!index.isValid()) {
        return QModelIndex();
    }

    DiagnosticCode* child_item = static_cast<DiagnosticCode*>(
                index.internalPointer());
    DiagnosticCode* parent_item = child_item->parent();

    if (!parent_item || parent_item == m_root_item) {
        return QModelIndex();
    }

    return createIndex(parent_item->row(), 0, parent_item);
}


int DiagnosticCodeSet::rowCount(const QModelIndex& parent_index) const
{
    DiagnosticCode* parent_item;
    if (parent_index.column() > 0) {
        return 0;
    }

    if (!parent_index.isValid()) {
        parent_item = m_root_item;
    } else {
        parent_item = static_cast<DiagnosticCode*>(
                    parent_index.internalPointer());
    }

    return parent_item->childCount();
}


int DiagnosticCodeSet::columnCount(const QModelIndex& parent_index) const
{
    if (parent_index.isValid()) {
        return static_cast<DiagnosticCode*>(
                    parent_index.internalPointer())->columnCount();
    } else {
        return m_root_item->columnCount();
    }
}


QVariant DiagnosticCodeSet::data(const QModelIndex &index, int role) const
{
    if (!index.isValid()) {
        return QVariant();
    }

    if (role != Qt::DisplayRole) {
        return QVariant();
    }

    DiagnosticCode* item = static_cast<DiagnosticCode*>(
                index.internalPointer());

    return item->data(index.column());
}


Qt::ItemFlags DiagnosticCodeSet::flags(const QModelIndex& index) const
{
    if (!index.isValid()) {
        return 0;
    }
    // return QAbstractItemModel::flags(index);
    DiagnosticCode* item = static_cast<DiagnosticCode*>(
                index.internalPointer());
    Qt::ItemFlags flags = Qt::ItemIsEnabled;
    if (item->selectable()) {
        flags |= Qt::ItemIsSelectable;
    }
    return flags;
}


QVariant DiagnosticCodeSet::headerData(int section,
                                       Qt::Orientation orientation,
                                       int role) const
{
    if (orientation == Qt::Horizontal && role == Qt::DisplayRole) {
        return m_root_item->data(section);
    }

    return QVariant();
}


QString DiagnosticCodeSet::title() const
{
    return m_title;
}


QModelIndex DiagnosticCodeSet::firstMatchCode(const QString &code) const
{
    // http://www.qtcentre.org/threads/15572-How-can-I-traverse-all-of-the-items-in-a-QStandardItemModel
    // Walk the tree:

    QStack<DiagnosticCode*> stack;
    stack.push(m_root_item);
    while (!stack.isEmpty()) {
        DiagnosticCode* item = stack.pop();

        // Do something with item:
        if (item->code() == code) {
            return createIndex(item->row(), 0, item);
        }

        for (int i = item->childCount() - 1; i >= 0; --i) {
            stack.push(item->child(i));
        }
    }
    return QModelIndex();
}


QDebug operator<<(QDebug debug, const DiagnosticCodeSet& d)
{
    debug << "DiagnosticCodeSet: m_setname" << d.m_setname
          << "m_title" << d.m_title << "\n";
    if (d.m_root_item) {
        debug << *d.m_root_item;  // will recurse
    } else {
        debug << "... no items";
    }
    debug << "... end\n";
    return debug;
}


QString DiagnosticCodeSet::xstring(const QString& stringname) const
{
    return m_app.xstring(m_setname, stringname);
}


int DiagnosticCodeSet::size() const
{
    return m_root_item->descendantCount();
}


DiagnosticCode* DiagnosticCodeSet::addCode(
        DiagnosticCode* parent, const QString& code,
        const QString& description, bool selectable,
        bool show_code_in_full_name)
{
    if (parent == nullptr) {
        parent = m_root_item;
    }
    DiagnosticCode* c = new DiagnosticCode(
                code, description,
                parent, parent->depth() + 1, selectable,
                show_code_in_full_name);
    parent->appendChild(c);
    return c;
}
