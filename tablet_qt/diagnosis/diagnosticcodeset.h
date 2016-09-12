#pragma once
#include <QAbstractItemModel>
#include <QList>
#include <QString>
#include "diagnosticcode.h"

class CamcopsApp;


class DiagnosticCodeSet : public QAbstractItemModel
{
    Q_OBJECT
public:
    DiagnosticCodeSet(CamcopsApp& app, const QString& setname,
                      const QString& title, QObject* parent = nullptr);
    ~DiagnosticCodeSet();

    QVariant data(const QModelIndex& index, int role) const override;
    Qt::ItemFlags flags(const QModelIndex& index) const override;
    QVariant headerData(int section, Qt::Orientation orientation,
                        int role = Qt::DisplayRole) const override;
    QModelIndex index(
            int row, int column,
            const QModelIndex& parent_index = QModelIndex()) const override;
    QModelIndex parent(const QModelIndex& child) const override;
    int rowCount(const QModelIndex& parent_index) const override;
    int columnCount(const QModelIndex& parent_index) const override;

    int size() const;
    QString title() const;
    QModelIndex firstMatchCode(const QString& code) const;
protected:
    QString xstring(const QString& stringname) const;
    DiagnosticCode* addCode(DiagnosticCode* parent,
                            const QString& code,
                            const QString& description,
                            bool selectable = true,
                            bool show_code_in_full_name = true);
protected:
    CamcopsApp& m_app;
    QString m_setname;  // for xstring
    QString m_title;  // cosmetic
    DiagnosticCode* m_root_item;

public:
    friend QDebug operator<<(QDebug debug, const DiagnosticCodeSet& d);
};
