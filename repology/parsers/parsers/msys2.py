# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.logger import Logger
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.versions import VersionStripper


def _parse_descfile(path):
    data = {}
    with open(path, 'r', encoding='utf-8') as descfile:
        key = None
        value = []

        for line in descfile:
            line = line.strip()
            if line.startswith('%') and line.endswith('%'):
                key = line[1:-1]
                value = []
            elif line == '':
                data[key] = value
            else:
                value.append(line)


class MSYS2Parser(Parser):
    def iter_parse(self, path, factory):
        normalize_version = VersionStripper().strip_right('-')

        for packagedir in os.listdir(path):
            pkg = factory.begin(packagedir)

            data = _parse_descfile(os.path.join(path, packagedir, 'desc'))

            if 'BASE' in data and data['NAME'][0] != data['BASE'][0]:
                pkg.log('skipped, subpackage', severity=Logger.WARNING)
                # XXX: include subpackages
                continue

            pkg.set_name(data['NAME'][0])
            pkg.set_version(data['VERSION'][0], normalize_version)

            if 'DESC' in data:
                pkg.set_summary(data['DESC'][0])

            pkg.add_homepages(data.get('URL'))

            pkg.add_licenses(data.get('LICENSE'))

            pkg.add_maintainers(map(extract_maintainers, data['PACKAGER']))

            pkg.add_categories(data.get('GROUPS'))

            yield pkg
