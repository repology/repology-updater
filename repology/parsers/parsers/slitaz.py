# Copyright (C) 2018-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.package import PackageFlags
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_list
from repology.transformer import PackageTransformer


class SliTazJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for item in iter_json_list(path, ('items', None)):
            with factory.begin() as pkg:
                pkg.set_basename(item['meta'])
                pkg.set_version(item['ver'])
                pkg.add_maintainers(item['maintainer'])
                pkg.add_licenses(item['license'])
                pkg.add_homepages(item['home'])
                pkg.add_downloads(item.get('src'))

                if pkg.version == 'latest':
                    pkg.set_flags(PackageFlags.ROLLING)

                for subitem in item['pkgs']:
                    subpkg = pkg.clone()

                    subpkg.add_categories(subitem['cat'])
                    subpkg.set_summary(subitem['desc'])
                    subpkg.set_name(subitem['name'])
                    subpkg.set_version(subitem.get('ver'))

                    yield subpkg
