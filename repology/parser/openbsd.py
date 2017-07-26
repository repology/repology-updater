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

import csv
import re

from repology.package import Package
from repology.util import GetMaintainers, SplitPackageNameVersion


def SanitizeVersion(version):
    origversion = version

    match = re.match('(.*)v[0-9]+$', version)
    if match is not None:
        version = match.group(1)

    match = re.match('(.*)p[0-9]+$', version)
    if match is not None:
        version = match.group(1)

    if version != origversion:
        return version, origversion
    else:
        return version, None


class OpenBSDIndexParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        with open(path, encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='|')
            for row in reader:
                pkg = Package()

                pkgname = row[0]

                # cut away string suffixws which come after version
                match = re.match('(.*?)(-[a-z_]+[0-9]*)+$', pkgname)
                if match is not None:
                    pkgname = match.group(1)

                pkg.name, version = SplitPackageNameVersion(pkgname)
                pkg.version, pkg.origversion = SanitizeVersion(version)
                pkg.comment = row[3]
                pkg.maintainers = GetMaintainers(row[5])
                pkg.category = row[6].split(' ')[0].strip()

                origin = row[1].rsplit(',', 1)[0]
                pkg.extrafields['portname'] = origin.split('/')[1]
                pkg.extrafields['origin'] = origin

                result.append(pkg)

        return result
