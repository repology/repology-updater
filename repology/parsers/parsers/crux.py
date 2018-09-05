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

from repology.logger import Logger
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers


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


class CRUXParser(Parser):
    def iter_parse(self, path, factory):
        for pkgdir in os.listdir(path):
            pkgpath = os.path.join(path, pkgdir, 'Pkgfile')
            if not os.path.exists(pkgpath):
                continue

            with open(pkgpath, 'r', encoding='utf-8', errors='ignore') as pkgfile:
                pkg = factory.begin()

                for line in pkgfile:
                    line = line.strip()
                    if line.startswith('# Description:'):
                        if not pkg.comment:
                            pkg.comment = line[14:].strip()
                        else:
                            factory.log('duplicate Description for {}'.format(pkgdir), severity=Logger.ERROR)

                    if line.startswith('# URL:'):
                        if not pkg.homepage:
                            pkg.homepage = line[6:].strip()
                        else:
                            factory.log('duplicate URL for {}'.format(pkgdir), severity=Logger.ERROR)

                    if line.startswith('# Maintainer:'):
                        maintainer = line[13:].strip()
                        if ',' in maintainer:
                            _, email = line[13:].strip().split(',', 1)
                            pkg.maintainers += extract_maintainers(email)
                        else:
                            factory.log('unexpected Maintainer format for {}'.format(pkgdir), severity=Logger.ERROR)

                    if line.startswith('name=') and not pkg.name:
                        pkg.name = line[5:]

                    if line.startswith('version=') and not pkg.version:
                        pkg.version = line[8:]

                if not pkg.name or not pkg.version:
                    factory.log('unable to parse port form {}: no name or version'.format(pkgdir), severity=Logger.ERROR)
                    continue

                if '$' in pkg.name or '$' in pkg.version:
                    factory.log('unable to parse port form {}: name or version contain variables'.format(pkgdir), severity=Logger.ERROR)
                    continue

                yield pkg
