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

from dataclasses import dataclass
from typing import Dict, List, Optional, TypeVar

from libversion import ANY_IS_PATCH, P_IS_PATCH, version_compare

from repology.package import PackageFlags as PackageFlags
from repology.package import PackageStatus as PackageStatus

__all__ = [
    'AnyPackageDataMinimal',
    'AnyPackageDataSummarizable',
    'PackageDataMinimal',
    'PackageDataSummarizable',
    'PackageDataDetailed',
    'PackageFlags',
    'PackageStatus',
]


@dataclass
class PackageDataMinimal:
    repo: str
    family: str

    name: str
    effname: str

    version: str
    versionclass: int

    flags: int


@dataclass
class PackageDataSummarizable(PackageDataMinimal):
    maintainers: List[str]


@dataclass
class PackageDataDetailed(PackageDataSummarizable):
    basename: Optional[str]
    subrepo: Optional[str]

    origversion: str
    rawversion: str

    category: Optional[str]
    comment: Optional[str]
    homepage: Optional[str]
    licenses: List[str]
    downloads: List[str]

    extrafields: Dict[str, str]


AnyPackageDataMinimal = TypeVar('AnyPackageDataMinimal', bound=PackageDataMinimal)
AnyPackageDataSummarizable = TypeVar('AnyPackageDataSummarizable', bound=PackageDataSummarizable)


def package_version_compare(a: AnyPackageDataMinimal, b: AnyPackageDataMinimal) -> int:
    metaorder_a = 1 if a.flags & PackageFlags.ROLLING else -1 if a.flags & PackageFlags.OUTDATED else 0
    metaorder_b = 1 if b.flags & PackageFlags.ROLLING else -1 if b.flags & PackageFlags.OUTDATED else 0

    if metaorder_a < metaorder_b:
        return -1
    if metaorder_a > metaorder_b:
        return 1

    return version_compare(
        a.version,
        b.version,
        ((a.flags & PackageFlags.P_IS_PATCH) and P_IS_PATCH) |
        ((a.flags & PackageFlags.ANY_IS_PATCH) and ANY_IS_PATCH),
        ((b.flags & PackageFlags.P_IS_PATCH) and P_IS_PATCH) |
        ((b.flags & PackageFlags.ANY_IS_PATCH) and ANY_IS_PATCH)
    )
