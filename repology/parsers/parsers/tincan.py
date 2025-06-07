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

from repology.logger import Logger
from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.walk import walk_tree

def iter_sources(sources: list[str]):
    for url in sources:
        if '://' in url:
            yield url

class TinCanGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for info_path_abs in walk_tree(path, name='package.toml'):
            package_path_abs = os.path.dirname(info_path_abs)
            package_subdir = os.path.basename(package_path_abs)

            with factory.begin(package_subdir) as pkg: 
                with open(info_path_abs, 'r') as f:
                    info_contents = f.read()
                    pkgdata = tomli.loads(info_contents)

                pkg.add_name(package_subdir, NameType.GENERIC_SRC_NAME) 
                pkg.set_version(pkgdata['meta']['version'])
                pkg.add_links(LinkType.UPSTREAM_DOWNLOAD, iter_sources(pkgdata['meta']['sources']))
                pkg.add_maintainers(extract_maintainers(pkgdata['meta']['maintainer']))

                yield pkg

