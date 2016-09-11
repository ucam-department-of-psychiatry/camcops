#pragma once
#include "diagnosticcodeset.h"
#include <QCoreApplication>  // for Q_DECLARE_TR_FUNCTIONS
#include <QPair>
#include <QStack>

class CamcopsApp;


class Icd10 : public DiagnosticCodeSet
{
    Q_DECLARE_TR_FUNCTIONS(Icd10)

public:
    Icd10(CamcopsApp* app);

    using CodeDescriptionPair = QPair<QString, QString>;
    using DepthIndexPair = QPair<int, int>;
private:
    void addIcd10Codes(const QList<QString>& codes);
    void addIndividualIcd10Code(const QString& code, const QString& desc,
                                bool show_code_in_full_name = true);
    void addSubcodes(const QString& basecode,
                     const QString& basedesc,
                     const QList<CodeDescriptionPair>& level1);
    void addSubcodes(const QString& basecode,
                     const QString& basedesc,
                     const QList<CodeDescriptionPair>& level1,
                     const QList<CodeDescriptionPair>& level2);

    QStack<DepthIndexPair> m_creation_stack;  // depth, index (of parents)

    void addDementia(const QString& basecode, const QString& basedesc);
    void addSubstance(const QString& basecode, const QString& basedesc);
    void addSchizophrenia(const QString& basecode, const QString& basedesc);
    void addSelfHarm(const QString& basecode, const QString& basedesc);

    static const QList<QString> BASE_CODES;
    static const QList<CodeDescriptionPair> DEMENTIA_L1;
    static const QList<CodeDescriptionPair> DEMENTIA_L2;
    static const QList<CodeDescriptionPair> SUBSTANCE_L1;
    static const QList<CodeDescriptionPair> SCHIZOPHRENIA_L1;
    static const QList<CodeDescriptionPair> SELFHARM_L1;
    static const QList<CodeDescriptionPair> SELFHARM_L2;
};
