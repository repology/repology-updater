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
import re
import sys

from repology.package import Package
from repology.util import SplitPackageNameVersion


def SanitizeVersion(version):
    origversion = version

    pos = version.rfind('+')
    if pos != -1:
        version = version[0:pos]

    if version != origversion:
        return version, origversion
    else:
        return version, None


class YACPGitParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        for package in os.listdir(path):
            package_path = os.path.join(path, package)
            if not os.path.isdir(package_path):
                continue

            for cygport in os.listdir(package_path):
                if not cygport.endswith('.cygport'):
                    continue

                # XXX: save *bl* to origversion
                match = re.match('(.*)-[0-9]+bl[0-9]+\.cygport$', cygport)

                if not match:
                    print('WARNING: unable to parse cygport: {}'.format(cygport), file=sys.stderr)
                    continue

                pkg = Package()
                pkg.name, version = SplitPackageNameVersion(match.group(1))
                pkg.version, pkg.origversion = SanitizeVersion(version)

                result.append(pkg)

        return result
