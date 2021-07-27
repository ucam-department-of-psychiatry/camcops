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

    QVERIFY(options.atIndex(0).name() == "A");
    QVERIFY(options.atIndex(0).value() == 1);
    QVERIFY(options.atIndex(1).name() == "B");
    QVERIFY(options.atIndex(1).value() == 2);
    QVERIFY(options.atIndex(2).name() == "C");
    QVERIFY(options.atIndex(2).value() == 3);
}

QTEST_MAIN(TestNameValueOptions)

#include "testnamevalueoptions.moc"
