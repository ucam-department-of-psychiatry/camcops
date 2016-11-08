#pragma once
#include "db/databaseobject.h"
#include <QDate>
#include <QMap>
#include <QPointer>
class CamcopsApp;
class IdPolicy;
class OpenableWidget;
class Questionnaire;

extern const QString FORENAME_FIELD;
extern const QString SURNAME_FIELD;
extern const QString DOB_FIELD;
extern const QString SEX_FIELD;
extern const QString ADDRESS_FIELD;
extern const QString GP_FIELD;
extern const QString OTHER_FIELD;
extern const QString IDNUM_FIELD_FORMAT;


class Patient : public DatabaseObject
{
    Q_OBJECT
    using AttributesType = QMap<QString, bool>;
public:
    Patient(CamcopsApp& app,
            const QSqlDatabase& db,
            int load_pk = DbConst::NONEXISTENT_PK);
    int id() const;
    QString forename() const;
    QString surname() const;
    QString surnameUpperForename() const;
    QString sex() const;
    bool isFemale() const;
    bool isMale() const;
    QDate dob() const;
    QString dobText() const;
    int ageYears() const;
    bool hasForename() const;
    bool hasSurname() const;
    bool hasDob() const;
    bool hasSex() const;
    bool hasIdnum(int which_idnum) const;
    QVariant idnumVariant(int which_idnum) const;
    qlonglong idnumInteger(int which_idnum) const;
    OpenableWidget* editor(bool read_only);
    AttributesType policyAttributes() const;
    bool compliesWith(const IdPolicy& policy) const;
    QString shortIdnumSummary() const;
protected:
    void updateQuestionnaireIndicators(const FieldRef* fieldref = nullptr,
                                       const QObject* originator = nullptr);
protected:
    CamcopsApp& m_app;
    QPointer<Questionnaire> m_questionnaire;
};
