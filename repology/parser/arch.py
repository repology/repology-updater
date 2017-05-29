# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import sys

from repology.package import Package
from repology.util import GetMaintainers


def SanitizeVersion(version):
    origversion = version

    pos = version.find('-')
    if pos != -1:
        version = version[:pos]

    pos = version.find(':')
    if pos != -1:
        version = version[pos + 1:]

    pos = version.find('+')
    if pos != -1:
        version = version[:pos]

    if version != origversion:
        return version, origversion
    else:
        return version, None


class ArchDBParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        for package in os.listdir(path):
            desc_path = os.path.join(path, package, 'desc')
            if not os.path.isfile(desc_path):
                continue

            with open(desc_path, encoding='utf-8') as file:
                pkg = Package()

                tag = None
                for line in file:
                    line = line.strip()

                    if line == '':
                        tag = None
                    elif tag == 'NAME':
                        pkg.name = line
                    elif tag == 'VERSION':
                        pkg.version, pkg.origversion = SanitizeVersion(line)
                    elif tag == 'DESC':
                        if pkg.comment is None:
                            pkg.comment = ''
                        if pkg.comment != '':
                            pkg.comment += '\n'
                        pkg.comment += line
                    elif tag == 'URL':
                        pkg.homepage = line
                    elif tag == 'LICENSE':
                        pkg.licenses.append(line)
                    elif tag == 'PACKAGER':
                        pkg.maintainers += GetMaintainers(line)
                    elif line.startswith('%') and line.endswith('%'):
                        tag = line[1:-1]

                if pkg.name is not None and pkg.version is not None:
                    result.append(pkg)
                else:
                    print('WARNING: %s skipped, likely due to parsing problems' % package, file=sys.stderr)

        return result
