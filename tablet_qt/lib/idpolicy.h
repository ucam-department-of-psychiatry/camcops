#pragma once
#include <QList>
#include <QMap>
#include <QString>


class IdPolicy
{
    using AttributesType = QMap<QString, bool>;
public:
    IdPolicy(const QString& policy_text);
    bool complies(const AttributesType& attributes) const;
    QString original() const;
    QString pretty() const;
public:
    enum class ChunkValue {
        True,
        False,
        Unknown,
        SyntaxError,
    };
    enum class OperatorValue {
        And,
        Or,
        None,
    };
protected:
    void initializeTokenDicts();
    void tokenize(const QString& policy_text);
    void reportSyntaxError(const QString& msg) const;
    ChunkValue idPolicyChunk(const QList<int>& tokens,
                             const AttributesType& attributes) const;
    ChunkValue idPolicyContent(const QList<int>& tokens,
                               const AttributesType& attributes,
                               int& index) const;
    OperatorValue idPolicyOp(const QList<int>& tokens, int& index) const;
    ChunkValue idPolicyElement(const AttributesType& attributes,
                               int token) const;
    QString stringify(const QList<int>& tokens) const;
protected:
    QString m_policy_text;
    QMap<int, QString> m_token_to_name;
    QMap<QString, int> m_name_to_token;
    QList<int> m_tokens;
    bool m_valid;
};


extern const IdPolicy TABLET_ID_POLICY;
