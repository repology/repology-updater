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

import json
import os

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


class AURParser():
    def __init__(self):
        pass

    def Parse(self, path):
        packages = []

        for filename in os.listdir(path):
            if not filename.endswith('.json'):
                continue

            with open(os.path.join(path, filename), 'r') as jsonfile:
                for result in json.load(jsonfile)['results']:
                    pkg = Package()

                    pkg.name = result['Name']

                    for badsuffix in ['-cvs', '-svn', '-hg', '-darcs', '-bzr', '-git', '-bin']:
                        if pkg.name.endswith(badsuffix):
                            pkg.effname = pkg.name[:-len(badsuffix)]
                            pkg.ignoreversion = True
                            break

                    pkg.version, pkg.origversion = SanitizeVersion(result['Version'])
                    pkg.comment = result['Description']
                    pkg.homepage = result['URL']

                    if 'License' in result:
                        for license in result['License']:
                            pkg.licenses.append(license)

                    if 'Maintainer' in result and result['Maintainer']:
                        pkg.maintainers += GetMaintainers(result['Maintainer'] + '@aur')

                    packages.append(pkg)

        return packages
