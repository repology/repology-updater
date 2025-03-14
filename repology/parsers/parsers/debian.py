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

import re
from typing import Iterable

from repology.package import LinkType, PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.versions import DebianVersionParser


_DEBIAN_KEYVAL_RE = re.compile('([A-Za-z0-9_-]+):(.*?)')


def _iter_packages(path: str) -> Iterable[dict[str, str]]:
    with open(path, encoding='utf-8', errors='ignore') as f:
        current_data: dict[str, str] = {}
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


def _extract_vcs_link(pkgdata: dict[str, str]) -> str | None:
    if 'Vcs-Browser' in pkgdata:
        return pkgdata['Vcs-Browser']

    for key, value in pkgdata.items():
        if key.startswith('Vcs-'):
            return value

    return None


class DebianSourcesParser(Parser):
    _allowed_vcs_urls_re: re.Pattern[str] | None
    _version_parser: DebianVersionParser

    def __init__(self, allowed_vcs_urls: str | None = None, extra_garbage_words: list[str] | str | None = None) -> None:
        self._allowed_vcs_urls_re = None if allowed_vcs_urls is None else re.compile(allowed_vcs_urls, re.IGNORECASE)
        match extra_garbage_words:
            case str():
                self._version_parser = DebianVersionParser([extra_garbage_words])
            case list():
                self._version_parser = DebianVersionParser(extra_garbage_words)
            case _:
                self._version_parser = DebianVersionParser()

    def _extra_handling(self, pkg: PackageMaker, pkgdata: dict[str, str]) -> None:
        if 'Binary' not in pkgdata or 'Source' in pkgdata:
            raise RuntimeError('Sanity check failed, expected Package descriptions with Binary, but without Source field')
        pkg.add_name(pkgdata['Package'], NameType.DEBIAN_SOURCE_PACKAGE)
        pkg.add_binnames(pkgdata['Binary'].split(', '))

    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for pkgdata in _iter_packages(path):
            with factory.begin(pkgdata['Package']) as pkg:
                fixed_version, flags = self._version_parser.parse(pkgdata['Version'])

                pkg.set_version(fixed_version)
                pkg.set_rawversion(pkgdata['Version'])
                pkg.set_flags(flags)

                pkg.add_maintainers(extract_maintainers(pkgdata.get('Maintainer', '')))
                pkg.add_maintainers(extract_maintainers(pkgdata.get('Uploaders', '')))
                pkg.add_categories(pkgdata.get('Section'))
                pkg.add_homepages(pkgdata.get('Homepage'))

                self._extra_handling(pkg, pkgdata)

                if (url := _extract_vcs_link(pkgdata)) is not None:
                    if self._allowed_vcs_urls_re is not None and self._allowed_vcs_urls_re.match(url):
                        pkg.add_links(LinkType.PACKAGE_SOURCES, url)

                yield pkg


class OpenWrtPackagesParser(DebianSourcesParser):
    def _extra_handling(self, pkg: PackageMaker, pkgdata: dict[str, str]) -> None:
        pkgpath = pkgdata['Source'].split('/')
        pkg.add_name(pkgdata['Package'], NameType.OPENWRT_PACKAGE)
        pkg.add_name(pkgpath[-1], NameType.OPENWRT_SOURCEDIR)
        pkg.add_name(pkgdata['Source'], NameType.OPENWRT_SOURCE)
        if 'SourceName' in pkgdata:  # not present in openwrt < 19_07
            pkg.add_name(pkgdata['SourceName'], NameType.OPENWRT_SOURCENAME)
        pkg.set_arch(pkgdata['Architecture'])
        pkg.set_extra_field('path', '/'.join(pkgpath[2:]))
        pkg.add_homepages(pkgdata.get('URL'))
        if cpeid := pkgdata.get('CPE-ID'):
            cpe_components = cpeid.split(':')
            if len(cpe_components) < 4:
                raise RuntimeError(f'unable to parse cpe-id (not enough components): {cpeid}')
            pkg.add_cpe(cpe_components[2], cpe_components[3])

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


class DebianPackagesParser(DebianSourcesParser):
    def _extra_handling(self, pkg: PackageMaker, pkgdata: dict[str, str]) -> None:
        if 'Binary' in pkgdata or 'Source' in pkgdata:
            raise RuntimeError('Sanity check failed, expected Package descriptions without Binary or Source fields')
        pkg.add_name(pkgdata['Package'], NameType.DEBIAN_BINARY_PACKAGE)
