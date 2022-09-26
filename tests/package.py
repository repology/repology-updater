#!/usr/bin/env python3
#
# Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
#
# This file is part of repology
#
# repology is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# repology is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with repology.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from typing import Any

import pytest

from repology.package import Package
from repology.packagemaker import NameType, PackageFactory


def spawn_package(
    *,
    name: str = 'dummyname',
    version: str = '1.0',
    repo: str = 'dummyrepo',
    flags: int = 0,
    family: str | None = None,
    comment: str | None = None,
    category: str | None = None,
    maintainers: list[str] | None = None,
    flavors: list[str] | None = None,
    branch: str | None = None,
    links: list[tuple[int, str]] | None = None,
) -> Package:
    m = PackageFactory().begin()

    m.add_name(name, NameType.GENERIC_SRCBIN_NAME)
    m.set_version(version)

    m.set_flags(flags)
    m.set_summary(comment)
    m.add_categories(category)
    m.add_maintainers(maintainers)

    if links:
        for link_type, url in links:
            m.add_links(link_type, url)

    p = m.spawn(repo=repo, family=family if family is not None else repo)

    if flavors is not None:
        p.flavors.extend(flavors)

    if branch is not None:
        p.branch = branch

    return p


class PackageSample:
    package: Package
    expectations: dict[str, Any]

    def __init__(self, **pkgargs: Any) -> None:
        self.package = spawn_package(**pkgargs)
        self.expectations = {}

    def expect(self, **expectations: Any) -> 'PackageSample':
        self.expectations = expectations
        return self

    def check(self, test: unittest.TestCase) -> None:
        for k, v in self.expectations.items():
            test.assertEqual(getattr(self.package, k), v, msg=f'{k} of {self.package}')

    def check_pytest(self) -> None:
        __tracebackhide__ = True

        for key, expected in self.expectations.items():
            actual = getattr(self.package, key)

            if actual != expected:
                pytest.fail(f'field "{key}" value "{actual}" != expected "{expected}" for {self.package}')
