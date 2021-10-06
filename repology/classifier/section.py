# Copyright (C) 2016-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from dataclasses import dataclass
from typing import Callable, Optional

from repology.classifier.group import VersionGroup
from repology.package import Package, PackageStatus


@dataclass
class Section:
    GuardFn = Callable[[VersionGroup], bool]

    name: str
    newest_status: int
    guard: GuardFn | None = None
    next_section: Optional['Section'] = None

    first_package: Package | None = None
    first_package_alt: Package | None = None
    last_package: Package | None = None

    def add_package(self, package: Package, alt: bool = False) -> None:
        if self.first_package_alt is None:
            self.first_package_alt = package
        if self.first_package is None and not alt:
            self.first_package = package

        self.last_package = package

    def preceeds_package(self, package: Package) -> bool:
        return self.last_package.version_compare(package) > 0 if self.last_package else False

    def follows_package(self, package: Package, alt: bool = False) -> bool:
        first_package = self.first_package_alt if alt else self.first_package
        return first_package.version_compare(package) < 0 if first_package else False

    def contains_package(self, package: Package, alt: bool = False) -> bool:
        first_package = self.first_package_alt if alt else self.first_package
        return (
            first_package is not None
            and first_package.version_compare(package) >= 0
            and self.last_package.version_compare(package) <= 0  # type: ignore  # (last_package is always set if any of first_package* is)
        )

    def is_empty(self) -> bool:
        return self.last_package is None

    def compared_to_best(self, package: Package, alt: bool = False) -> int:
        if alt:
            return package.version_compare(self.first_package_alt) if self.first_package_alt else 1
        else:
            return package.version_compare(self.first_package) if self.first_package else 1

    def is_suitable_for_group(self, group: VersionGroup) -> bool:
        return not self.guard or self.guard(group)

    def get_next_section(self) -> 'Section':
        assert(self.next_section)
        return self.next_section

    def __repr__(self) -> str:
        if self.first_package is not None and self.first_package is self.first_package_alt:
            assert(self.last_package)
            return f'Section("{self.name}", versions=[{self.first_package.version}, {self.last_package.version}])'
        elif self.first_package is not None:
            assert(self.last_package)
            assert(self.first_package_alt)
            return f'Section("{self.name}", versions=[{self.first_package.version} ({self.first_package_alt.version}), {self.last_package.version}])'
        elif self.first_package_alt is not None:
            assert(self.last_package)
            return f'Section("{self.name}", versions=[({self.first_package_alt.version}), {self.last_package.version}])'
        else:
            return f'Section("{self.name}", empty)'


def generate_sections() -> list[Section]:
    sections = [
        Section(
            'devel',
            PackageStatus.DEVEL,
            lambda section: section.is_devel
        ),
        Section(
            'stable',
            PackageStatus.NEWEST,
        ),
    ]

    for section, next_section in zip(sections, sections[1:]):
        section.next_section = next_section

    # last section must not have a guard as there's no more
    # sections to fall through to
    assert sections[-1].guard is None

    return sections
