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


from typing import Any, ClassVar, Dict, List, Optional

from libversion import ANY_IS_PATCH, P_IS_PATCH, version_compare


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
    # remove package
    REMOVE: ClassVar[int] = 1 << 0

    # devel version
    DEVEL: ClassVar[int] = 1 << 1

    # ignored variants
    IGNORE: ClassVar[int] = 1 << 2
    INCORRECT: ClassVar[int] = 1 << 3
    UNTRUSTED: ClassVar[int] = 1 << 4
    NOSCHEME: ClassVar[int] = 1 << 5

    ANY_IGNORED: ClassVar[int] = IGNORE | INCORRECT | UNTRUSTED | NOSCHEME

    ROLLING: ClassVar[int] = 1 << 7  # is processed differently than other ignoreds

    # forced classes
    OUTDATED: ClassVar[int] = 1 << 8
    LEGACY: ClassVar[int] = 1 << 9

    # version special flags
    P_IS_PATCH: ClassVar[int] = 1 << 10
    ANY_IS_PATCH: ClassVar[int] = 1 << 11

    TRACE: ClassVar[int] = 1 << 12

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


class Package:
    __slots__ = [
        # parsed, immutable
        'repo',
        'family',
        'subrepo',

        'name',
        'basename',
        'keyname',
        'visiblename',
        'projectname_seed',

        'origversion',
        'rawversion',

        'arch',

        'maintainers',
        'category',
        'comment',
        'homepage',
        'licenses',
        'downloads',

        'extrafields',

        # calculated
        'effname',

        'version',
        'versionclass',

        'flags',
        'shadow',

        'flavors',
    ]

    repo: str
    family: str
    subrepo: Optional[str]

    name: Optional[str]
    basename: Optional[str]
    keyname: Optional[str]
    visiblename: str
    projectname_seed: str

    origversion: str
    rawversion: str

    arch: Optional[str]

    maintainers: List[str]
    category: Optional[str]
    comment: Optional[str]
    homepage: Optional[str]
    licenses: List[str]
    downloads: List[str]

    extrafields: Dict[str, str]

    effname: str

    version: str
    versionclass: int

    flags: int
    shadow: bool
    flavors: List[str]

    def __init__(self, *,
                 repo: str,
                 family: str,

                 visiblename: str,
                 projectname_seed: str,
                 effname: str,

                 version: str,
                 origversion: str,
                 rawversion: str,

                 versionclass: int,

                 subrepo: Optional[str] = None,

                 name: Optional[str] = None,
                 basename: Optional[str] = None,
                 keyname: Optional[str] = None,

                 arch: Optional[str] = None,

                 maintainers: Optional[List[str]] = None,
                 category: Optional[str] = None,
                 comment: Optional[str] = None,
                 homepage: Optional[str] = None,
                 licenses: Optional[List[str]] = None,
                 downloads: Optional[List[str]] = None,

                 extrafields: Optional[Dict[str, str]] = None,

                 flags: int = 0,
                 shadow: bool = False,
                 flavors: Optional[List[str]] = None):
        # parsed, immutable
        self.repo = repo
        self.family = family
        self.subrepo = subrepo

        self.name = name
        self.basename = basename
        self.keyname = keyname
        self.visiblename = visiblename
        self.projectname_seed = projectname_seed

        self.origversion = origversion
        self.rawversion = rawversion

        self.arch = arch

        self.maintainers = maintainers if maintainers else []
        self.category = category
        self.comment = comment
        self.homepage = homepage
        self.licenses = licenses if licenses else []
        self.downloads = downloads if downloads else []

        self.extrafields = extrafields if extrafields else {}

        # calculated
        self.effname = effname

        self.version = version
        self.versionclass = versionclass

        self.flags = flags
        self.shadow = shadow

        self.flavors = flavors if flavors else []

    def check_format(self) -> bool:
        # check
        for slot in self.__slots__:
            if not hasattr(self, slot):
                return False

        return True

    # setters
    def set_flag(self, flag: int, isset: bool = True) -> None:
        if isset:
            self.flags |= flag
        else:
            self.flags &= ~flag

    # getters
    def has_flag(self, flag: int) -> bool:
        return bool(self.flags & flag)

    # other helper methods
    def version_compare(self, other: 'Package') -> int:
        self_metaorder = PackageFlags.get_metaorder(self.flags)
        other_metaorder = PackageFlags.get_metaorder(other.flags)

        if self_metaorder < other_metaorder:
            return -1
        if self_metaorder > other_metaorder:
            return 1

        return version_compare(
            self.version,
            other.version,
            ((self.flags & PackageFlags.P_IS_PATCH) and P_IS_PATCH) |
            ((self.flags & PackageFlags.ANY_IS_PATCH) and ANY_IS_PATCH),
            ((other.flags & PackageFlags.P_IS_PATCH) and P_IS_PATCH) |
            ((other.flags & PackageFlags.ANY_IS_PATCH) and ANY_IS_PATCH)
        )

    def __repr__(self) -> str:
        return 'Package(repo={}, name={}, version={})'.format(self.repo, self.name, self.version)

    # XXX: add signature to this, see https://github.com/python/mypy/issues/6523
    @property
    def __dict__(self):  # type: ignore
        return {slot: getattr(self, slot) for slot in self.__slots__}

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Package):
            return NotImplemented
        return all((getattr(self, slot) == getattr(other, slot) for slot in self.__slots__))
