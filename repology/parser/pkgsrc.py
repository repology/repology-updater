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

from ..util import SplitPackageNameVersion
from ..package import Package

def SanitizeVersion(version):
    match = re.match("(.*)nb[0-9]+$", version)
    if not match is None:
        version = match.group(1)

    return version

class PkgSrcPackagesSHA512Parser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        with open(path) as file:
            for line in file:
                pkgname = line[12:-137]

                if pkgname.find('-') == -1:
                    continue

                pkg = Package()

                pkg.name, pkg.fullversion = SplitPackageNameVersion(pkgname)
                pkg.version = SanitizeVersion(pkg.fullversion)

                result.append(pkg)

        return result

class PkgSrcReadmeAllParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        with open(path, encoding="utf-8") as file:
            pkg = Package()
            for line in file:
                line = line[:-1]

                if line.find('(for sorting)') == -1:
                    continue

                parts = re.split("<[^<>]+>", line)

                if len(parts) != 10:
                    continue

                pkg = Package()

                pkg.name, pkg.fullversion = SplitPackageNameVersion(parts[4])
                pkg.version = SanitizeVersion(pkg.fullversion)
                pkg.category = parts[7]
                pkg.comment = parts[9]

                result.append(pkg)

        return result
