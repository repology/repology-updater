# Copyright (C) 2021 Vanessa Sochat
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

from typing import Iterable

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_list
from repology.transformer import PackageTransformer
from repology.parsers.versions import VersionStripper
import json

class SpackJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_left(':')

        for pkgdata in iter_json_list(path, ('packages', None)):
            with factory.begin() as pkg:

                pkg.add_name(pkgdata['name'], NameType.SPACK)
                pkg.set_version(pkgdata['version'], normalize_version)
                pkg.set_rawversion(pkgdata['version'])

                # We don't currently have good keywords, could in the future!
                # pkg.add_categories(packagedata['keywords'])
                pkg.add_homepages(pkgdata['homepages'])
                pkg.add_downloads(pkgdata['downloads'])
                pkg.set_summary(pkgdata['summary'])
                # Ensure that maintainer usernames are in context of spack
                pkg.add_maintainers(["%s @spack" %x for x in pkgdata['maintainers']])
                # Not currently used/needed, but available
                # pkg.set_extra_field('dependencies', packagedata['dependencies'])
                yield pkg


