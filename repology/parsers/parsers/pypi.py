# Copyright (C) 2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


class PyPiCacheJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for pkgdata in iter_json_list(path, (None,)):
            with factory.begin() as pkg:
                info = pkgdata['info']

                pkg.add_name(info['name'], NameType.PYPI_NAME)
                pkg.set_version(info['version'])

                if info['home_page']:
                    pkg.add_homepages(info['home_page'])
                pkg.add_homepages(info['project_url'])

                if info['author_email']:
                    pkg.add_maintainers(map(str.strip, info['author_email'].split(',')))

                if info['summary']:
                    pkg.set_summary(info['summary'])

                release_items = pkgdata['releases'][info['version']]

                pkg.add_downloads(item['url'] for item in release_items)

                yield pkg
