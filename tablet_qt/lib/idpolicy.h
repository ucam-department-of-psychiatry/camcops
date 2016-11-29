/*
    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

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
