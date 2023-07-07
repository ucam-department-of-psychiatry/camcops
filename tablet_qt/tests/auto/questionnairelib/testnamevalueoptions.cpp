#include <QtTest/QtTest>

#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/namevaluepair.h"


class TestNameValueOptions: public QObject
{
    Q_OBJECT

private slots:
    void testInitializedWithList();
};


void TestNameValueOptions::testInitializedWithList()
{
    NameValueOptions options{
        {"A", 1},
        {"B", 2},
        {"C", 3},
    };

    QVERIFY(options.nameFromPosition(0) == "A");
    QVERIFY(options.valueFromPosition(0) == 1);
    QVERIFY(options.nameFromPosition(1) == "B");
    QVERIFY(options.valueFromPosition(1) == 2);
    QVERIFY(options.nameFromPosition(2) == "C");
    QVERIFY(options.valueFromPosition(2) == 3);
}

QTEST_MAIN(TestNameValueOptions)

#include "testnamevalueoptions.moc"
