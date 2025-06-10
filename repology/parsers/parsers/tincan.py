# Copyright (C) 2025 AVS Origami <avs.origami@gmail.com>
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

from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.walk import walk_tree


class TinCanGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for info_path_abs in walk_tree(path, name='package.toml'):
            package_path_abs = os.path.dirname(info_path_abs)
            package_subdir = os.path.basename(package_path_abs)
            files_path_abs = os.path.join(package_path_abs, 'files')

            with factory.begin(package_subdir) as pkg:
                with open(info_path_abs, 'r') as f:
                    info_contents = f.read()
                    pkgdata = tomli.loads(info_contents)

                pkg.add_name(package_subdir, NameType.GENERIC_SRC_NAME)
                pkg.set_version(pkgdata['meta']['version'])
                pkg.add_links(LinkType.UPSTREAM_DOWNLOAD, [url for url in pkgdata['meta']['sources'] if '://' in url])
                pkg.add_maintainers(extract_maintainers(pkgdata['meta']['maintainer']))

                if os.path.exists(files_path_abs):
                    patches = sorted((
                        os.path.relpath(path, files_path_abs)
                        for path in walk_tree(files_path_abs, suffix='.patch')
                    ))
                    if len(patches) > 0:
                        pkg.set_extra_field('patch', patches)

                yield pkg
