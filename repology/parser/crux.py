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


class CRUXParser():
    def __init__(self):
        pass

    def Parse(self, path):
        packages = []

        for pkgdir in os.listdir(path):
            pkgpath = os.path.join(path, pkgdir, 'Pkgfile')
            if not os.path.exists(pkgpath):
                continue

            with open(pkgpath, 'r', encoding='utf-8', errors='ignore') as pkgfile:
                pkg = Package()

                for line in pkgfile:
                    line = line.strip()
                    if line.startswith('# Description:'):
                        if not pkg.comment:
                            pkg.comment = line[14:].strip()
                        else:
                            print('WARNING: duplicate Description for {}'.format(pkgdir), file=sys.stderr)

                    if line.startswith('# URL:'):
                        if not pkg.homepage:
                            pkg.homepage = line[6:].strip()
                        else:
                            print('WARNING: duplicate URL for {}'.format(pkgdir), file=sys.stderr)

                    if line.startswith('# Maintainer:'):
                        maintainer = line[13:].strip()
                        if ',' in maintainer:
                            _, email = line[13:].strip().split(',', 1)
                            pkg.maintainers += GetMaintainers(email)
                        else:
                            print('WARNING: bad Maintainer format for {}'.format(pkgdir), file=sys.stderr)

                    if line.startswith('name=') and not pkg.name:
                        pkg.name = line[5:]

                    if line.startswith('version=') and not pkg.version:
                        pkg.version = line[8:]

                if not pkg.name or not pkg.version:
                    print('WARNING: unable to parse port form {}: no name or version'.format(pkgdir), file=sys.stderr)
                    continue

                if '$' in pkg.name or '$' in pkg.version:
                    print('WARNING: unable to parse port form {}: name or version contain variables'.format(pkgdir), file=sys.stderr)
                    continue

                packages.append(pkg)

        return packages
