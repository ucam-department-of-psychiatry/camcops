#pragma once
#include <QString>

/*
#include "zallocator.h"

typedef std::basic_string<char, std::char_traits<char>, zallocator<char>> SecureQString;
*/

using SecureQString = QString;

// No joy with this. My operator=() was failing.
// See also
// - http://stackoverflow.com/questions/3785582/how-to-write-a-password-safe-class
// - https://forum.qt.io/topic/15341/clear-the-password-from-memory/8
// - OpenSSL EVP example: https://wiki.openssl.org/index.php/EVP_Symmetric_Encryption_and_Decryption
// - QString <-> std::string: http://stackoverflow.com/questions/1814189/how-to-change-string-into-qstring
// - Note also that QString has a non-virtual destructor.
//   Not critical, I think; http://www.programmerinterview.com/index.php/c-cplusplus/virtual-destructors/
// - Note the difference between
//      Type x = Type(...);  // copy initialization
//      Type x(...);  // direct initialization
//   http://stackoverflow.com/questions/1051379/is-there-a-difference-in-c-between-copy-initialization-and-direct-initializati
//   http://stackoverflow.com/questions/4293596/when-should-you-use-direct-initialization-and-when-copy-initialization
//   http://scottmeyers.blogspot.co.uk/2015/09/thoughts-on-vagaries-of-c-initialization.html

// class SecureQByteArray;

/*
class SecureQString : public QString
{
public:
    SecureQString();
    SecureQString(const QChar* unicode, int size = -1);
    SecureQString(QChar ch);
    SecureQString(int size, QChar ch);
    SecureQString(QLatin1String str);
    SecureQString(const QString& other);
    SecureQString(const SecureQString& other);
    SecureQString(QString&& other);
    SecureQString(SecureQString&& other);
    SecureQString(const char* str);
    SecureQString(const QByteArray& ba);
    SecureQString(const SecureQByteArray& ba);
    virtual ~SecureQString();
    SecureQString& operator=(const SecureQString& other);
};
*/
