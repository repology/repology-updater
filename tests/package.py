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

# mypy: no-disallow-untyped-calls

import unittest
from typing import Any, Optional

from repology.package import Package
from repology.packagemaker import NameType, PackageFactory


def spawn_package(
    *,
    name: str = 'dummyname',
    version: str = '0',
    repo: str = 'dummyrepo',
    flags: int = 0,
    family: Optional[str] = None,
    comment: Optional[str] = None,
    category: Optional[str] = None,
    maintainers: Optional[list[str]] = None,
    flavors: Optional[list[str]] = None,
    branch: Optional[str] = None,
    links: Optional[list[tuple[int, str]]] = None,
) -> Package:
    m = PackageFactory().begin()

    m.add_name(name, NameType.GENERIC_GEN_NAME)
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
            test.assertEqual(getattr(self.package, k), v, msg='{} of {}'.format(k, self.package))
