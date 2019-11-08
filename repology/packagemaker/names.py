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
from typing import ClassVar, Dict, Optional, Tuple


__all__ = ['NameType', 'NameMapper']


class NameType:
    IGNORED: ClassVar[int] = 0  # special type which is always ignored

    GENERIC_PKGNAME: ClassVar[int] = 10

    WIKIDATA_ENTITY: ClassVar[int] = 20
    WIKIDATA_LABEL: ClassVar[int] = 21
    WIKIDATA_REPOLOGY_PROJECT_NAME: ClassVar[int] = 22

    BSD_PKGNAME: ClassVar[int] = 30
    BSD_ORIGIN: ClassVar[int] = 31

    NPACKD_TITLE: ClassVar[int] = IGNORED
    NPACKD_FULLNAME: ClassVar[int] = 41
    NPACKD_LASTNAME: ClassVar[int] = 42

    DEBIAN_PACKAGE: ClassVar[int] = 50
    OPENWRT_SOURCEDIR: ClassVar[int] = 51

    CYGWIN_PACKAGE_NAME: ClassVar[int] = 60
    CYGWIN_SUBPACKAGE_NAME: ClassVar[int] = 61

    WIKI_TITLE: ClassVar[int] = 70
    WIKI_PAGE: ClassVar[int] = 71

    GENTOO_NAME: ClassVar[int] = 80
    GENTOO_FULL_NAME: ClassVar[int] = 81

    # Common pattern "NOBN" = Name + Optional BaseName
    PATTERN_NOBN_NAME: ClassVar[int] = 200
    PATTERN_NOBN_BASENAME: ClassVar[int] = 201

    MSYS2_NAME: ClassVar[int] = PATTERN_NOBN_NAME
    MSYS2_BASENAME: ClassVar[int] = PATTERN_NOBN_BASENAME

    SOLUS_NAME: ClassVar[int] = PATTERN_NOBN_NAME
    SOLUS_SOURCE_NAME: ClassVar[int] = PATTERN_NOBN_BASENAME

    ARCH_NAME: ClassVar[int] = PATTERN_NOBN_NAME
    ARCH_BASENAME: ClassVar[int] = PATTERN_NOBN_BASENAME

    SLITAZ_NAME: ClassVar[int] = PATTERN_NOBN_NAME
    SLITAZ_META: ClassVar[int] = PATTERN_NOBN_BASENAME

    VOID_NAME: ClassVar[int] = PATTERN_NOBN_NAME
    VOID_SOURCE: ClassVar[int] = PATTERN_NOBN_BASENAME


@dataclass
class _NameMapping:
    visiblename: int
    projectname_seed: int

    name: Optional[int] = None
    basename: Optional[int] = None
    keyname: Optional[int] = None


@dataclass
class MappedNames:
    name: Optional[str] = None
    basename: Optional[str] = None
    keyname: Optional[str] = None
    visiblename: Optional[str] = None
    projectname_seed: Optional[str] = None


_MAPPINGS = [
    # Generic
    _NameMapping(
        name=NameType.GENERIC_PKGNAME,
        visiblename=NameType.GENERIC_PKGNAME,
        projectname_seed=NameType.GENERIC_PKGNAME,
    ),
    # Wikidata
    _NameMapping(
        keyname=NameType.WIKIDATA_ENTITY,
        visiblename=NameType.WIKIDATA_LABEL,
        projectname_seed=NameType.WIKIDATA_REPOLOGY_PROJECT_NAME,
    ),
    # *BSD
    _NameMapping(
        name=NameType.BSD_PKGNAME,
        keyname=NameType.BSD_ORIGIN,
        visiblename=NameType.BSD_ORIGIN,
        projectname_seed=NameType.BSD_PKGNAME,
    ),
    # Npackd
    _NameMapping(
        # XXX: add support for NPACKD_TITLE as visible name
        name=NameType.NPACKD_FULLNAME,
        basename=NameType.NPACKD_LASTNAME,
        visiblename=NameType.NPACKD_FULLNAME,
        projectname_seed=NameType.NPACKD_LASTNAME,
    ),
    # Debian
    _NameMapping(
        name=NameType.DEBIAN_PACKAGE,
        visiblename=NameType.DEBIAN_PACKAGE,
        projectname_seed=NameType.DEBIAN_PACKAGE,
    ),
    _NameMapping(
        name=NameType.DEBIAN_PACKAGE,
        basename=NameType.OPENWRT_SOURCEDIR,
        visiblename=NameType.DEBIAN_PACKAGE,
        projectname_seed=NameType.OPENWRT_SOURCEDIR,
    ),
    # Cygwin
    _NameMapping(
        name=NameType.CYGWIN_SUBPACKAGE_NAME,
        basename=NameType.CYGWIN_PACKAGE_NAME,
        visiblename=NameType.CYGWIN_SUBPACKAGE_NAME,
        projectname_seed=NameType.CYGWIN_PACKAGE_NAME,
    ),
    # Wiki
    _NameMapping(
        name=NameType.WIKI_TITLE,
        keyname=NameType.WIKI_PAGE,
        visiblename=NameType.WIKI_TITLE,
        projectname_seed=NameType.WIKI_TITLE,
    ),
    # Gentoo
    _NameMapping(
        name=NameType.GENTOO_NAME,
        keyname=NameType.GENTOO_FULL_NAME,
        visiblename=NameType.GENTOO_FULL_NAME,
        projectname_seed=NameType.GENTOO_NAME,
    ),
    # Pattern NOBN
    _NameMapping(
        name=NameType.PATTERN_NOBN_NAME,
        visiblename=NameType.PATTERN_NOBN_NAME,
        projectname_seed=NameType.PATTERN_NOBN_NAME,
    ),
    _NameMapping(
        name=NameType.PATTERN_NOBN_NAME,
        basename=NameType.PATTERN_NOBN_BASENAME,
        visiblename=NameType.PATTERN_NOBN_NAME,
        projectname_seed=NameType.PATTERN_NOBN_BASENAME,
    ),
]


class NameMapper:
    _names: Dict[int, str]
    _mappings: ClassVar[Dict[Tuple[int, ...], _NameMapping]] = {
        tuple(sorted(set(filter(None, mapping.__dict__.values())))): mapping
        for mapping in _MAPPINGS
    }

    def __init__(self) -> None:
        self._names = {}

    def add_name(self, name: str, name_type: int) -> None:
        if name_type != NameType.IGNORED:
            self._names[name_type] = name

    def get_mapped_names(self) -> MappedNames:
        keys = tuple(sorted(self._names.keys()))

        mapping = NameMapper._mappings.get(keys)

        if mapping is None:
            raise RuntimeError('no mapping for names combination {}'.format(keys))

        mapped = MappedNames()

        for out_name, in_name in mapping.__dict__.items():
            if in_name is not None:
                setattr(mapped, out_name, self._names[in_name])

        return mapped

    def describe(self) -> Optional[str]:
        if not self._names:
            return None
        return '|'.join(v for _, v in sorted(self._names.items()))
