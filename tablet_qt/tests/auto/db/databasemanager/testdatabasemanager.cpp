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

class TestDatabaseManager: public QObject
{
    Q_OBJECT

private:
    QString m_fixtures_dir;
    bool openFixture(const QString filename, QTemporaryFile& test_db);

private slots:
    void initTestCase();
    void testCanEncryptPlainDatabase();
    void testCanConnectToEncryptedDatabase();
    void testCanConnectToEncryptedDatabaseOnSecondAttempt();
    void testCanConnectToEncryptedV3Database();
};


void TestDatabaseManager::initTestCase()
{
    QSqlDatabase::registerSqlDriver(whichdb::SQLCIPHER,
                                    new QSqlDriverCreator<SQLCipherDriver>);

    const QString this_dir = QFileInfo(__FILE__).dir().absolutePath();
    m_fixtures_dir = this_dir + QDir::separator() +  "fixtures";
}

void TestDatabaseManager::testCanEncryptPlainDatabase()
{
    auto plain_file = QTemporaryFile();
    plain_file.open();
    auto plain_manager = DatabaseManager(plain_file.fileName(), "plain");
    QVERIFY(plain_manager.canReadDatabase());

    auto encrypted_file = QTemporaryFile();
    encrypted_file.open();
    plain_manager.encryptToAnother(encrypted_file.fileName(), "password");

    auto encrypted_manager = DatabaseManager(encrypted_file.fileName(), "test");
    QVERIFY(!encrypted_manager.canReadDatabase());

    QVERIFY(encrypted_manager.decrypt("password"));
}

void TestDatabaseManager::testCanConnectToEncryptedDatabase()
{
    QTemporaryFile v4_test_file;
    QVERIFY(openFixture("encrypted_test_database_v4.5.5.sqlite", v4_test_file));

    auto manager = DatabaseManager(v4_test_file.fileName(), "test");
    QVERIFY(!manager.canReadDatabase());
    QVERIFY(manager.decrypt("password"));
}

void TestDatabaseManager::testCanConnectToEncryptedDatabaseOnSecondAttempt()
{
    QTemporaryFile v4_test_file;
    QVERIFY(openFixture("encrypted_test_database_v4.5.5.sqlite", v4_test_file));

    auto manager = DatabaseManager(v4_test_file.fileName(), "test");
    QVERIFY(!manager.canReadDatabase());
    QVERIFY(!manager.decrypt("wrongpassword"));
    QVERIFY(manager.decrypt("password"));
}

void TestDatabaseManager::testCanConnectToEncryptedV3Database()
{
    // Should migrate to V4
    QTemporaryFile v3_test_file;

    QVERIFY(openFixture("encrypted_test_database_v3.20.1.sqlite", v3_test_file));

    auto manager = DatabaseManager(v3_test_file.fileName(), "test");
    QVERIFY(!manager.canReadDatabase());
    QVERIFY(manager.decrypt("password"));
}


bool TestDatabaseManager::openFixture(const QString filename, QTemporaryFile& test_db)
{
    // Copy fixture to temporary file so we don't change the original
    QFile original_test_db = QFile(m_fixtures_dir + QDir::separator() + filename);
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

QTEST_MAIN(TestDatabaseManager)

#include "testdatabasemanager.moc"
