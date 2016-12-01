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

import re

from ..package import Package


def SanitizeVersion(version):
    origversion = version

    pos = version.find(':')
    if pos != -1:
        version = version[pos+1:]

    pos = version.find('-')
    if pos != -1:
        version = version[0:pos]

    pos = version.find('+')
    if pos != -1:
        version = version[0:pos]

    pos = version.find('~')
    if pos != -1:
        version = version[0:pos]

    match = re.match("(.*[0-9])[^0-9]*dfsg\\.?[0-9]*$", version)
    if match is not None:
        version = match.group(1)

    match = re.match("(.*[0-9])ubuntu[0-9.]+$", version)
    if match is not None:
        version = match.group(1)

    if version != origversion:
        return version, origversion
    else:
        return version, None


class DebianSourcesParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        with open(path, encoding='utf-8') as file:
            pkg = Package()
            for line in file:
                line = line.strip()
                if line == "":
                    result.append(pkg)
                    pkg = Package()
                elif line.startswith('Package: '):
                    pkg.name = line[9:]
                elif line.startswith('Version: '):
                    pkg.version, pkg.fullversion = SanitizeVersion(line[9:])
                elif line.startswith('Maintainer: '):
                    pkg.maintainers.append(line[12:])
                elif line.startswith('Uploaders: '):
                    for m in re.findall("(?:\"[^\"]*\"|[^,])+", line[11:]):
                        pkg.maintainers.append(m.strip())
                elif line.startswith('Section: '):
                    pkg.category = line[9:]
                elif line.startswith('Homepage: '):
                    pkg.homepage = line[10:]

        return result
