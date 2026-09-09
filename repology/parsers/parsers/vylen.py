# Copyright (C) 2026 CELESTIFYX Team <celestifyx@gmail.com>
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
from repology.package import LinkType
from repology.parsers import Parser
from repology.parsers.json import iter_json_list
from repology.parsers.maintainers import extract_maintainers


class VylenPackagesJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for pkgdata in iter_json_list(path, (None,)):
            with factory.begin() as pkg:
                pkg.add_name(pkgdata['name'], NameType.GENERIC_SRC_NAME)
                pkg.set_version(pkgdata['version'])
                pkg.set_rawversion(pkgdata['version'] + '-' + pkgdata['release'])
                pkg.set_summary(pkgdata['description'])
                pkg.add_links(LinkType.PROJECT_HOMEPAGE, pkgdata['homepage'])
                pkg.add_maintainers(extract_maintainers(pkgdata['maintainer']))

                for source in pkgdata.get('source', []):
                    url = source.get('url')

                    if source.get('type') == 'ext':
                        pkg.add_links(LinkType.UPSTREAM_DOWNLOAD, url)
                    elif url.endswith(('.patch', '.diff')):
                        pkg.add_links(LinkType.PACKAGE_PATCH, url)
                        pkg.add_links(LinkType.PACKAGE_PATCH_RAW, url.replace('/-/blob/', '/-/raw/'))

                yield pkg
