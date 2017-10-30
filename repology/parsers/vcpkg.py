# Copyright (C) 2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


def SanitizeVersion(version):
    origversion = version

    version = re.sub('[^0-9]*vcpkg.*$', '', version)  # vcpkg stuff
    version = re.sub('(alpha|beta|rc|patch)-([0-9]+)$', '\\1\\2', version)  # save from the following rule
    version = re.sub('-[0-9]+$', '', version)  # cut off revision
    version = re.sub('-[0-9a-f]{6,}$', '', version)  # drop commits

    if version != origversion:
        return version, origversion
    else:
        return version, None


class VcpkgGitParser():
    def __init__(self):
        pass

    def Parse(self, path):
        packages = []

        for pkgdir in os.listdir(os.path.join(path, 'ports')):
            controlpath = os.path.join(path, 'ports', pkgdir, 'CONTROL')
            if not os.path.exists(controlpath):
                continue

            pkg = Package(name=pkgdir)

            with open(controlpath, 'r', encoding='utf-8', errors='ignore') as controlfile:
                for line in controlfile:
                    line = line.strip()
                    if line.startswith('Version:'):
                        version = line[8:].strip()
                        match = re.match('[0-9]{4}[.-][0-9]{1,2}[.-][0-9]{1,2}', version)
                        if match:
                            pkg.version = version
                            pkg.ignoreversion = True
                        else:
                            pkg.version, pkg.origversion = SanitizeVersion(line[8:].strip())
                    elif line.startswith('Description:'):
                        comment = line[12:].strip()
                        if comment:
                            pkg.comment = comment

            if not pkg.version:
                print('WARNING: unable to parse port {}: no version'.format(pkgdir), file=sys.stderr)
                continue

            packages.append(pkg)

        return packages
