# Copyright (C) 2018-2019,2022 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.logger import Logger
from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_dict


class CondaRepodataJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for pkgfilename, pkgdata in iter_json_dict(path, ('packages', None)):
            with factory.begin(pkgfilename) as pkg:
                raise RuntimeError('recheck if GENERIC_SRC_NAME is correct here')
                pkg.add_name(pkgdata['name'], NameType.GENERIC_SRC_NAME)  # type: ignore
                pkg.set_version(pkgdata['version'])
                pkg.add_licenses(pkgdata.get('license', ''))

                yield pkg


class CondaChanneldataJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for pkgname, pkgdata in iter_json_dict(path, ('packages', None)):
            with factory.begin(pkgname) as pkg:
                pkg.add_name(pkgname, NameType.GENERIC_SRC_NAME)
                if 'version' not in pkgdata:
                    pkg.log('version missing', Logger.ERROR)
                    continue

                pkg.set_version(pkgdata['version'])
                pkg.add_licenses(pkgdata.get('license'))
                pkg.set_summary(pkgdata.get('summary'))
                pkg.add_links(LinkType.UPSTREAM_DOCUMENTATION, pkgdata.get('doc_url'), pkgdata.get('doc_source_url'))
                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, pkgdata.get('home'))
                pkg.add_links(LinkType.UPSTREAM_DOWNLOAD, pkgdata.get('source_url'))
                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, pkgdata.get('dev_url'))

                yield pkg
