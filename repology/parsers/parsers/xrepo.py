# Copyright (C) 2026 Aleksandr Kovalko <gistrec@gmail.com>
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

from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_list


class XrepoJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for pkgdata in iter_json_list(path, ('packages', None)):
            if 'base' in pkgdata:
                continue

            with factory.begin() as pkg:
                pkg.add_name(pkgdata['name'], NameType.XREPO_NAME)

                pkg.set_summary(pkgdata.get('description'))
                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, pkgdata.get('homepage'))
                pkg.add_licenses(pkgdata.get('license'))
                pkg.add_links(LinkType.UPSTREAM_REPOSITORY, pkgdata.get('repository_url'))

                latest_version = pkgdata['version']

                for version in pkgdata.get('versions') or [latest_version]:
                    verpkg = pkg.clone()
                    verpkg.set_version(version)

                    if version == latest_version:
                        verpkg.add_links(LinkType.UPSTREAM_DOWNLOAD, pkgdata.get('download_urls') or pkgdata.get('download_url'))

                    patches = [patch for patch in pkgdata.get('patches', []) if f'/patches/{version}/' in patch]
                    if patches:
                        verpkg.set_extra_field('patch', patches)

                    yield verpkg
