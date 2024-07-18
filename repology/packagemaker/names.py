# Copyright (C) 2019-2022 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import warnings
from dataclasses import dataclass
from typing import ClassVar


__all__ = ['NameType', 'NameMapper']


class NameType:
    IGNORED: ClassVar[int] = 0  # special type which is always ignored
    UNSUPPORTED: ClassVar[int] = 1  # special type which always fails

    # Common patterns: single name
    GENERIC_SRC_NAME: ClassVar[int] = 1001
    GENERIC_BIN_NAME: ClassVar[int] = 1002
    GENERIC_SRCBIN_NAME: ClassVar[int] = 1003

    # Common patterns: name + optional basename
    GENERIC_NOBN_NAME: ClassVar[int] = 1010
    GENERIC_NOBN_BASENAME: ClassVar[int] = 1011

    # Common patterns: category/name hierarchy
    GENERIC_CATNAME_NAME: ClassVar[int] = 1020
    GENERIC_CATNAME_FULL_NAME: ClassVar[int] = 1021

    # Individual repos
    WIKIDATA_ENTITY: ClassVar[int] = 20
    WIKIDATA_LABEL: ClassVar[int] = 21
    WIKIDATA_REPOLOGY_PROJECT_NAME: ClassVar[int] = 22

    BSD_PKGNAME: ClassVar[int] = 30
    BSD_ORIGIN: ClassVar[int] = 31

    NPACKD_TITLE: ClassVar[int] = 40
    NPACKD_FULLNAME: ClassVar[int] = 41
    NPACKD_LASTNAME: ClassVar[int] = 42

    DEBIAN_SOURCE_PACKAGE: ClassVar[int] = 50
    DEBIAN_BINARY_PACKAGE: ClassVar[int] = 51

    OPENWRT_PACKAGE: ClassVar[int] = 60
    OPENWRT_SOURCE: ClassVar[int] = 61
    OPENWRT_SOURCENAME: ClassVar[int] = IGNORED
    OPENWRT_SOURCEDIR: ClassVar[int] = 63

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

    OPENBSD_PKGPATH: ClassVar[int] = 140
    OPENBSD_STEM: ClassVar[int] = 141
    OPENBSD_STRIPPED_STEM: ClassVar[int] = 142

    HOMEBREW_NAME: ClassVar[int] = 150
    HOMEBREW_NAME_PRE_AT: ClassVar[int] = 151
    HOMEBREW_FULL_NAME: ClassVar[int] = IGNORED

    HOMEBREW_CASK_TOKEN: ClassVar[int] = 160
    HOMEBREW_CASK_FIRST_NAME: ClassVar[int] = 161

    SLACKWARE_NAME: ClassVar[int] = 170
    SLACKWARE_FULL_NAME: ClassVar[int] = IGNORED
    SLACKWARE_PSEUDO_FULL_NAME: ClassVar[int] = 172

    SRCRPM_NAME: ClassVar[int] = 190

    BINRPM_NAME: ClassVar[int] = 200
    BINRPM_SRCNAME: ClassVar[int] = 201

    AOSC_NAME: ClassVar[int] = 210
    AOSC_DIRECTORY: ClassVar[int] = IGNORED
    AOSC_FULLPATH: ClassVar[int] = 212

    MACPORTS_NAME: ClassVar[int] = 220
    MACPORTS_PORTDIR: ClassVar[int] = 221
    MACPORTS_PORTNAME: ClassVar[int] = IGNORED

    PISI_NAME: ClassVar[int] = 230
    PISI_PKGDIR: ClassVar[int] = 231

    OPENINDIANA_FMRI: ClassVar[int] = 240
    OPENINDIANA_NAME: ClassVar[int] = 241

    NIX_PNAME: ClassVar[int] = 250
    NIX_ATTRIBUTE_PATH: ClassVar[int] = 251

    CONAN_RECIPE_NAME: ClassVar[int] = 260

    WINGET_ID: ClassVar[int] = IGNORED
    WINGET_ID_NAME: ClassVar[int] = 271
    WINGET_NAME: ClassVar[int] = 272
    WINGET_PATH: ClassVar[int] = 273

    APPGET_ID: ClassVar[int] = 280
    APPGET_NAME: ClassVar[int] = 281

    GUIX_NAME: ClassVar[int] = 290

    SAGEMATH_NAME: ClassVar[int] = 300
    SAGEMATH_PROJECT_NAME: ClassVar[int] = 301

    PACSTALL_NAME: ClassVar[int] = 310
    PACSTALL_VISIBLENAME: ClassVar[int] = IGNORED

    OS4DEPOT_PATH: ClassVar[int] = 320  # foo/bar/baz.lha
    OS4DEPOT_FILENAME_EXT: ClassVar[int] = 321  # baz.lha
    OS4DEPOT_FILENAME_NO_EXT: ClassVar[int] = 322  # baz

    CHROMEBREW_NAME: ClassVar[int] = 330

    # Note that packages reside in subdirs such as packages/,
    # root-packages/, x11-packages/ and it may be that srcname
    # should include directory as well. However these are names
    # reported by upstream and these seem to be unique ATOW
    TERMUX_NAME: ClassVar[int] = GENERIC_SRCBIN_NAME

    VCPKG_SOURCE: ClassVar[int] = GENERIC_SRC_NAME

    GOBOLINUX_RECIPE: ClassVar[int] = GENERIC_SRC_NAME

    RUBYGEMS_NAME: ClassVar[int] = GENERIC_SRC_NAME

    # since binary artifacts (e.g. wheels) are distributed, we also
    # set biname
    PYPI_NAME: ClassVar[int] = GENERIC_SRCBIN_NAME

    CPAN_NAME: ClassVar[int] = GENERIC_SRC_NAME

    LUAROCKS_NAME: ClassVar[int] = GENERIC_SRC_NAME

    CRATESIO_ID: ClassVar[int] = GENERIC_SRC_NAME

    ELPA_NAME: ClassVar[int] = GENERIC_SRC_NAME

    # see package pages, binaries are published as well
    CRAN_NAME: ClassVar[int] = GENERIC_SRCBIN_NAME

    HACKAGE_NAME: ClassVar[int] = GENERIC_SRC_NAME

    STACKAGE_NAME: ClassVar[int] = GENERIC_SRC_NAME

    SPACK_NAME: ClassVar[int] = GENERIC_SRC_NAME

    DISTROWATCH_NAME: ClassVar[int] = GENERIC_SRC_NAME

    FRESHCODE_NAME: ClassVar[int] = GENERIC_SRC_NAME

    RAVENPORTS_NAMEBASE: ClassVar[int] = GENERIC_SRCBIN_NAME

    SCOOP_NAME: ClassVar[int] = GENERIC_BIN_NAME

    CRUX_NAME: ClassVar[int] = GENERIC_SRC_NAME

    # though in fact packages reside in subdirectories such as
    # core/ and extras/, only package name is used to reference
    # the package, e.g. in depends
    KISS_NAME: ClassVar[int] = GENERIC_SRC_NAME

    HPUX_NAME: ClassVar[int] = GENERIC_SRCBIN_NAME

    JUSTINSTALL_NAME: ClassVar[int] = GENERIC_SRCBIN_NAME

    # judging by https://distr1.org/things-to-try/ binary packages
    # are available
    DISTRI_NAME: ClassVar[int] = GENERIC_SRCBIN_NAME

    SALIX_NAME: ClassVar[int] = GENERIC_SRC_NAME

    ATARAXIA_NAME: ClassVar[int] = GENERIC_SRC_NAME

    BAULK_NAME: ClassVar[int] = GENERIC_SRCBIN_NAME

    YIFFOS_NAME: ClassVar[int] = GENERIC_SRC_NAME

    BUILDROOT_NAME: ClassVar[int] = GENERIC_SRC_NAME

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

    APK_BIG_P: ClassVar[int] = GENERIC_NOBN_NAME
    APK_SMALL_O: ClassVar[int] = GENERIC_NOBN_BASENAME

    GENTOO_NAME: ClassVar[int] = GENERIC_CATNAME_NAME
    GENTOO_FULL_NAME: ClassVar[int] = GENERIC_CATNAME_FULL_NAME

    EXHERBO_NAME: ClassVar[int] = GENERIC_CATNAME_NAME
    EXHERBO_FULL_NAME: ClassVar[int] = GENERIC_CATNAME_FULL_NAME

    HAIKUPORTS_NAME: ClassVar[int] = GENERIC_CATNAME_NAME
    HAIKUPORTS_FULL_NAME: ClassVar[int] = GENERIC_CATNAME_FULL_NAME

    SLACKBUILDS_NAME: ClassVar[int] = GENERIC_CATNAME_NAME
    SLACKBUILDS_FULL_NAME: ClassVar[int] = GENERIC_CATNAME_FULL_NAME

    T2_NAME: ClassVar[int] = GENERIC_SRC_NAME

    SERPENTOS_NAME: ClassVar[int] = GENERIC_SRC_NAME


@dataclass
class _NameMapping:
    visiblename: int
    projectname_seed: int

    srcname: int | None = None
    binname: int | None = None
    trackname: int | None = None


@dataclass
class MappedNames:
    srcname: str | None = None
    binname: str | None = None
    visiblename: str | None = None
    projectname_seed: str | None = None
    trackname: str | None = None


_MAPPINGS = [
    # Generic
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
        srcname=NameType.GENERIC_SRC_NAME,
        trackname=NameType.GENERIC_SRC_NAME,
        visiblename=NameType.GENERIC_SRC_NAME,
        projectname_seed=NameType.GENERIC_SRC_NAME,
    ),
    _NameMapping(
        binname=NameType.GENERIC_BIN_NAME,
        trackname=NameType.GENERIC_BIN_NAME,
        visiblename=NameType.GENERIC_BIN_NAME,
        projectname_seed=NameType.GENERIC_BIN_NAME,
    ),
    _NameMapping(
        srcname=NameType.GENERIC_SRCBIN_NAME,
        binname=NameType.GENERIC_SRCBIN_NAME,
        trackname=NameType.GENERIC_SRCBIN_NAME,
        visiblename=NameType.GENERIC_SRCBIN_NAME,
        projectname_seed=NameType.GENERIC_SRCBIN_NAME,
    ),
    _NameMapping(
        srcname=NameType.GENERIC_CATNAME_FULL_NAME,
        visiblename=NameType.GENERIC_CATNAME_FULL_NAME,
        projectname_seed=NameType.GENERIC_CATNAME_NAME,
        trackname=NameType.GENERIC_CATNAME_FULL_NAME,
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
        srcname=NameType.WIKIDATA_ENTITY,
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
    _NameMapping(
        srcname=NameType.OPENBSD_PKGPATH,
        binname=NameType.OPENBSD_STEM,
        visiblename=NameType.OPENBSD_PKGPATH,
        projectname_seed=NameType.OPENBSD_STRIPPED_STEM,
        trackname=NameType.OPENBSD_PKGPATH,
    ),
    # Npackd
    _NameMapping(
        # XXX: note that despite that npackd manages binary software,
        # this is srcname as it refers to how the recipe is called
        # See https://github.com/repology/repology-updater/issues/944#issuecomment-1251327958
        srcname=NameType.NPACKD_FULLNAME,
        binname=NameType.NPACKD_FULLNAME,
        visiblename=NameType.NPACKD_TITLE,
        projectname_seed=NameType.NPACKD_LASTNAME,
        trackname=NameType.NPACKD_FULLNAME,
    ),
    # ReactOS
    _NameMapping(
        srcname=NameType.REACTOS_FILENAME,
        # according to https://reactos.org/wiki/RAPPS#Command_Line_Support
        binname=NameType.REACTOS_FILENAME,
        trackname=NameType.REACTOS_FILENAME,
        visiblename=NameType.REACTOS_NAME,
        projectname_seed=NameType.REACTOS_FILENAME,
    ),
    # Chocolatey
    _NameMapping(
        binname=NameType.CHOCOLATEY_TITLE,
        trackname=NameType.CHOCOLATEY_TITLE,
        visiblename=NameType.CHOCOLATEY_METADATA_TITLE,  # may be empty
        projectname_seed=NameType.CHOCOLATEY_TITLE,
    ),
    _NameMapping(
        binname=NameType.CHOCOLATEY_TITLE,
        trackname=NameType.CHOCOLATEY_TITLE,
        visiblename=NameType.CHOCOLATEY_TITLE,
        projectname_seed=NameType.CHOCOLATEY_TITLE,
    ),
    # Debian
    _NameMapping(
        srcname=NameType.DEBIAN_SOURCE_PACKAGE,
        trackname=NameType.DEBIAN_SOURCE_PACKAGE,
        visiblename=NameType.DEBIAN_SOURCE_PACKAGE,
        projectname_seed=NameType.DEBIAN_SOURCE_PACKAGE,
    ),
    _NameMapping(
        # XXX the only consumer for these ATOW is WakeMeOps repo
        # which is not genuine Debian, so if we want to support
        # binary deb distros at some point, WakeMeOps may need
        # to be switched to dedicated NameType
        binname=NameType.DEBIAN_BINARY_PACKAGE,
        trackname=NameType.DEBIAN_BINARY_PACKAGE,
        visiblename=NameType.DEBIAN_BINARY_PACKAGE,
        projectname_seed=NameType.DEBIAN_BINARY_PACKAGE,
    ),
    _NameMapping(
        binname=NameType.OPENWRT_PACKAGE,
        srcname=NameType.OPENWRT_SOURCE,
        trackname=NameType.OPENWRT_SOURCE,
        visiblename=NameType.OPENWRT_PACKAGE,
        projectname_seed=NameType.OPENWRT_SOURCEDIR,
    ),
    # Wiki
    _NameMapping(
        srcname=NameType.WIKI_PAGE,
        visiblename=NameType.WIKI_TITLE,
        projectname_seed=NameType.WIKI_TITLE,
        trackname=NameType.WIKI_PAGE,
    ),
    # F-Droid
    _NameMapping(
        srcname=NameType.FDROID_ID,
        binname=NameType.FDROID_ID,
        trackname=NameType.FDROID_ID,
        visiblename=NameType.FDROID_NAME,
        projectname_seed=NameType.FDROID_NAME,
    ),
    # Homebrew
    _NameMapping(
        srcname=NameType.HOMEBREW_NAME,
        trackname=NameType.HOMEBREW_NAME,
        visiblename=NameType.HOMEBREW_NAME,
        projectname_seed=NameType.HOMEBREW_NAME_PRE_AT,
    ),
    _NameMapping(
        srcname=NameType.HOMEBREW_CASK_TOKEN,
        trackname=NameType.HOMEBREW_CASK_TOKEN,
        visiblename=NameType.HOMEBREW_CASK_FIRST_NAME,
        projectname_seed=NameType.HOMEBREW_CASK_TOKEN,
    ),
    # Slackware
    _NameMapping(
        binname=NameType.SLACKWARE_NAME,
        visiblename=NameType.SLACKWARE_NAME,
        projectname_seed=NameType.SLACKWARE_NAME,
        trackname=NameType.SLACKWARE_PSEUDO_FULL_NAME,
    ),
    # RPM
    _NameMapping(
        srcname=NameType.SRCRPM_NAME,
        trackname=NameType.SRCRPM_NAME,
        visiblename=NameType.SRCRPM_NAME,
        projectname_seed=NameType.SRCRPM_NAME,
    ),
    _NameMapping(
        srcname=NameType.BINRPM_SRCNAME,
        binname=NameType.BINRPM_NAME,
        trackname=NameType.BINRPM_SRCNAME,
        visiblename=NameType.BINRPM_NAME,
        projectname_seed=NameType.BINRPM_SRCNAME,
    ),
    # AOSC
    _NameMapping(
        srcname=NameType.AOSC_FULLPATH,
        binname=NameType.AOSC_NAME,
        trackname=NameType.AOSC_FULLPATH,
        visiblename=NameType.AOSC_NAME,
        # XXX: we could use AOSC_DIRECTORY here, as in fact it's closer to basename,
        # however, the difference is very minor and there are some pessimizations
        projectname_seed=NameType.AOSC_NAME,
    ),
    # MacPorts
    _NameMapping(
        srcname=NameType.MACPORTS_PORTDIR,
        binname=NameType.MACPORTS_NAME,
        # Note: generally that'd be PORTDIR, but a port may contain packages of different versions
        # (example is haskell-platform), and there are no NAME conflict
        trackname=NameType.MACPORTS_NAME,
        visiblename=NameType.MACPORTS_NAME,
        # XXX: may use PORTNAME as well, but this leads to some pessimizations
        projectname_seed=NameType.MACPORTS_NAME,
    ),
    # Pisi
    _NameMapping(
        srcname=NameType.PISI_PKGDIR,
        trackname=NameType.PISI_PKGDIR,
        visiblename=NameType.PISI_NAME,  # PKGDIR is too long and NAMES are unique
        projectname_seed=NameType.PISI_NAME,
    ),
    # OpenIndiana
    _NameMapping(
        srcname=NameType.OPENINDIANA_NAME,
        binname=NameType.OPENINDIANA_FMRI,
        trackname=NameType.OPENINDIANA_NAME,
        visiblename=NameType.OPENINDIANA_NAME,  # FRMI is too long
        projectname_seed=NameType.OPENINDIANA_NAME,
    ),
    # Nix
    _NameMapping(
        srcname=NameType.NIX_ATTRIBUTE_PATH,
        trackname=NameType.NIX_ATTRIBUTE_PATH,
        visiblename=NameType.NIX_PNAME,
        projectname_seed=NameType.NIX_PNAME,
    ),
    # Conan
    _NameMapping(
        srcname=NameType.CONAN_RECIPE_NAME,
        trackname=NameType.CONAN_RECIPE_NAME,
        visiblename=NameType.CONAN_RECIPE_NAME,
        projectname_seed=NameType.CONAN_RECIPE_NAME,
    ),
    # Winget
    _NameMapping(
        srcname=NameType.WINGET_PATH,
        trackname=NameType.WINGET_PATH,
        visiblename=NameType.WINGET_NAME,
        projectname_seed=NameType.WINGET_ID_NAME,
    ),
    # Appget
    _NameMapping(
        srcname=NameType.APPGET_ID,
        trackname=NameType.APPGET_ID,
        visiblename=NameType.APPGET_NAME,
        projectname_seed=NameType.APPGET_ID,
    ),
    # Guix
    _NameMapping(
        srcname=NameType.GUIX_NAME,
        binname=NameType.GUIX_NAME,
        trackname=NameType.GUIX_NAME,
        visiblename=NameType.GUIX_NAME,
        projectname_seed=NameType.GUIX_NAME,
    ),
    # Sagemath
    _NameMapping(
        srcname=NameType.SAGEMATH_NAME,
        binname=NameType.SAGEMATH_NAME,
        trackname=NameType.SAGEMATH_NAME,
        visiblename=NameType.SAGEMATH_NAME,
        projectname_seed=NameType.SAGEMATH_PROJECT_NAME,
    ),
    # Pacstall
    _NameMapping(
        srcname=NameType.PACSTALL_NAME,
        binname=NameType.PACSTALL_NAME,
        trackname=NameType.PACSTALL_NAME,
        visiblename=NameType.PACSTALL_NAME,
        projectname_seed=NameType.PACSTALL_NAME,
    ),
    # OS4Depot
    _NameMapping(
        binname=NameType.OS4DEPOT_PATH,
        trackname=NameType.OS4DEPOT_PATH,
        visiblename=NameType.OS4DEPOT_FILENAME_EXT,
        projectname_seed=NameType.OS4DEPOT_FILENAME_NO_EXT,
    ),
    # Chromebrew
    _NameMapping(
        srcname=NameType.CHROMEBREW_NAME,
        trackname=NameType.CHROMEBREW_NAME,
        visiblename=NameType.CHROMEBREW_NAME,
        projectname_seed=NameType.CHROMEBREW_NAME,
    ),
]


class NameMapper:
    _names: dict[int, str]
    _mappings: ClassVar[dict[tuple[int, ...], _NameMapping]] = {
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
                if out_name == 'name':
                    warnings.warn('using generic name in name mappings is deprecated', DeprecationWarning)
                setattr(mapped, out_name, self._names[in_name])

        return mapped

    def describe(self) -> str | None:
        if not self._names:
            return None
        names = sorted(set(self._names.values()))
        if len(names) == 1:
            return names[0]
        else:
            return names[0] + ' (' + ', '.join(names[1:]) + ')'
