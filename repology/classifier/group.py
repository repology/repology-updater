# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional, cast

from repology.package import Package, PackageFlags


def _group_packages_by_version(packages: Iterable[Package]) -> Iterator[list[Package]]:
    """Group packages by version.

    Groups a sequence of packages sorted by version into
    a sequence of lists, each containing packages with
    equally compared version"""

    current: list[Package] = []

    for package in packages:
        if not current:
            current = [package]
        elif current[0].version_compare(package) == 0:
            current.append(package)
        else:
            yield current
            current = [package]

    if current:
        yield current


@dataclass
class VersionGroup:
    """A set of equally versioned packages with some aggregate values."""

    all_flags: int = 0
    is_devel: bool = False
    totally_ignored: bool = False
    packages: list[Package] = field(default_factory=list)
    branches: set[Optional[str]] = field(default_factory=set)


def group_packages(packages: Iterable[Package], suppress_ignore: bool = True) -> Iterator[VersionGroup]:
    for packages in _group_packages_by_version(packages):
        all_flags = 0
        has_non_devel = False
        totally_ignored = not suppress_ignore
        branches = set()

        for package in packages:
            all_flags |= package.flags

            if not package.has_flag(PackageFlags.ANY_IGNORED):
                totally_ignored = False

            if not package.has_flag(PackageFlags.DEVEL | PackageFlags.WEAK_DEVEL):
                has_non_devel = True

            branches.add(package.branch)

        if all_flags & PackageFlags.RECALLED:
            totally_ignored = True

        is_devel = cast(
            bool,
            (
                all_flags & PackageFlags.DEVEL or (
                    all_flags & PackageFlags.WEAK_DEVEL and not has_non_devel
                )
            ) and not all_flags & PackageFlags.STABLE
        )

        yield VersionGroup(
            all_flags=all_flags,
            is_devel=is_devel,
            totally_ignored=totally_ignored,
            packages=packages,
            branches=branches,
        )
