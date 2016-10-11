#pragma once
#include <QByteArray>

using SecureQByteArray = QByteArray;

/*
class SecureQByteArray : public QByteArray
{
    // Version of QByteArray that explicitly wipes itself on destruction.
public:
    SecureQByteArray();
    SecureQByteArray(const char* str);
    SecureQByteArray(const char* data, int size);
    SecureQByteArray(int size, char ch);
    SecureQByteArray(const QByteArray& other);
    SecureQByteArray(const SecureQByteArray& other);
    virtual ~SecureQByteArray();
};
*/
