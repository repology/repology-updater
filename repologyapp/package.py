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
from typing import ClassVar, Dict, List, Optional, TypeVar

from libversion import ANY_IS_PATCH, P_IS_PATCH, version_compare

__all__ = [
    'AnyPackageDataMinimal',
    'AnyPackageDataSummarizable',
    'PackageDataMinimal',
    'PackageDataSummarizable',
    'PackageDataDetailed',
    'PackageFlags',
    'PackageStatus',
]


class PackageStatus:
    # XXX: better make this state innrepresentable by introducing an intermediate
    # type for inprocessed package, missing versionclass and other fields which
    # are filled later
    UNPROCESSED: ClassVar[int] = 0

    NEWEST: ClassVar[int] = 1
    OUTDATED: ClassVar[int] = 2
    IGNORED: ClassVar[int] = 3
    UNIQUE: ClassVar[int] = 4
    DEVEL: ClassVar[int] = 5
    LEGACY: ClassVar[int] = 6
    INCORRECT: ClassVar[int] = 7
    UNTRUSTED: ClassVar[int] = 8
    NOSCHEME: ClassVar[int] = 9
    ROLLING: ClassVar[int] = 10

    @staticmethod
    def is_ignored(val: int) -> bool:
        """Return whether a specified val is equivalent to ignored."""
        return (val == PackageStatus.IGNORED or
                val == PackageStatus.INCORRECT or
                val == PackageStatus.UNTRUSTED or
                val == PackageStatus.NOSCHEME or
                val == PackageStatus.ROLLING)

    @staticmethod
    def as_string(val: int) -> str:
        """Return string representation of a version class."""
        return {
            PackageStatus.NEWEST: 'newest',
            PackageStatus.OUTDATED: 'outdated',
            PackageStatus.IGNORED: 'ignored',
            PackageStatus.UNIQUE: 'unique',
            PackageStatus.DEVEL: 'devel',
            PackageStatus.LEGACY: 'legacy',
            PackageStatus.INCORRECT: 'incorrect',
            PackageStatus.UNTRUSTED: 'untrusted',
            PackageStatus.NOSCHEME: 'noscheme',
            PackageStatus.ROLLING: 'rolling',
        }[val]


class PackageFlags:
    REMOVE: ClassVar[int] = 1 << 0
    DEVEL: ClassVar[int] = 1 << 1
    IGNORE: ClassVar[int] = 1 << 2
    INCORRECT: ClassVar[int] = 1 << 3
    UNTRUSTED: ClassVar[int] = 1 << 4
    NOSCHEME: ClassVar[int] = 1 << 5
    ROLLING: ClassVar[int] = 1 << 7
    OUTDATED: ClassVar[int] = 1 << 8
    LEGACY: ClassVar[int] = 1 << 9
    P_IS_PATCH: ClassVar[int] = 1 << 10
    ANY_IS_PATCH: ClassVar[int] = 1 << 11
    TRACE: ClassVar[int] = 1 << 12
    WEAK_DEVEL: ClassVar[int] = 1 << 13
    STABLE: ClassVar[int] = 1 << 14
    ALTVER: ClassVar[int] = 1 << 15

    ANY_IGNORED: ClassVar[int] = IGNORE | INCORRECT | UNTRUSTED | NOSCHEME

    @staticmethod
    def get_metaorder(val: int) -> int:
        """Return a higher order version sorting key based on flags.

        E.g. rolling versions always precede normal versions,
        and normal versions always precede outdated versions

        Within a specific metaorder versions are compared normally
        """
        if val & PackageFlags.ROLLING:
            return 1
        if val & PackageFlags.OUTDATED:
            return -1
        return 0

    @staticmethod
    def as_string(val: int) -> str:
        """Return string representation of a flags combination."""
        if val == 0:
            return '-'

        return '|'.join(
            name for var, name in {
                PackageFlags.REMOVE: 'REMOVE',
                PackageFlags.DEVEL: 'DEVEL',
                PackageFlags.IGNORE: 'IGNORE',
                PackageFlags.INCORRECT: 'INCORRECT',
                PackageFlags.UNTRUSTED: 'UNTRUSTED',
                PackageFlags.NOSCHEME: 'NOSCHEME',
                PackageFlags.ROLLING: 'ROLLING',
                PackageFlags.OUTDATED: 'OUTDATED',
                PackageFlags.LEGACY: 'LEGACY',
                PackageFlags.P_IS_PATCH: 'P_IS_PATCH',
                PackageFlags.ANY_IS_PATCH: 'ANY_IS_PATCH',
                PackageFlags.TRACE: 'TRACE',
                PackageFlags.WEAK_DEVEL: 'WEAK_DEVEL',
                PackageFlags.STABLE: 'STABLE',
                PackageFlags.ALTVER: 'ALTVER',
            }.items() if val & var
        )


@dataclass
class PackageDataMinimal:
    repo: str
    family: str

    visiblename: str
    effname: str

    version: str
    versionclass: int

    flags: int


@dataclass
class PackageDataSummarizable(PackageDataMinimal):
    maintainers: List[str]


@dataclass
class PackageDataDetailed(PackageDataSummarizable):
    subrepo: Optional[str]

    name: Optional[str]
    keyname: Optional[str]
    basename: Optional[str]

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
