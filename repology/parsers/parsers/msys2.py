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
from collections import defaultdict
from typing import Dict, Iterable, List

from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.versions import VersionStripper
from repology.transformer import PackageTransformer


def _parse_descfile(path: str) -> Dict[str, List[str]]:
    data: Dict[str, List[str]] = defaultdict(list)

    with open(path, 'r', encoding='utf-8') as descfile:
        key = ''
        for line in descfile:
            line = line.strip()
            if line.startswith('%') and line.endswith('%'):
                key = line[1:-1]
            elif line:
                data[key].append(line)

    return data


class MSYS2DescParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right('-')

        for packagedir in os.listdir(path):
            with factory.begin(packagedir) as pkg:
                data = _parse_descfile(os.path.join(path, packagedir, 'desc'))

                pkg.set_name(data['NAME'][0])
                if 'BASE' in data:
                    pkg.set_basename(data['BASE'][0])
                pkg.set_version(data['VERSION'][0], normalize_version)

                if 'DESC' in data:
                    pkg.set_summary(data['DESC'][0])

                pkg.add_homepages(data.get('URL'))
                pkg.add_licenses(data.get('LICENSE'))
                pkg.add_maintainers(map(extract_maintainers, data['PACKAGER']))
                pkg.add_categories(data.get('GROUPS'))

                yield pkg
