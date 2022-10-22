# Copyright (C) 2022 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import tomli

from repology.logger import Logger
from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.walk import walk_tree


class GlaucusGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for ceras_path_abs in walk_tree(path, name='ceras'):
            package_path_abs = os.path.dirname(ceras_path_abs)
            package_subdir = os.path.basename(package_path_abs)

            with factory.begin(package_subdir) as pkg:
                patches_path_abs = os.path.join(package_path_abs, 'patches')

                with open(ceras_path_abs, 'rb') as f:
                    pkgdata = tomli.load(f)

                pkg.add_name(pkgdata['nom'], NameType.GENERIC_SRC_NAME)

                if package_subdir != pkgdata['nom']:
                    raise RuntimeError(f'package subdir "{package_subdir}" is expected to be equal to package name "{pkgdata["nom"]}"')

                if 'ver' not in pkgdata:
                    pkg.log('package without version, skipping', Logger.ERROR)
                    continue
                if 'url' not in pkgdata:
                    pkg.log('package without url, assuming virtual package and skipping', Logger.ERROR)
                    continue

                pkg.set_version(pkgdata['ver'])
                pkg.set_summary(pkgdata.get('cnt'))
                pkg.add_links(LinkType.UPSTREAM_DOWNLOAD, pkgdata.get('url'))

                if os.path.exists(patches_path_abs):
                    pkg.set_extra_field(
                        'patch',
                        sorted(
                            os.path.relpath(patch_path_abs, patches_path_abs)
                            for patch_path_abs in walk_tree(patches_path_abs, suffix='.patch')
                        )
                    )

                yield pkg
