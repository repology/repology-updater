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
from typing import Dict, Iterable, Optional, Tuple

from repology.logger import Logger
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.transformer import PackageTransformer


def _iter_packages(path: str) -> Iterable[Tuple[str, str]]:
    for category in os.listdir(path):
        if category.startswith('.'):
            continue

        category_path = os.path.join(path, category)
        if not os.path.isdir(category_path):
            continue

        for package in os.listdir(category_path):
            package_path = os.path.join(category_path, package)
            if not os.path.isdir(package_path):
                continue

            yield category, package


def _parse_infofile(path: str) -> Dict[str, str]:
    variables: Dict[str, str] = {}

    with open(path, encoding='utf-8', errors='ignore') as infofile:
        key: Optional[str] = None
        total_value = []

        for line in infofile:
            line = line.strip()
            if not line:
                continue

            if key:  # continued
                value = line
            else:  # new variable
                key, value = line.split('=', 1)
                value = value.lstrip('"').lstrip()

            if value.endswith('\\'):  # will continue
                total_value.append(value.rstrip('\\').rstrip())
            elif not value or value.endswith('"'):
                total_value.append(value.rstrip('"').rstrip())
                variables[key] = ' '.join(total_value)
                key = None
                total_value = []

    return variables


class SlackBuildsParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for category, pkgname in _iter_packages(path):
            pkg = factory.begin(category + '/' + pkgname)

            info_path = os.path.join(path, category, pkgname, pkgname + '.info')
            if not os.path.isfile(info_path):
                pkg.log('.info file does not exist', severity=Logger.ERROR)
                continue

            pkg.add_categories(category)

            variables = _parse_infofile(info_path)

            pkg.set_name(variables['PRGNAM'])
            pkg.set_version(variables['VERSION'])
            pkg.add_homepages(variables['HOMEPAGE'])
            pkg.add_maintainers(extract_maintainers(variables['EMAIL']))

            for key in ['DOWNLOAD', 'DOWNLOAD_x86_64']:
                if variables[key] not in ['', 'UNSUPPORTED', 'UNTESTED']:
                    pkg.add_downloads(variables[key].split())

            yield pkg
