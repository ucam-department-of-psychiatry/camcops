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

#include <QtTest/QtTest>

#include "lib/filefunc.h"


class TestFileFunc: public QObject
{
    Q_OBJECT

private slots:
    void testTextFileContentsReturnsContentsOfFile();
};


using namespace filefunc;

void TestFileFunc::testTextFileContentsReturnsContentsOfFile()
{
    // https://www.cl.cam.ac.uk/~mgk25/ucs/examples/quickbrown.txt
    const char *text = ""
        "Quizdeltagerne spiste jordbær med fløde, mens cirkusklovnen "
        "Wolther spillede på xylofon."
        "Γαζέες καὶ μυρτιὲς δὲν θὰ βρῶ πιὰ στὸ χρυσαφὶ ξέφωτο."
        "В чащах юга жил бы цитрус? Да, но фальшивый экземпляр!";

    auto file = QTemporaryFile();
    file.open();
    file.write(text);
    file.close();
    QCOMPARE(textfileContents(file.fileName()), QString(text));
}

QTEST_MAIN(TestFileFunc)

#include "testfilefunc.moc"