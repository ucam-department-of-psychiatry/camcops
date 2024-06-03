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

#include <QTemporaryFile>
#include <QtTest/QtTest>

#include "db/databasemanager.h"
#include "db/sqlcipherdriver.h"
#include "db/whichdb.h"

class TestDatabaseManager: public QObject
{
    Q_OBJECT

private slots:
    void testCanConnectToEncryptedDatabase();

};


void TestDatabaseManager::testCanConnectToEncryptedDatabase()
{
    QSqlDatabase::registerSqlDriver(whichdb::SQLCIPHER,
                                    new QSqlDriverCreator<SQLCipherDriver>);

    auto plain_file = QTemporaryFile();
    plain_file.open();
    qInfo() << "Plain file:" << plain_file.fileName();
    auto plain_manager = DatabaseManager(plain_file.fileName(), "plain");
    QVERIFY(plain_manager.canReadDatabase());

    auto encrypted_file = QTemporaryFile();
    encrypted_file.open();
    qInfo() << "Encrypted file:" << encrypted_file.fileName();
    plain_manager.encryptToAnother(encrypted_file.fileName(), "password");

    auto encrypted_manager = DatabaseManager(encrypted_file.fileName(), "encrypted");
    QVERIFY(!encrypted_manager.canReadDatabase());

    encrypted_manager.decrypt("password");
    QVERIFY(encrypted_manager.canReadDatabase());
}

QTEST_MAIN(TestDatabaseManager)

#include "testdatabasemanager.moc"
