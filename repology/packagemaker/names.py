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
    UNSUPPORTED: ClassVar[int] = 1  # special type which always fails

    # Unclassified, process all cases and remove
    GENERIC_PKGNAME: ClassVar[int] = 10

    # Common patterns: single name
    GENERIC_SN_NAME: ClassVar[int] = 1000

    # Common patterns: name + optional basename
    GENERIC_NOBN_NAME: ClassVar[int] = 1010
    GENERIC_NOBN_BASENAME: ClassVar[int] = 1011

    # Common patterns: gentoolike (category/name)
    GENERIC_GENTOOLIKE_NAME: ClassVar[int] = 1020
    GENERIC_GENTOOLIKE_FULL_NAME: ClassVar[int] = 1021

    # Individual repos
    WIKIDATA_ENTITY: ClassVar[int] = 20
    WIKIDATA_LABEL: ClassVar[int] = 21
    WIKIDATA_REPOLOGY_PROJECT_NAME: ClassVar[int] = 22

    BSD_PKGNAME: ClassVar[int] = 30
    BSD_ORIGIN: ClassVar[int] = 31

    NPACKD_TITLE: ClassVar[int] = 40
    NPACKD_FULLNAME: ClassVar[int] = 41
    NPACKD_LASTNAME: ClassVar[int] = 42

    DEBIAN_PACKAGE: ClassVar[int] = 50
    OPENWRT_SOURCEDIR: ClassVar[int] = 51

    WIKI_TITLE: ClassVar[int] = 70
    WIKI_PAGE: ClassVar[int] = 71

    REACTOS_FILENAME: ClassVar[int] = 90
    REACTOS_NAME: ClassVar[int] = 91

    FDROID_NAME: ClassVar[int] = 100
    FDROID_ID: ClassVar[int] = 101

    CHOCOLATEY_TITLE: ClassVar[int] = 110
    CHOCOLATEY_METADATA_TITLE: ClassVar[int] = 111

    YACP_NAME: ClassVar[int] = 120  # also has binary packages as PKG_NAMES, but we don't support these

    KAOS_NAME: ClassVar[int] = 130  # arch-like, but no source/basename info available

    BUCKAROO_NAME: ClassVar[int] = GENERIC_SN_NAME
    BUCKAROO_FILENAME: ClassVar[int] = IGNORED

    TERMUX_NAME: ClassVar[int] = GENERIC_SN_NAME

    VCPKG_SOURCE: ClassVar[int] = GENERIC_SN_NAME

    GOBOLINUX_RECIPE: ClassVar[int] = GENERIC_SN_NAME

    GUIX_NAME: ClassVar[int] = GENERIC_SN_NAME

    RUBYGEMS_NAME: ClassVar[int] = GENERIC_SN_NAME

    CPAN_NAME: ClassVar[int] = GENERIC_SN_NAME

    LUAROCKS_NAME: ClassVar[int] = GENERIC_SN_NAME

    CRATESIO_ID: ClassVar[int] = GENERIC_SN_NAME

    ELPA_NAME: ClassVar[int] = GENERIC_SN_NAME

    CRAN_NAME: ClassVar[int] = GENERIC_SN_NAME

    HACKAGE_NAME: ClassVar[int] = GENERIC_SN_NAME

    STACKAGE_NAME: ClassVar[int] = GENERIC_SN_NAME

    DISTROWATCH_NAME: ClassVar[int] = GENERIC_SN_NAME

    FRESHCODE_NAME: ClassVar[int] = GENERIC_SN_NAME

    RAVENPORTS_NAMEBASE: ClassVar[int] = GENERIC_SN_NAME

    SCOOP_NAME: ClassVar[int] = GENERIC_SN_NAME

    CRUX_NAME: ClassVar[int] = GENERIC_SN_NAME

    KISS_NAME: ClassVar[int] = GENERIC_SN_NAME

    HPUX_NAME: ClassVar[int] = GENERIC_SN_NAME

    OS4DEPOT_NAME: ClassVar[int] = GENERIC_SN_NAME

    KWORT_NAME: ClassVar[int] = GENERIC_SN_NAME

    JUSTINSTALL_NAME: ClassVar[int] = GENERIC_SN_NAME

    DISTRI_NAME: ClassVar[int] = GENERIC_SN_NAME

    MSYS2_NAME: ClassVar[int] = GENERIC_NOBN_NAME
    MSYS2_BASENAME: ClassVar[int] = GENERIC_NOBN_BASENAME

    SOLUS_NAME: ClassVar[int] = GENERIC_NOBN_NAME
    SOLUS_SOURCE_NAME: ClassVar[int] = GENERIC_NOBN_BASENAME

    SLITAZ_NAME: ClassVar[int] = GENERIC_NOBN_NAME
    SLITAZ_META: ClassVar[int] = GENERIC_NOBN_BASENAME

    VOID_NAME: ClassVar[int] = GENERIC_NOBN_NAME
    VOID_SOURCE: ClassVar[int] = GENERIC_NOBN_BASENAME

    ARCH_NAME: ClassVar[int] = GENERIC_NOBN_NAME
    ARCH_BASENAME: ClassVar[int] = GENERIC_NOBN_BASENAME

    CYGWIN_PACKAGE_NAME: ClassVar[int] = GENERIC_NOBN_BASENAME
    CYGWIN_SUBPACKAGE_NAME: ClassVar[int] = GENERIC_NOBN_NAME

    GENTOO_NAME: ClassVar[int] = GENERIC_GENTOOLIKE_NAME
    GENTOO_FULL_NAME: ClassVar[int] = GENERIC_GENTOOLIKE_FULL_NAME

    EXHERBO_NAME: ClassVar[int] = GENERIC_GENTOOLIKE_NAME
    EXHERBO_FULL_NAME: ClassVar[int] = GENERIC_GENTOOLIKE_FULL_NAME

    HAIKUPORTS_NAME: ClassVar[int] = GENERIC_GENTOOLIKE_NAME
    HAIKUPORTS_FULL_NAME: ClassVar[int] = GENERIC_GENTOOLIKE_FULL_NAME


@dataclass
class _NameMapping:
    visiblename: int
    projectname_seed: int

    name: Optional[int] = None
    srcname: Optional[int] = None
    binname: Optional[int] = None
    basename: Optional[int] = None
    keyname: Optional[int] = None
    trackname: Optional[int] = None


@dataclass
class MappedNames:
    name: Optional[str] = None
    srcname: Optional[str] = None
    binname: Optional[str] = None
    basename: Optional[str] = None
    keyname: Optional[str] = None
    visiblename: Optional[str] = None
    projectname_seed: Optional[str] = None
    trackname: Optional[str] = None


_MAPPINGS = [
    # Generic
    _NameMapping(
        name=NameType.GENERIC_PKGNAME,
        visiblename=NameType.GENERIC_PKGNAME,
        projectname_seed=NameType.GENERIC_PKGNAME,
    ),
    _NameMapping(
        srcname=NameType.GENERIC_NOBN_NAME,
        binname=NameType.GENERIC_NOBN_NAME,
        trackname=NameType.GENERIC_NOBN_NAME,
        visiblename=NameType.GENERIC_NOBN_NAME,
        projectname_seed=NameType.GENERIC_NOBN_NAME,
    ),
    _NameMapping(
        srcname=NameType.GENERIC_NOBN_BASENAME,
        binname=NameType.GENERIC_NOBN_NAME,
        trackname=NameType.GENERIC_NOBN_BASENAME,
        visiblename=NameType.GENERIC_NOBN_NAME,
        projectname_seed=NameType.GENERIC_NOBN_BASENAME,
    ),
    _NameMapping(
        name=NameType.GENERIC_SN_NAME,
        trackname=NameType.GENERIC_SN_NAME,
        visiblename=NameType.GENERIC_SN_NAME,
        projectname_seed=NameType.GENERIC_SN_NAME,
    ),
    _NameMapping(
        srcname=NameType.GENERIC_GENTOOLIKE_FULL_NAME,
        visiblename=NameType.GENERIC_GENTOOLIKE_FULL_NAME,
        projectname_seed=NameType.GENERIC_GENTOOLIKE_NAME,
        trackname=NameType.GENERIC_GENTOOLIKE_FULL_NAME,
    ),
    # KaOS
    _NameMapping(
        binname=NameType.KAOS_NAME,
        trackname=NameType.KAOS_NAME,
        visiblename=NameType.KAOS_NAME,
        projectname_seed=NameType.KAOS_NAME,
    ),
    # YACP
    _NameMapping(
        srcname=NameType.YACP_NAME,
        trackname=NameType.YACP_NAME,
        visiblename=NameType.YACP_NAME,
        projectname_seed=NameType.YACP_NAME,
    ),
    # Wikidata
    _NameMapping(
        name=NameType.WIKIDATA_ENTITY,
        visiblename=NameType.WIKIDATA_LABEL,
        projectname_seed=NameType.WIKIDATA_REPOLOGY_PROJECT_NAME,
        trackname=NameType.WIKIDATA_ENTITY,
    ),
    # *BSD
    _NameMapping(
        srcname=NameType.BSD_ORIGIN,
        binname=NameType.BSD_PKGNAME,
        visiblename=NameType.BSD_ORIGIN,
        projectname_seed=NameType.BSD_PKGNAME,
        trackname=NameType.BSD_ORIGIN,
    ),
    # Npackd
    _NameMapping(
        name=NameType.NPACKD_FULLNAME,
        visiblename=NameType.NPACKD_TITLE,
        projectname_seed=NameType.NPACKD_LASTNAME,
        trackname=NameType.NPACKD_FULLNAME,
    ),
    # ReactOS
    _NameMapping(
        name=NameType.REACTOS_FILENAME,
        trackname=NameType.REACTOS_FILENAME,
        visiblename=NameType.REACTOS_NAME,
        projectname_seed=NameType.REACTOS_FILENAME,
    ),
    # Chocolatey
    _NameMapping(
        name=NameType.CHOCOLATEY_TITLE,
        trackname=NameType.CHOCOLATEY_TITLE,
        visiblename=NameType.CHOCOLATEY_METADATA_TITLE,  # may be empty
        projectname_seed=NameType.CHOCOLATEY_TITLE,
    ),
    _NameMapping(
        name=NameType.CHOCOLATEY_TITLE,
        trackname=NameType.CHOCOLATEY_TITLE,
        visiblename=NameType.CHOCOLATEY_TITLE,
        projectname_seed=NameType.CHOCOLATEY_TITLE,
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
    # Wiki
    _NameMapping(
        name=NameType.WIKI_PAGE,
        visiblename=NameType.WIKI_TITLE,
        projectname_seed=NameType.WIKI_TITLE,
        trackname=NameType.WIKI_PAGE,
    ),
    # F-Droid
    _NameMapping(
        name=NameType.FDROID_ID,
        trackname=NameType.FDROID_ID,
        visiblename=NameType.FDROID_NAME,
        projectname_seed=NameType.FDROID_NAME,
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
