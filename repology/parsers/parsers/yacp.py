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
from typing import Iterable, Tuple

from repology.logger import Logger
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.versions import VersionStripper
from repology.transformer import PackageTransformer


def _iter_cygports(path: str) -> Iterable[Tuple[str, str]]:
    for package in os.listdir(path):
        package_path = os.path.join(path, package)
        if not os.path.isdir(package_path):
            continue

        for cygport in os.listdir(package_path):
            if not cygport.endswith('.cygport'):
                continue

            yield os.path.join(package_path, cygport), cygport


class YACPGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right('+')

        for cygport_path, cygport_name in _iter_cygports(path):
            pkg = factory.begin(cygport_name)

            # XXX: save *bl* to rawversion
            match = re.match('(.*)-[0-9]+bl[0-9]+\\.cygport$', cygport_name)
            if not match:
                pkg.log('unable to parse cygport name', severity=Logger.ERROR)
                continue

            name, version = match.group(1).rsplit('-', 1)

            pkg.set_name(name)
            pkg.set_version(version, normalize_version)

            # these fields not contain variables (for now), so are safe to extract
            with open(cygport_path, 'r') as cygdata:
                for line in cygdata:
                    match = re.match('CATEGORY="([^"$]+)"', line)
                    if match:
                        pkg.add_categories(match.group(1))

                    match = re.match('SUMMARY="([^"$]+)"', line)
                    if match:
                        pkg.set_summary(match.group(1))

            yield pkg
