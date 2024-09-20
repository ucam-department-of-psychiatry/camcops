"""
camcops_server/cc_modules/cc_testproviders.py

===============================================================================

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

===============================================================================

**Faker test data providers.**

There may be some interest in a Faker Medical community provider if we felt it
was worth the effort.

https://github.com/joke2k/faker/issues/1142

See also duplicate functionality in CRATE: crate_anon/testing/providers.py

"""

from cardinal_pythonlib.nhs import generate_random_nhs_number
from faker import Faker
from faker.providers import BaseProvider
from typing import Any, List


class NhsNumberProvider(BaseProvider):
    def nhs_number(self) -> str:
        return generate_random_nhs_number()


class ChoiceProvider(BaseProvider):
    def random_choice(self, choices: List, **kwargs) -> Any:
        """
        Given a list of choices return a random value
        """
        choices = self.generator.random.choices(choices, **kwargs)

        return choices[0]


class ForenameProvider(BaseProvider):
    """
    Return a forename given the sex of the person
    """

    def forename(self, sex: str) -> str:
        if sex == "M":
            return self.generator.first_name_male()

        if sex == "F":
            return self.generator.first_name_female()

        return self.generator.first_name()[:1]


class HeightProvider(BaseProvider):
    def height_m(self) -> float:
        return float(self.generator.random_int(min=145, max=191) / 100.0)


class MassProvider(BaseProvider):
    def mass_kg(self) -> float:
        return float(self.generator.random_int(min=400, max=1000) / 10.0)


class SexProvider(ChoiceProvider):
    """
    Return a random sex, with realistic distribution.
    """

    def sex(self) -> str:
        return self.random_choice(["M", "F", "X"], weights=[49.8, 49.8, 0.4])


def register_all_providers(fake: Faker) -> None:
    fake.add_provider(ChoiceProvider)
    fake.add_provider(ForenameProvider)
    fake.add_provider(HeightProvider)
    fake.add_provider(MassProvider)
    fake.add_provider(NhsNumberProvider)
    fake.add_provider(SexProvider)
