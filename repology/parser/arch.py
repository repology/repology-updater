# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from pkg_resources import parse_version

from ..util import VersionCompare
from ..package import Package

def SanitizeVersion(version):
    pos = version.find('-')
    if pos != -1:
        version = version[0:pos]

    pos = version.find(':')
    if pos != -1:
        version = version[pos+1:]

    return version

class ArchDBParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        for package in os.listdir(path):
            desc_path = os.path.join(path, package, "desc")
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
                        pkg.fullversion = line
                        pkg.version = SanitizeVersion(pkg.fullversion)
                    elif tag == 'DESC':
                        if pkg.comment is None:
                            pkg.comment = ''
                        if pkg.comment != '':
                            pkg.comment += "\n"
                        pkg.comment += line
                    elif tag == 'URL':
                        pkg.homepage = line
                    elif tag == 'LICENSE':
                        if pkg.license is None:
                            pkg.license = []
                        pkg.license.append(line)
                    elif tag == 'PACKAGER':
                        pkg.maintainers.append(line)
                    elif line.startswith('%') and line.endswith('%'):
                        tag = line[1:-1]

                if pkg.name is not None and pkg.version is not None:
                    result.append(pkg)

        return result
