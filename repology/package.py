# Copyright (C) 2016-2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import pickle
from typing import Any, ClassVar, TypeAlias

from libversion import ANY_IS_PATCH, P_IS_PATCH, version_compare

import xxhash


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
        return (val == PackageStatus.IGNORED
                or val == PackageStatus.INCORRECT
                or val == PackageStatus.UNTRUSTED
                or val == PackageStatus.NOSCHEME
                or val == PackageStatus.ROLLING)

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
    SINK: ClassVar[int] = 1 << 8
    LEGACY: ClassVar[int] = 1 << 9
    P_IS_PATCH: ClassVar[int] = 1 << 10
    ANY_IS_PATCH: ClassVar[int] = 1 << 11
    TRACE: ClassVar[int] = 1 << 12
    WEAK_DEVEL: ClassVar[int] = 1 << 13
    STABLE: ClassVar[int] = 1 << 14
    ALTVER: ClassVar[int] = 1 << 15
    VULNERABLE: ClassVar[int] = 1 << 16
    ALTSCHEME: ClassVar[int] = 1 << 17
    NOLEGACY: ClassVar[int] = 1 << 18
    OUTDATED: ClassVar[int] = 1 << 19
    RECALLED: ClassVar[int] = 1 << 20

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
        if val & PackageFlags.SINK:
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
                PackageFlags.SINK: 'SINK',
                PackageFlags.LEGACY: 'LEGACY',
                PackageFlags.P_IS_PATCH: 'P_IS_PATCH',
                PackageFlags.ANY_IS_PATCH: 'ANY_IS_PATCH',
                PackageFlags.TRACE: 'TRACE',
                PackageFlags.WEAK_DEVEL: 'WEAK_DEVEL',
                PackageFlags.STABLE: 'STABLE',
                PackageFlags.ALTVER: 'ALTVER',
                PackageFlags.VULNERABLE: 'VULNERABLE',
                PackageFlags.ALTSCHEME: 'ALTSCHEME',
                PackageFlags.NOLEGACY: 'NOLEGACY',
                PackageFlags.OUTDATED: 'OUTDATED',
                PackageFlags.RECALLED: 'RECALLED',
            }.items() if val & var
        )


class LinkType:
    UPSTREAM_HOMEPAGE: ClassVar[int] = 0
    UPSTREAM_DOWNLOAD: ClassVar[int] = 1
    UPSTREAM_REPOSITORY: ClassVar[int] = 2
    UPSTREAM_ISSUE_TRACKER: ClassVar[int] = 3
    PROJECT_HOMEPAGE: ClassVar[int] = 4
    PACKAGE_HOMEPAGE: ClassVar[int] = 5
    PACKAGE_DOWNLOAD: ClassVar[int] = 6
    PACKAGE_SOURCES: ClassVar[int] = 7
    PACKAGE_ISSUE_TRACKER: ClassVar[int] = 8
    PACKAGE_RECIPE: ClassVar[int] = 9
    PACKAGE_RECIPE_RAW: ClassVar[int] = 10
    PACKAGE_PATCH: ClassVar[int] = 11
    PACKAGE_PATCH_RAW: ClassVar[int] = 12
    PACKAGE_BUILD_LOG: ClassVar[int] = 13
    PACKAGE_BUILD_LOG_RAW: ClassVar[int] = 14
    PACKAGE_NEW_VERSION_CHECKER: ClassVar[int] = 15
    UPSTREAM_DOCUMENTATION: ClassVar[int] = 16
    UPSTREAM_CHANGELOG: ClassVar[int] = 17
    PROJECT_DOWNLOAD: ClassVar[int] = 18
    UPSTREAM_DONATION: ClassVar[int] = 19  # XXX: to be used sparingly not to provide obsolete funding info
    UPSTREAM_DISCUSSION: ClassVar[int] = 20
    UPSTREAM_COVERAGE: ClassVar[int] = 21
    UPSTREAM_CI: ClassVar[int] = 22
    UPSTREAM_WIKI: ClassVar[int] = 23
    PACKAGE_STATISTICS: ClassVar[int] = 25
    PACKAGE_BUILD_STATUS: ClassVar[int] = 26
    PACKAGE_BUILD_LOGS: ClassVar[int] = 27
    UPSTREAM_DOWNLOAD_PAGE: ClassVar[int] = 28
    OTHER: ClassVar[int] = 99

    @staticmethod
    def as_string(val: int) -> str:
        return {
            LinkType.UPSTREAM_HOMEPAGE: 'UPSTREAM_HOMEPAGE',
            LinkType.UPSTREAM_DOWNLOAD: 'UPSTREAM_DOWNLOAD',
            LinkType.UPSTREAM_REPOSITORY: 'UPSTREAM_REPOSITORY',
            LinkType.UPSTREAM_ISSUE_TRACKER: 'UPSTREAM_ISSUE_TRACKER',
            LinkType.PROJECT_HOMEPAGE: 'PROJECT_HOMEPAGE',
            LinkType.PACKAGE_HOMEPAGE: 'PACKAGE_HOMEPAGE',
            LinkType.PACKAGE_DOWNLOAD: 'PACKAGE_DOWNLOAD',
            LinkType.PACKAGE_SOURCES: 'PACKAGE_SOURCES',
            LinkType.PACKAGE_ISSUE_TRACKER: 'PACKAGE_ISSUE_TRACKER',
            LinkType.PACKAGE_RECIPE: 'PACKAGE_RECIPE',
            LinkType.PACKAGE_RECIPE_RAW: 'PACKAGE_RECIPE_RAW',
            LinkType.PACKAGE_PATCH: 'PACKAGE_PATCH',
            LinkType.PACKAGE_PATCH_RAW: 'PACKAGE_PATCH_RAW',
            LinkType.PACKAGE_BUILD_LOG: 'PACKAGE_BUILD_LOG',
            LinkType.PACKAGE_BUILD_LOG_RAW: 'PACKAGE_BUILD_LOG_RAW',
            LinkType.PACKAGE_NEW_VERSION_CHECKER: 'PACKAGE_NEW_VERSION_CHECKER',
            LinkType.UPSTREAM_DOCUMENTATION: 'UPSTREAM_DOCUMENTATION',
            LinkType.UPSTREAM_CHANGELOG: 'UPSTREAM_CHANGELOG',
            LinkType.PROJECT_DOWNLOAD: 'PROJECT_DOWNLOAD',
            LinkType.UPSTREAM_DONATION: 'UPSTREAM_DONATION',
            LinkType.UPSTREAM_DISCUSSION: 'UPSTREAM_DISCUSSION',
            LinkType.UPSTREAM_COVERAGE: 'UPSTREAM_COVERAGE',
            LinkType.UPSTREAM_CI: 'UPSTREAM_CI',
            LinkType.UPSTREAM_WIKI: 'UPSTREAM_WIKI',
            LinkType.PACKAGE_STATISTICS: 'PACKAGE_STATISTICS',
            LinkType.PACKAGE_BUILD_STATUS: 'PACKAGE_BUILD_STATUS',
            LinkType.PACKAGE_BUILD_LOGS: 'PACKAGE_BUILD_LOGS',
            LinkType.UPSTREAM_DOWNLOAD_PAGE: 'UPSTREAM_DOWNLOAD_PAGE',
            LinkType.OTHER: 'OTHER',
        }[val]

    @staticmethod
    def from_string(val: str) -> int:
        return {
            'UPSTREAM_HOMEPAGE': LinkType.UPSTREAM_HOMEPAGE,
            'UPSTREAM_DOWNLOAD': LinkType.UPSTREAM_DOWNLOAD,
            'UPSTREAM_REPOSITORY': LinkType.UPSTREAM_REPOSITORY,
            'UPSTREAM_ISSUE_TRACKER': LinkType.UPSTREAM_ISSUE_TRACKER,
            'PROJECT_HOMEPAGE': LinkType.PROJECT_HOMEPAGE,
            'PACKAGE_HOMEPAGE': LinkType.PACKAGE_HOMEPAGE,
            'PACKAGE_DOWNLOAD': LinkType.PACKAGE_DOWNLOAD,
            'PACKAGE_SOURCES': LinkType.PACKAGE_SOURCES,
            'PACKAGE_ISSUE_TRACKER': LinkType.PACKAGE_ISSUE_TRACKER,
            'PACKAGE_RECIPE': LinkType.PACKAGE_RECIPE,
            'PACKAGE_RECIPE_RAW': LinkType.PACKAGE_RECIPE_RAW,
            'PACKAGE_PATCH': LinkType.PACKAGE_PATCH,
            'PACKAGE_PATCH_RAW': LinkType.PACKAGE_PATCH_RAW,
            'PACKAGE_BUILD_LOG': LinkType.PACKAGE_BUILD_LOG,
            'PACKAGE_BUILD_LOG_RAW': LinkType.PACKAGE_BUILD_LOG_RAW,
            'PACKAGE_NEW_VERSION_CHECKER': LinkType.PACKAGE_NEW_VERSION_CHECKER,
            'UPSTREAM_DOCUMENTATION': LinkType.UPSTREAM_DOCUMENTATION,
            'UPSTREAM_CHANGELOG': LinkType.UPSTREAM_CHANGELOG,
            'PROJECT_DOWNLOAD': LinkType.PROJECT_DOWNLOAD,
            'UPSTREAM_DONATION': LinkType.UPSTREAM_DONATION,
            'UPSTREAM_DISCUSSION': LinkType.UPSTREAM_DISCUSSION,
            'UPSTREAM_COVERAGE': LinkType.UPSTREAM_COVERAGE,
            'UPSTREAM_CI': LinkType.UPSTREAM_CI,
            'UPSTREAM_WIKI': LinkType.UPSTREAM_WIKI,
            'PACKAGE_STATISTICS': LinkType.PACKAGE_STATISTICS,
            'PACKAGE_BUILD_STATUS': LinkType.PACKAGE_BUILD_STATUS,
            'PACKAGE_BUILD_LOGS': LinkType.PACKAGE_BUILD_LOGS,
            'UPSTREAM_DOWNLOAD_PAGE': LinkType.UPSTREAM_DOWNLOAD_PAGE,
            'OTHER': LinkType.OTHER,
        }[val]

    @staticmethod
    def is_relevant_for_rule_matching(val: int) -> bool:
        return val in [
            LinkType.PROJECT_DOWNLOAD,
            LinkType.PROJECT_HOMEPAGE,
            LinkType.UPSTREAM_DOWNLOAD,
            LinkType.UPSTREAM_HOMEPAGE,
            LinkType.UPSTREAM_REPOSITORY,
        ]


PackageLinkTuple: TypeAlias = tuple[int, str] | tuple[int, str, str]


class Package:
    __slots__ = [
        # parsed, immutable
        'repo',
        'family',
        'subrepo',

        'name',
        'srcname',
        'binname',
        'binnames',
        'trackname',
        'visiblename',
        'projectname_seed',

        'origversion',
        'rawversion',

        'arch',

        'maintainers',
        'category',
        'comment',
        'licenses',

        'extrafields',

        'cpe_vendor',
        'cpe_product',
        'cpe_edition',
        'cpe_lang',
        'cpe_sw_edition',
        'cpe_target_sw',
        'cpe_target_hw',
        'cpe_other',

        'links',

        # calculated
        'effname',

        'version',
        'versionclass',

        'flags',
        'shadow',

        'flavors',
        'branch',
    ]

    _hashable_slots: ClassVar[list[str]] = [slot for slot in __slots__ if slot != 'versionclass']

    repo: str
    family: str
    subrepo: str | None

    name: str | None
    srcname: str | None
    binname: str | None
    binnames: list[str] | None
    trackname: str | None
    visiblename: str
    projectname_seed: str

    origversion: str
    rawversion: str

    arch: str | None

    maintainers: list[str] | None
    category: str | None
    comment: str | None
    licenses: list[str] | None

    extrafields: dict[str, Any] | None

    cpe_vendor: str | None
    cpe_product: str | None
    cpe_edition: str | None
    cpe_lang: str | None
    cpe_sw_edition: str | None
    cpe_target_sw: str | None
    cpe_target_hw: str | None
    cpe_other: str | None

    links: list[PackageLinkTuple] | None

    effname: str

    version: str
    versionclass: int

    flags: int
    shadow: bool
    flavors: list[str]
    branch: str | None

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

                 subrepo: str | None = None,

                 name: str | None = None,
                 srcname: str | None = None,
                 binname: str | None = None,
                 binnames: list[str] | None = None,
                 trackname: str | None = None,

                 arch: str | None = None,

                 maintainers: list[str] | None = None,
                 category: str | None = None,
                 comment: str | None = None,
                 licenses: list[str] | None = None,

                 extrafields: dict[str, Any] | None = None,

                 cpe_vendor: str | None = None,
                 cpe_product: str | None = None,
                 cpe_edition: str | None = None,
                 cpe_lang: str | None = None,
                 cpe_sw_edition: str | None = None,
                 cpe_target_sw: str | None = None,
                 cpe_target_hw: str | None = None,
                 cpe_other: str | None = None,

                 links: list[PackageLinkTuple] | None = None,

                 flags: int = 0,
                 shadow: bool = False,
                 flavors: list[str] | None = None,
                 branch: str | None = None):
        # parsed, immutable
        self.repo = repo
        self.family = family
        self.subrepo = subrepo

        self.name = name
        self.srcname = srcname
        self.binname = binname
        self.binnames = binnames
        self.trackname = trackname
        self.visiblename = visiblename
        self.projectname_seed = projectname_seed

        self.origversion = origversion
        self.rawversion = rawversion

        self.arch = arch

        self.maintainers = maintainers
        self.category = category
        self.comment = comment
        self.licenses = licenses

        self.extrafields = extrafields

        self.cpe_vendor = cpe_vendor
        self.cpe_product = cpe_product
        self.cpe_edition = cpe_edition
        self.cpe_lang = cpe_lang
        self.cpe_sw_edition = cpe_sw_edition
        self.cpe_target_sw = cpe_target_sw
        self.cpe_target_hw = cpe_target_hw
        self.cpe_other = cpe_other

        self.links = links

        # calculated
        self.effname = effname

        self.version = version
        self.versionclass = versionclass

        self.flags = flags
        self.shadow = shadow

        self.flavors = flavors if flavors else []
        self.branch = branch

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
            ((self.flags & PackageFlags.P_IS_PATCH) and P_IS_PATCH)
            | ((self.flags & PackageFlags.ANY_IS_PATCH) and ANY_IS_PATCH),
            ((other.flags & PackageFlags.P_IS_PATCH) and P_IS_PATCH)
            | ((other.flags & PackageFlags.ANY_IS_PATCH) and ANY_IS_PATCH)
        )

    def get_classless_hash(self) -> int:
        return xxhash.xxh64_intdigest(
            # least-overhead stable binary encoding of meaningful Package fields (I could come with)
            pickle.dumps(
                [
                    (slot, value)
                    for slot in Package._hashable_slots
                    if (value := getattr(self, slot, None)) is not None
                ]
            )
        ) & 0x7fffffffffffffff  # to fit into PostgreSQL integer

    def __repr__(self) -> str:
        return f'Package(repo={self.repo}, name={self.name}, version={self.version})'

    # XXX: add signature to this, see https://github.com/python/mypy/issues/6523
    @property
    def __dict__(self):  # type: ignore
        return {slot: getattr(self, slot, None) for slot in self.__slots__}

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Package):
            return NotImplemented
        return all((getattr(self, slot, None) == getattr(other, slot, None) for slot in self.__slots__))
