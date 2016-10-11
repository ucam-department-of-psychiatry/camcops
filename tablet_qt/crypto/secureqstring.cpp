#include "secureqstring.h"
// #include "secureqbytearray.h"

/*

SecureQString::SecureQString()
{
}


SecureQString::SecureQString(const QChar* unicode, int size) :
    QString(unicode, size)
{
}


SecureQString::SecureQString(QChar ch) :
    QString(ch)
{
}


SecureQString::SecureQString(int size, QChar ch) :
    QString(size, ch)
{
}


SecureQString::SecureQString(QLatin1String str) :
    QString(str)
{
}


SecureQString::SecureQString(const QString& other) :
    QString(other)
{
}


SecureQString::SecureQString(const SecureQString& other) :
    QString(other)
{
}


SecureQString::SecureQString(QString&& other) :
    QString(other)
{
}


SecureQString::SecureQString(SecureQString&& other) :
    QString(other)
{
}


SecureQString::SecureQString(const char* str) :
    QString(str)
{
}


SecureQString::SecureQString(const QByteArray& ba) :
    QString(ba)
{
}


SecureQString::SecureQString(const SecureQByteArray& ba) :
    QString(ba)
{
}

SecureQString::~SecureQString()
{
    // Wipe it with zeros.
    for (int i = 0; i < length(); ++i) {
        (*this)[i] = 0;
    }
}

SecureQString& SecureQString::operator=(const SecureQString& other)
{
    // https://en.wikipedia.org/wiki/Rule_of_three_(C%2B%2B_programming)
    SecureQString tmp(other);         // re-use copy-constructor
    *this = std::move(tmp); // re-use move-assignment
    return *this;
}

*/
