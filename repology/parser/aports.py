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

from repology.package import Package
from repology.util import GetMaintainers


def SanitizeVersion(version):
    origversion = version

    match = re.match('(.*)-r[0-9]+$', version)
    if match is not None:
        version = match.group(1)

    if version != origversion:
        return version, origversion
    else:
        return version, None


class ApkIndexParser():
    def __init__(self):
        pass

    def Parse(self, path):
        packages = []

        with open(os.path.join(path, 'APKINDEX'), 'r', encoding='utf-8') as apkindex:
            state = {}
            for line in apkindex:
                line = line.strip()
                if line:
                    state[line[0]] = line[2:].strip()
                    continue

                if not state:
                    continue

                if state['P'] != state['o']:
                    continue

                pkg = Package()

                pkg.name = state['P']
                pkg.version, pkg.origversion = SanitizeVersion(state['V'])

                pkg.comment = state['T']
                pkg.homepage = state['U']  # XXX: switch to homepages, split
                pkg.licenses = [state['L']]

                if 'm' in state:
                    pkg.maintainers = GetMaintainers(state['m'])

                state = {}

                packages.append(pkg)

        return packages
