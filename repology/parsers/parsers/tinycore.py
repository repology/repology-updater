# Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Dict, Iterable

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


def _parse_infofile(path: str) -> Dict[str, str]:
    data: Dict[str, str] = {}

    with open(path, 'r', encoding='utf-8', errors='ignore') as infofile:
        key = None

        for line in infofile:
            match = re.fullmatch('([A-Za-z-]+):[ \t]*(.*?)', line, re.DOTALL)

            if match:
                key = match.group(1).lower()
                if 'see list of sites below' not in line:
                    data[key] = match.group(2).strip()
            elif key:
                if 'see list of sites below' not in line:
                    data[key] += '\n' + line.strip()
            else:
                raise RuntimeError('Rogue string without key')

    return data


class TczInfoParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for filename in os.listdir(path):
            if not filename.endswith('.tcz.info'):
                continue

            with factory.begin(filename) as pkg:
                data = _parse_infofile(os.path.join(path, filename))

                pkg.add_name(filename[:-9], NameType.UNSUPPORTED)
                pkg.set_version(data['version'])
                pkg.set_summary(data['description'])

                pkg.add_homepages(data.get('original-site'))
                pkg.add_licenses(data.get('copying-policy'))

                yield pkg
