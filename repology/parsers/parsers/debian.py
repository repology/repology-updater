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

import re
from typing import Dict, Iterable

from repology.package import PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.transformer import PackageTransformer


_DEBIAN_VERSION_BAD_SUFFIX_RE = re.compile('[.~+-]?(dfsg|ubuntu|mx).*', re.IGNORECASE)
_DEBIAN_VERSION_GOOD_SUFFIX_RE = re.compile('((?:a|b|r|alpha|beta|rc|rcgit|pre|patch|git|svn|cvs|hg|bzr|darcs|dev)[.-]?[0-9]+(?:\\.[0-9]+)*|(?:alpha|beta|rc))', re.IGNORECASE)
_DEBIAN_VERSION_SUFFIX_SEP_RE = re.compile('[~+-]')
_DEBIAN_KEYVAL_RE = re.compile('([A-Za-z0-9_-]+):(.*?)')


def _normalize_version(version: str) -> str:
    # epoch
    pos = version.find(':')
    if pos != -1:
        version = version[pos + 1:]

    # revision
    pos = version.rfind('-')
    if pos != -1:
        version = version[0:pos]

    # garbage debian/ubuntu addendums
    version = _DEBIAN_VERSION_BAD_SUFFIX_RE.sub('', version)

    # remove suffixes
    version, *suffixes = _DEBIAN_VERSION_SUFFIX_SEP_RE.split(version)

    # append useful suffixes
    good_suffixes = []
    for suffix in suffixes:
        match = _DEBIAN_VERSION_GOOD_SUFFIX_RE.match(suffix)
        if match:
            good_suffixes.append(match.group(1))

    version += '.'.join(good_suffixes)

    return version


def _iter_packages(path: str) -> Iterable[Dict[str, str]]:
    with open(path, encoding='utf-8', errors='ignore') as f:
        current_data: Dict[str, str] = {}
        last_key = None

        for line in f:
            line = line.rstrip('\n')

            # empty line, yield ready package
            if line == '':
                if not current_data:
                    continue  # may happen on empty package list

                yield current_data

                current_data = {}
                last_key = None
                continue

            # key - value pair
            match = _DEBIAN_KEYVAL_RE.fullmatch(line)
            if match:
                key = match.group(1)
                value = match.group(2).strip()
                current_data[key] = value
                last_key = key
                continue

            # continuation of previous key
            if line.startswith(' '):
                if last_key is None:
                    raise RuntimeError('unable to parse line: {}'.format(line))

                current_data[last_key] += line.strip()
                continue

            raise RuntimeError('unable to parse line: {}'.format(line))


class DebianSourcesParser(Parser):
    def _extra_handling(self, pkg: PackageMaker, pkgdata: Dict[str, str]) -> None:
        if 'Binary' not in pkgdata or 'Source' in pkgdata:
            raise RuntimeError('Sanity check failed, expected Package descriptions with Binary, but without Source field')
        pkg.add_name(pkgdata['Package'], NameType.DEBIAN_SOURCE_PACKAGE)
        pkg.add_binnames(pkgdata['Binary'].split(', '))

    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for pkgdata in _iter_packages(path):
            with factory.begin(pkgdata['Package']) as pkg:
                pkg.set_version(pkgdata['Version'], _normalize_version)
                pkg.add_maintainers(extract_maintainers(pkgdata.get('Maintainer', '')))
                pkg.add_maintainers(extract_maintainers(pkgdata.get('Uploaders', '')))
                pkg.add_categories(pkgdata.get('Section'))
                pkg.add_homepages(pkgdata.get('Homepage'))

                self._extra_handling(pkg, pkgdata)

                yield pkg


class OpenWrtPackagesParser(DebianSourcesParser):
    def _extra_handling(self, pkg: PackageMaker, pkgdata: Dict[str, str]) -> None:
        pkgpath = pkgdata['Source'].split('/')
        pkg.add_name(pkgdata['Package'], NameType.OPENWRT_PACKAGE)
        pkg.add_name(pkgpath[-1], NameType.OPENWRT_SOURCEDIR)
        pkg.add_name(pkgdata['Source'], NameType.OPENWRT_SOURCE)
        if 'SourceName' in pkgdata:  # not present in openwrt < 19_07
            pkg.add_name(pkgdata['SourceName'], NameType.OPENWRT_SOURCENAME)
        pkg.set_arch(pkgdata['Architecture'])
        pkg.set_extra_field('path', '/'.join(pkgpath[2:]))

        if pkgpath[2:4] == ['lang', 'python']:
            # All python modules are in lang/python, but not all of lang/python are python modules
            # some are prefixed by python- or python3-, some are not
            # as a result, there's no reliable way to detect python modules and there may be
            # name clashes, (itsdangerous, xmltodict)
            # Prevent these by marking as untrusted
            pkg.set_flags(PackageFlags.UNTRUSTED)

        if pkgpath[2:4] == ['lang' 'erlang']:
            # modules with their own versions packages as a single entity
            pkg.set_flags(PackageFlags.UNTRUSTED)
