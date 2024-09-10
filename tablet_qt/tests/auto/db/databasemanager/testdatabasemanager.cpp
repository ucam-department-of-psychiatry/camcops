/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#include <QDir>
#include <QFileInfo>
#include <QTemporaryFile>
#include <QtTest/QtTest>

#include "db/databasemanager.h"
#include "db/sqlcipherdriver.h"
#include "db/whichdb.h"

const QString PLAIN_CONNECTION_NAME("plain");
const QString ENCRYPTED_CONNECTION_NAME("encrypted");
const QString RIGHT_PASSWORD("password");
const QString WRONG_PASSWORD("wrongpassword");
const QString
    V3_ENCRYPTED_TEST_DATABASE("encrypted_test_database_v3.20.1.sqlite");
const QString
    V4_ENCRYPTED_TEST_DATABASE("encrypted_test_database_v4.5.5.sqlite");

class TestDatabaseManager : public QObject
{
    Q_OBJECT

private:
    QString m_fixtures_dir;
    bool openFixture(const QString filename, QTemporaryFile& test_db);
    // Call this to run a test with DatabaseManager threaded or not from
    // the method <name of original test method>_data().
    // See corresponding QFETCH() in the test itself.
    void threadedData();

private slots:
    void initTestCase();
    // All tests are run twice: threaded and not threaded
    void testCanEncryptPlainDatabase();
    void testCanEncryptPlainDatabase_data();
    void testCanConnectToEncryptedDatabase();
    void testCanConnectToEncryptedDatabase_data();
    void testCanConnectToEncryptedDatabaseOnSecondAttempt();
    void testCanConnectToEncryptedDatabaseOnSecondAttempt_data();
    void testCanConnectToEncryptedV3Database();
    void testCanConnectToEncryptedV3Database_data();
};

void TestDatabaseManager::initTestCase()
{
    QSqlDatabase::
        registerSqlDriver(whichdb::SQLCIPHER, new QSqlDriverCreator<SQLCipherDriver>);

    const QString this_dir = QFileInfo(__FILE__).dir().absolutePath();
    m_fixtures_dir = this_dir + QDir::separator() + "fixtures";
}

void TestDatabaseManager::testCanEncryptPlainDatabase()
{
    QFETCH(bool, threaded);

    auto plain_file = QTemporaryFile();
    plain_file.open();
    auto plain_manager = DatabaseManager(
        plain_file.fileName(), PLAIN_CONNECTION_NAME, whichdb::DBTYPE, threaded
    );
    QVERIFY(plain_manager.canReadDatabase());

    auto encrypted_file = QTemporaryFile();
    encrypted_file.open();
    plain_manager.encryptToAnother(encrypted_file.fileName(), RIGHT_PASSWORD);

    auto encrypted_manager = DatabaseManager(
        encrypted_file.fileName(),
        ENCRYPTED_CONNECTION_NAME,
        whichdb::DBTYPE,
        threaded
    );
    QVERIFY(!encrypted_manager.canReadDatabase());

    QVERIFY(encrypted_manager.decrypt(RIGHT_PASSWORD));
}

void TestDatabaseManager::testCanEncryptPlainDatabase_data()
{
    threadedData();
}

void TestDatabaseManager::testCanConnectToEncryptedDatabase()
{
    QFETCH(bool, threaded);

    QTemporaryFile v4_test_file;
    QVERIFY(openFixture(V4_ENCRYPTED_TEST_DATABASE, v4_test_file));

    auto manager = DatabaseManager(
        v4_test_file.fileName(),
        ENCRYPTED_CONNECTION_NAME,
        whichdb::DBTYPE,
        threaded
    );
    QVERIFY(!manager.canReadDatabase());
    QVERIFY(manager.decrypt(RIGHT_PASSWORD));
}

void TestDatabaseManager::testCanConnectToEncryptedDatabase_data()
{
    threadedData();
}

void TestDatabaseManager::testCanConnectToEncryptedDatabaseOnSecondAttempt()
{
    QFETCH(bool, threaded);

    QTemporaryFile v4_test_file;
    QVERIFY(openFixture(V4_ENCRYPTED_TEST_DATABASE, v4_test_file));

    auto manager = DatabaseManager(
        v4_test_file.fileName(),
        ENCRYPTED_CONNECTION_NAME,
        whichdb::DBTYPE,
        threaded
    );
    QVERIFY(!manager.canReadDatabase());
    QVERIFY(!manager.decrypt(WRONG_PASSWORD));
    QVERIFY(manager.decrypt(RIGHT_PASSWORD));
}

void TestDatabaseManager::
    testCanConnectToEncryptedDatabaseOnSecondAttempt_data()
{
    threadedData();
}

void TestDatabaseManager::testCanConnectToEncryptedV3Database()
{
    QFETCH(bool, threaded);
    // Should fail initially with key and then migrate to V4
    // before trying again.
    QTemporaryFile v3_test_file;

    QVERIFY(openFixture(V3_ENCRYPTED_TEST_DATABASE, v3_test_file));

    auto manager = DatabaseManager(
        v3_test_file.fileName(),
        ENCRYPTED_CONNECTION_NAME,
        whichdb::DBTYPE,
        threaded
    );
    QVERIFY(!manager.canReadDatabase());
    QVERIFY(manager.decrypt(RIGHT_PASSWORD));
}

void TestDatabaseManager::testCanConnectToEncryptedV3Database_data()
{
    threadedData();
}

bool TestDatabaseManager::openFixture(
    const QString filename, QTemporaryFile& test_db
)
{
    // Copy fixture to temporary file so we don't change the original
    QFile original_test_db
        = QFile(m_fixtures_dir + QDir::separator() + filename);
    if (!original_test_db.open(QIODevice::ReadOnly)) {
        qDebug() << "Failed to open " << original_test_db.fileName();

        return false;
    }

    if (!test_db.open()) {
        qDebug() << "Failed to open temporary file";

        return false;
    }

    QByteArray data = original_test_db.readAll();
    const int num_written = test_db.write(data);
    if (num_written <= 0) {
        qDebug() << "Failed to write anything to temporary file";

        return false;
    }
    test_db.close();
    original_test_db.close();

    return true;
}

void TestDatabaseManager::threadedData()
{
    QTest::addColumn<bool>("threaded");
    QTest::newRow("threaded") << true;
    QTest::newRow("not threaded") << false;
}


QTEST_MAIN(TestDatabaseManager)

#include "testdatabasemanager.moc"
