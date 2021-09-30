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

import os
import re
import tarfile
from abc import abstractmethod
from io import StringIO
from typing import Any, IO, Iterable, Optional

from libversion import version_compare

from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.transformer import PackageTransformer


_WHITESPACE_PREFIX_RE = re.compile('([ ]*)[^ ]')
_KEYVAL_RE = re.compile('([a-zA-Z-]+)[ \t]*:[ \t]*(.*?)')


def _parse_cabal_file(cabalfile: IO[str]) -> dict[str, str]:
    cabaldata: dict[str, str] = {}
    offset: Optional[int] = None
    key: Optional[str] = None

    for line in cabalfile:
        line = line.rstrip()

        # offset is needed to be calculated first, from first non-whitespace line
        if offset is None:
            match = _WHITESPACE_PREFIX_RE.match(line)
            if match:
                offset = len(match.group(1))
            else:
                continue

        line = line[offset:]

        # ignore comments
        if line.startswith('--'):
            continue

        # process multiline keys
        if key:
            if line.startswith(' '):
                cabaldata[key] = cabaldata[key] + ' ' + line.strip() if key in cabaldata else line.strip()
                continue
            else:
                key = None

        # process singleline key or start of a multiline key
        match = _KEYVAL_RE.fullmatch(line)
        if not match:
            continue

        if match.group(2):
            cabaldata[match.group(1).lower()] = match.group(2)
        else:
            key = match.group(1).lower()

    return cabaldata


def _iter_cabal_hier(path: str) -> Iterable[dict[str, str]]:
    for moduledir in os.listdir(path):
        modulepath = os.path.join(path, moduledir)

        cabalpath: Optional[str] = None
        maxversion: Optional[str] = None

        for versiondir in os.listdir(modulepath):
            if versiondir == 'preferred-versions':
                continue

            if maxversion is None or version_compare(versiondir, maxversion) > 0:
                maxversion = versiondir
                cabalpath = os.path.join(path, moduledir, maxversion, moduledir + '.cabal')

        if cabalpath is not None:
            with open(cabalpath) as cabaldata:
                yield _parse_cabal_file(cabaldata)


def _extract_tarinfo(tar: tarfile.TarFile, tarinfo: tarfile.TarInfo) -> str:
    if (extracted := tar.extractfile(tarinfo)) is None:
        raise RuntimeError(f'cannot extract {tarinfo.name}')
    return extracted.read().decode('utf-8-sig')


def _iter_hackage_tarfile(path: str) -> Iterable[dict[str, str]]:
    preferred_versions: dict[str, str] = {}

    current_name: Optional[str] = None
    maxversion: Optional[str] = None
    maxversion_data: Optional[str] = None

    with tarfile.open(path, 'r|*') as tar:
        for tarinfo in tar:
            tarpath = tarinfo.name.split('/')

            if tarpath[-1] == 'preferred-versions':
                if current_name is not None:
                    raise RuntimeError('format assumption failed: preferred-versions go before all packages')

                preferred_versions[tarpath[0]] = _extract_tarinfo(tar, tarinfo)
            elif tarpath[-1].endswith('.cabal'):
                name, version = tarpath[0:2]

                if name != current_name:
                    if current_name is not None and name < current_name:
                        raise RuntimeError('format assumption failed: packages are alphabetically ordered')

                    if maxversion_data is not None:
                        yield _parse_cabal_file(StringIO(maxversion_data))

                    current_name = name
                    maxversion = version
                    maxversion_data = _extract_tarinfo(tar, tarinfo)
                else:
                    if maxversion is None or version_compare(version, maxversion) > 0:
                        maxversion = version
                        maxversion_data = _extract_tarinfo(tar, tarinfo)

        if maxversion_data is not None:
            yield _parse_cabal_file(StringIO(maxversion_data))


def _iter_hackage_tarfile_multipass(path: str) -> Iterable[dict[str, str]]:
    preferred_versions: dict[str, str] = {}
    latest_versions: dict[str, list[Any]] = {}  # name -> [version, count]

    # Pass 1: gather preferred versions
    with tarfile.open(path, 'r|*') as tar:
        for tarinfo in tar:
            tarpath = tarinfo.name.split('/')
            if tarpath[-1] == 'preferred-versions':
                preferred_versions[tarpath[0]] = _extract_tarinfo(tar, tarinfo)

    # Pass 2: gather latest versions
    with tarfile.open(path, 'r|*') as tar:
        for tarinfo in tar:
            tarpath = tarinfo.name.split('/')
            if tarpath[-1].endswith('.cabal'):
                name, version = tarpath[0:2]
                if name not in latest_versions or version_compare(version, latest_versions[name][0]) > 0:
                    latest_versions[name] = [version, 1]
                elif version == latest_versions[name][0]:
                    latest_versions[name][1] += 1

    # Pass 3: extract cabal files
    with tarfile.open(path, 'r|*') as tar:
        for tarinfo in tar:
            tarpath = tarinfo.name.split('/')
            if tarpath[-1].endswith('.cabal'):
                name, version = tarpath[0:2]

                if version == latest_versions[name][0]:
                    if latest_versions[name][1] > 1:
                        latest_versions[name][1] -= 1
                    else:
                        yield _parse_cabal_file(StringIO(_extract_tarinfo(tar, tarinfo)))


class HackageParserBase(Parser):
    @abstractmethod
    def _iterate(self, path: str) -> Iterable[dict[str, str]]:
        pass

    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for cabaldata in self._iterate(path):
            with factory.begin() as pkg:
                pkg.add_name(cabaldata['name'], NameType.HACKAGE_NAME)
                pkg.set_version(cabaldata['version'])

                pkg.set_summary(cabaldata.get('synopsis'))
                if 'maintainer' not in cabaldata:
                    pkg.add_maintainers('fallback-mnt-hackage@repology')
                else:
                    pkg.add_maintainers(extract_maintainers(cabaldata.get('maintainer')))
                pkg.add_licenses(cabaldata.get('license'))
                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, cabaldata.get('homepage'))
                pkg.add_categories(cabaldata.get('category'))

                if (bug_reports := cabaldata.get('bug-reports')) and bug_reports.startswith('http'):
                    pkg.add_links(LinkType.UPSTREAM_ISSUE_TRACKER, bug_reports)

                # XXX: may also parse repository url from source-repository section, but nested
                # parsing need to be implemented first

                yield pkg


class HackageParser(HackageParserBase):
    def _iterate(self, path: str) -> Iterable[dict[str, str]]:
        yield from _iter_cabal_hier(path)


class HackageTarParser(HackageParserBase):
    def _iterate(self, path: str) -> Iterable[dict[str, str]]:
        yield from _iter_hackage_tarfile(path)


class HackageTar01Parser(HackageParserBase):
    def _iterate(self, path: str) -> Iterable[dict[str, str]]:
        yield from _iter_hackage_tarfile_multipass(path)
