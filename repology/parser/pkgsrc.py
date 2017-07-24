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

import re
import sys

from repology.package import Package
from repology.util import GetMaintainers, SplitPackageNameVersion


def SanitizeVersion(version):
    origversion = version

    match = re.match('(.*)nb[0-9]+$', version)
    if match is not None:
        version = match.group(1)

    if version != origversion:
        return version, origversion
    else:
        return version, None


class PkgsrcIndexParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        with open(path, encoding='utf-8') as indexfile:
            for line in indexfile:
                fields = line.strip().split('|')
                if len(fields) != 12:
                    print('WARNING: package {} skipped, incorrect number of fields in INDEX'.format(fields[0]), file=sys.stderr)
                    continue
                if not fields[0]:
                    print('WARNING: line {} bogus, critical fields are empty'.format(line.strip()), file=sys.stderr)
                    continue

                pkg = Package()

                pkg.name, version = SplitPackageNameVersion(fields[0])
                pkg.version, pkg.origversion = SanitizeVersion(version)
                pkg.comment = fields[3]
                if fields[11]:
                    pkg.homepage = fields[11]

                # sometimes OWNER variable is used in which case
                # there's no MAINTAINER OWNER doesn't get to INDEX
                pkg.maintainers = GetMaintainers(fields[5])

                pkg.category = fields[6].split(' ')[0]

                pkg.extrafields['portname'] = fields[1].split('/')[-1]
                pkg.extrafields['origin'] = fields[1]

                result.append(pkg)

        return result
