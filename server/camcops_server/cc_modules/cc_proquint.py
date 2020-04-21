"""
camcops_server/cc_modules/cc_proquint.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.

===============================================================================

Convert integers into Pronounceable Quintuplets (proquints)
https://arxiv.org/html/0901.4016

Based on https://github.com/dsw/proquint, which has the following licence:

--8<---------------------------------------------------------------------------

Copyright (c) 2009 Daniel S. Wilkerson
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in
    the documentation and/or other materials provided with the
    distribution.

    Neither the name of Daniel S. Wilkerson nor the names of its
    contributors may be used to endorse or promote products derived
    from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

--8<---------------------------------------------------------------------------


"""
import random
import uuid
from unittest import TestCase


SIZE_OF_VOWEL = 2
SIZE_OF_CONSONANT = 4


class InvalidProquintException(Exception):
    pass


def proquint_from_uuid(uuid_obj: uuid.UUID) -> str:
    return proquint_from_int(uuid_obj.int, 128)


def proquint_from_int(int_value: int,
                      size_in_bits: int) -> str:
    """Convert integer value into proquint

    >>> proquint_from_int(0x7f000001, 32)
    lusab-babad

    0x7f000001 in binary is:
    0011 1111 0000 0000 - 0000 0000 0000 0001

    grouped into alternating 4 and 2 bit values:

    cons vo cons vo cons - cons vo cons vo cons
    0011 11 1100 00 0000 - 0000 00 0000 00 0001

       l  u    s  a    b -    b  a    b  a    d

    Args:
        int_value:
             integer value to encode
        size_in_bits:
             size of integer in bits (must be a multiple of 16)
    Returns:
        proquint string identifier
    """
    proquint = []

    if size_in_bits % 16 != 0:
        raise ValueError(
            f"size_in_bits ({size_in_bits}) must be a multiple of 16"
        )

    for i in range(size_in_bits // 16):
        proquint.insert(0, _proquint_from_int16(int_value & 0xffff))

        int_value >>= 16

    return "-".join(proquint)


def _proquint_from_int16(int16_value: int) -> str:
    consonants = "bdfghjklmnprstvz"
    vowels = "aiou"

    proquint = []
    for i in range(5):
        if i & 1:
            letters = vowels
            mask = 0x3
            shift = SIZE_OF_VOWEL
        else:
            letters = consonants
            mask = 0xf
            shift = SIZE_OF_CONSONANT

        index = int16_value & mask
        proquint.insert(0, letters[index])
        int16_value >>= shift

    return ''.join(proquint)


def uuid_from_proquint(proquint: str) -> uuid.UUID:
    int_value = int_from_proquint(proquint)

    return uuid.UUID(int=int_value)


def int_from_proquint(proquint: str) -> int:
    """Convert proquint string into integer.

    >>> hex(int_from_proquint('lusab-babad'))
    '0x7F000001'

       l    u    s    a    b -    b    a    b    a    d
     0x7  0x3  0xc  0x0  0x0 -  0x0  0x0  0x0  0x0  0x1

    0111   11 1100   00 0000 - 0000   00 0000   00 0001
    0111    1111   0000 0000 - 0000    0000   0000 0001
     0x7     0xf    0x0  0x0 -  0x0     0x0    0x0  0x1

    Args:
        proquint:
            string to decode
    Returns:
        converted integer value
    """

    consonant_values = {
        'b': 0x0, 'd': 0x1, 'f': 0x2, 'g': 0x3,
        'h': 0x4, 'j': 0x5, 'k': 0x6, 'l': 0x7,
        'm': 0x8, 'n': 0x9, 'p': 0xa, 'r': 0xb,
        's': 0xc, 't': 0xd, 'v': 0xe, 'z': 0xf,
    }

    vowel_values = {
        'a': 0x0, 'i': 0x1, 'o': 0x2, 'u': 0x3,
    }

    int_value = 0

    for word in proquint.split("-"):
        for (i, c) in enumerate(word):
            if i & 1:
                lookup_table = vowel_values
                shift = SIZE_OF_VOWEL
            else:
                lookup_table = consonant_values
                shift = SIZE_OF_CONSONANT

            value = lookup_table.get(c)

            if value is None:
                raise InvalidProquintException(
                    f"'{proquint}' is not a valid proquint"
                )

            int_value <<= shift
            int_value += value

    return int_value


# =============================================================================
# Unit tests
# =============================================================================

class ProquintTest(TestCase):
    def test_int_encoded_as_proquint(self):
        self.assertEqual(proquint_from_int(0x7f000001, 32), "lusab-babad")

    def test_uuid_encoded_as_proquint(self):
        self.assertEqual(
            proquint_from_uuid(
                uuid.UUID("6457cb90-1ca0-47a7-9f40-767567819bee")
            ),
            "kidil-sovib-dufob-hivol-nutab-linuj-kivad-nozov"
        )

    def test_proquint_decoded_as_int(self):
        self.assertEqual(int_from_proquint("lusab-babad"), 0x7f000001)

    def test_proquint_decoded_as_uuid(self):
        self.assertEqual(
            uuid_from_proquint(
                "kidil-sovib-dufob-hivol-nutab-linuj-kivad-nozov"
            ),
            uuid.UUID("6457cb90-1ca0-47a7-9f40-767567819bee")
        )

    def test_ints_converted_to_proquints_and_back(self):
        for bits in [16, 32, 48, 64, 80, 96, 128, 256]:
            for i in range(1000):
                random_int = random.getrandbits(bits)

                encoded = proquint_from_int(random_int, bits)

                num_expected_chunks = bits / 16
                num_expected_dashes = num_expected_chunks - 1
                expected_proquint_length = (5 * num_expected_chunks
                                            + num_expected_dashes)
                self.assertEqual(len(encoded), expected_proquint_length)

                decoded = int_from_proquint(encoded)

                self.assertEqual(
                    decoded,
                    random_int,
                    msg=(f"Conversion failed for {random_int}, "
                         f"encoded={encoded}, decoded={decoded} ")
                )

    def test_raises_when_bits_not_multiple_of_16(self):
        with self.assertRaises(ValueError) as cm:
            proquint_from_int(0, 5)

        self.assertEqual(str(cm.exception),
                         "size_in_bits (5) must be a multiple of 16")

    def test_raises_when_proquint_has_invalid_chars(self):
        with self.assertRaises(InvalidProquintException) as cm:
            int_from_proquint("lusab-rrrrr")

        self.assertEqual(str(cm.exception),
                         "'lusab-rrrrr' is not a valid proquint")

    def test_raises_when_proquint_has_chars_in_wrong_order(self):
        with self.assertRaises(InvalidProquintException) as cm:
            int_from_proquint("lusab-abadu")

        self.assertEqual(str(cm.exception),
                         "'lusab-abadu' is not a valid proquint")
