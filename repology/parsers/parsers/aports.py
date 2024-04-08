# Copyright (C) 2016-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Iterable, Iterator

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers


def _normalize_version(version: str) -> str:
    match = re.match('(.*)-r[0-9]+$', version)
    if match is not None:
        version = match.group(1)

    return version


def _iter_apkindex(path: str) -> Iterator[dict[str, str]]:
    with open(path, 'r', encoding='utf-8') as apkindex:
        state = {}
        for line in apkindex:
            line = line.strip()
            if line:
                state[line[0]] = line[2:].strip()
            elif state:
                yield state
                state = {}


class ApkIndexParser(Parser):
    _path_suffix: str | None = None

    def __init__(self, path_suffix: str | None = None) -> None:
        self._path_suffix = path_suffix

    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        index_path = os.path.join(path, self._path_suffix) if self._path_suffix else path

        for pkgdata in _iter_apkindex(index_path):
            with factory.begin(pkgdata['P']) as pkg:
                pkg.add_name(pkgdata['P'], NameType.APK_BIG_P)
                pkg.add_name(pkgdata['o'], NameType.APK_SMALL_O)
                pkg.set_version(pkgdata['V'], _normalize_version)

                pkg.set_summary(pkgdata['T'])
                pkg.add_homepages(pkgdata['U'])  # XXX: split?
                pkg.add_licenses(pkgdata['L'])
                pkg.set_arch(pkgdata['A'])

                pkg.add_maintainers(extract_maintainers(pkgdata.get('m')))

                yield pkg
