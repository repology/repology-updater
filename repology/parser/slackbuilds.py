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

import os
import sys

from repology.package import Package
from repology.util import GetMaintainers


class SlackBuildsParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        for category in os.listdir(path):
            if category.startswith('.'):
                continue

            category_path = os.path.join(path, category)
            if not os.path.isdir(category_path):
                continue

            for package in os.listdir(category_path):
                package_path = os.path.join(category_path, package)
                if not os.path.isdir(package_path):
                    continue

                info_path = os.path.join(category_path, package, package + '.info')
                if not os.path.isfile(info_path):
                    print('WARNING: {} does not exist, package skipped'.format(info_path), file=sys.stderr)
                    continue

                with open(info_path, encoding='utf-8', errors='ignore') as infofile:
                    pkg = Package()

                    pkg.category = category

                    for line in infofile:
                        line = line.strip()

                        if line.startswith('PRGNAM='):
                            pkg.name = line[7:].strip('"')
                        elif line.startswith('VERSION='):
                            pkg.version = line[8:].strip('"')
                        elif line.startswith('HOMEPAGE='):
                            pkg.homepage = line[9:].strip('"')
                        elif line.startswith('EMAIL='):
                            pkg.maintainers += GetMaintainers(line[6:].strip('"'))
                        elif line.startswith('DOWNLOAD='):
                            pkg.downloads.append(line[9:].strip('"'))

                    if pkg.name is not None and pkg.version is not None:
                        result.append(pkg)
                    else:
                        print('WARNING: {} skipped, likely due to parsing problems'.format(info_path), file=sys.stderr)

        return result
