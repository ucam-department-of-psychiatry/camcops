#include "storedvar.h"
#include "lib/uifunc.h"

const QString STOREDVAR_TABLENAME = "storedvar";
const QString NAME_FIELDNAME = "name";
const QString TYPE_FIELDNAME = "type";
// - No need to keep to legacy fieldnames (valueInteger, valueReal, valueText)
//   as we'll no longer be uploading these.
const QString VALUE_INTEGER_FIELDNAME = "value_integer";
const QString VALUE_REAL_FIELDNAME = "value_real";
const QString VALUE_TEXT_FIELDNAME = "value_text";
// - Also, SQLite is typeless... could make use of that, and store all values
//   in the same column. But for generality:
const QMap<QVariant::Type, QString> COLMAP{
    {QVariant::Int, VALUE_INTEGER_FIELDNAME},
    {QVariant::Double, VALUE_REAL_FIELDNAME},
    {QVariant::String, VALUE_TEXT_FIELDNAME},
};
const QMap<QVariant::Type, QString> TYPEMAP{
    // http://doc.qt.io/qt-5/qvariant-obsolete.html#Type-enum
    {QVariant::Int, "Int"},
    {QVariant::Double, "Double"},
    {QVariant::String, "String"},
};


StoredVar::StoredVar(const QSqlDatabase& db, const QString& name,
                     QVariant::Type type, QVariant default_value) :
    DatabaseObject(db, STOREDVAR_TABLENAME),
    m_name(name),
    m_type(type),
    m_value_fieldname("")
{
    // ------------------------------------------------------------------------
    // Define fields
    // ------------------------------------------------------------------------
    addField(NAME_FIELDNAME, QVariant::String, true, true, false);
    addField(TYPE_FIELDNAME, QVariant::String, true, true, false);
    QMapIterator<QVariant::Type, QString> i(COLMAP);
    while (i.hasNext()) {
        i.next();
        addField(i.value(), i.key(), false, false, false);
        if (i.key() == type) {
            // Define our primary field
            m_value_fieldname = i.value();
        }
    }
    if (m_value_fieldname.isEmpty()) {
        UiFunc::stopApp(QString("StoredVar::StoredVar: m_value_fieldname "
                                "unknown to StoredVar with type %1").arg(type));
    }
    if (!TYPEMAP.contains(type)) {
        qCritical() << Q_FUNC_INFO << "QVariant type unknown:" << type;
        UiFunc::stopApp("StoredVar::StoredVar: type unknown to StoredVar; see "
                        "debug console for details");
    }

    // ------------------------------------------------------------------------
    // Load from database (or create/save), unless this is a specimen
    // ------------------------------------------------------------------------
    if (!name.isEmpty()) {
        // Not a specimen; load, or set defaults and save
        bool success = load(NAME_FIELDNAME, name);
        if (!success) {
            setValue(NAME_FIELDNAME, name);
            setValue(TYPE_FIELDNAME, TYPEMAP[type]);
            qDebug() << "Setting type to:" << type;
            setValue(default_value);
            save();
        }
    }
}


StoredVar::~StoredVar()
{
}


void StoredVar::setValue(const QVariant &value, bool save_to_db)
{
    setValue(m_value_fieldname, value);
    if (save_to_db) {
        save();
    }
}


QVariant StoredVar::value() const
{
    QVariant v = value(m_value_fieldname);
    v.convert(m_type);
    return v;
}


QString StoredVar::name() const
{
    return m_name;
}
