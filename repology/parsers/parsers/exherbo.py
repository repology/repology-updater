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

from repology.package import PackageFlags
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.transformer import PackageTransformer


def _normalize_version(version: str) -> str:
    return re.sub('-r[0-9]+$', '', version)


def _iter_exheres(path: str) -> Iterable[Tuple[str, str, str]]:
    for category in os.listdir(path):
        category_path = os.path.join(path, category)
        if not os.path.isdir(category_path):
            continue
        if category == 'virtual' or category == 'metadata':
            continue

        for package in os.listdir(category_path):
            package_path = os.path.join(category_path, package)
            if not os.path.isdir(package_path):
                continue

            for exheres in os.listdir(package_path):
                if not exheres.startswith(package + '-') and not exheres.endswith('.exheres-0'):
                    continue

                yield category, package, exheres


def _get_repo_maintainers(path):
    with open(os.path.join(path, 'metadata/about.conf'), 'r', encoding='utf-8') as metadata:
        for line in metadata:
            if '=' in line:
                key, value = map(lambda s: s.strip(), line.split('=', 1))

                if key == 'owner':
                    return extract_maintainers(value)

    return []


class ExherboGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        maintainers = _get_repo_maintainers(path)

        for category, package, exheres in _iter_exheres(os.path.join(path, 'packages')):
            pkg = factory.begin('/'.join((category, package, exheres)))

            pkg.set_name(package)
            pkg.set_version(exheres[len(package) + 1:-10], _normalize_version)
            pkg.add_categories(category)
            pkg.add_maintainers(maintainers)

            if pkg.version == 'scm' or pkg.version.endswith('-scm'):
                pkg.set_flags(PackageFlags.rolling)

            yield pkg
