#pragma once
#include <QCoreApplication>  // for Q_DECLARE_TR_FUNCTIONS
#include <QString>
#include "namevalueoptions.h"


// Translation doesn't work for static variables, because static variables
// are initialized before QApplication is instantiated.
// We want translation here, so we use a class.
// Anything that needs translation must go via a function.

class CommonOptions
{
    Q_DECLARE_TR_FUNCTIONS(CommonOptions)

    // ========================================================================
    // Database-level constants
    // ========================================================================
public:
    static const QString NO_CHAR;
    static const QString YES_CHAR;
    static const int UNKNOWN_INT;
    static const int NO_INT;
    static const int YES_INT;
    static const int INCORRECT_INT;
    static const int CORRECT_INT;

    // ========================================================================
    // Translated text
    // ========================================================================
public:
    static QString yes();
    static QString no();
    static QString correct();
    static QString incorrect();
    static QString false_str();
    static QString true_str();
    static QString absent();
    static QString present();
    static QString unknown();

    // ========================================================================
    // Option sets
    // ========================================================================
public:
    static NameValueOptions yesNoChar();
    static NameValueOptions yesNoBoolean();
    static NameValueOptions yesNoInteger();
    static NameValueOptions noYesChar();
    static NameValueOptions noYesBoolean();
    static NameValueOptions noYesInteger();

    static NameValueOptions incorrectCorrectBoolean();
    static NameValueOptions incorrectCorrectInteger();
    static NameValueOptions falseTrueBoolean();
    static NameValueOptions absentPresentBoolean();
    static NameValueOptions unknownNoYesInteger();
};
