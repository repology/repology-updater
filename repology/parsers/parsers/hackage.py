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
from io import StringIO
from typing import Any, IO, Iterable

from libversion import version_compare

from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers


_WHITESPACE_PREFIX_RE = re.compile('([ ]*)[^ ]')
_KEYVAL_RE = re.compile('([a-zA-Z-]+)[ \t]*:[ \t]*(.*?)')


def _parse_cabal_file(cabalfile: IO[str]) -> dict[str, str]:
    cabaldata: dict[str, str] = {}
    offset: int | None = None
    key: str | None = None

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


def _extract_tarinfo(tar: tarfile.TarFile, tarinfo: tarfile.TarInfo) -> str:
    if (extracted := tar.extractfile(tarinfo)) is None:
        raise RuntimeError(f'cannot extract {tarinfo.name}')
    return extracted.read().decode('utf-8-sig')


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
                if 'hledger' in name and version == '1.24.99':
                    continue  # XXX: support preferred_versions properly
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


class HackageParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for cabaldata in _iter_hackage_tarfile_multipass(path):
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
