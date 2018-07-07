# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import json
import re

from repology.package import Package
from repology.util import GetMaintainers


def SanitizeVersion(version):
    origversion = version

    version = version.rsplit(':', 1)[-1]

    if version != origversion:
        return version, origversion
    else:
        return version, None


class TermuxJsonParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        with open(path, 'r', encoding='utf-8') as jsonfile:
            for packagedata in json.load(jsonfile):
                pkg = Package()
                pkg.name = packagedata['name']
                pkg.version, pkg.origversion = SanitizeVersion(packagedata['version'])

                pkg.comment = packagedata['description']
                pkg.homepage = packagedata['homepage']

                if 'srcurl' in packagedata:
                    pkg.downloads = [packagedata['srcurl']]

                match = re.search(' @([^ ]+)$', packagedata['maintainer'])
                if match:
                    pkg.maintainers = [match.group(1).lower() + '@termux']
                else:
                    pkg.maintainers = GetMaintainers(packagedata['maintainer'])

                result.append(pkg)

        return result
