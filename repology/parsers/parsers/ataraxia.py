# Copyright (C) 2017-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Iterable

from repology.logger import Logger
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.transformer import PackageTransformer


class AtaraxiaParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        packages_path = os.path.join(path, 'packages')
        for pkgdir in os.listdir(packages_path):
            pkgpath = os.path.join(packages_path, pkgdir, 'KagamiBuild')
            if not os.path.exists(pkgpath):
                continue

            with open(pkgpath, 'r', encoding='utf-8', errors='ignore') as pkgfile:
                pkg = factory.begin()

                pkg.set_origin(pkgdir)

                for line in pkgfile:
                    line = line.strip()
                    if line.startswith('# Description:'):
                        pkg.set_summary(line.split(':', 1)[1])

                    if line.startswith('# URL:'):
                        pkg.add_homepages(line.split(':', 1)[1])

                    if line.startswith('# Maintainer:'):
                        maintainer = line.split(':', 1)[1].strip()
                        if ',' in maintainer:
                            _, email = maintainer.split(',', 1)
                            pkg.add_maintainers(extract_maintainers(email))
                        else:
                            pkg.log('unexpected Maintainer format "{}"'.format(maintainer), severity=Logger.ERROR)

                    if line.startswith('name=') and not pkg.name:
                        pkg.set_name(line.split('=', 1)[1])

                    if line.startswith('version=') and not pkg.version:
                        pkg.set_version(line.split('=', 1)[1])

                if pkg.name and '$' in pkg.name:
                    pkg.log('name contains variables, unable to parse: {}'.format(pkg.name), severity=Logger.ERROR)
                    continue

                if pkg.version and '$' in pkg.version:
                    pkg.log('version contains variables, unable to parse: {}'.format(pkg.version), severity=Logger.ERROR)
                    continue

                yield pkg
