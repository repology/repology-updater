# Copyright (C) 2025 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import json
from typing import Iterable

from repology.logger import Logger
from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser


def _iter_packages(path: str) -> Iterable[dict[str, str]]:
    with open(path, encoding='utf-8', errors='ignore') as f:
        for line in f:
            yield json.loads(line.strip())


class StalixJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for pkgdata in _iter_packages(path):
            with factory.begin() as pkg:
                # a hack because we have no way to pass arbitrary flag to the ruleset
                # in fact the prefix should be added by 500ths rules
                prefix = ''
                match pkgdata.get('lang_module'):
                    case None:
                        pass
                    case 'python':
                        prefix = 'python:'
                    case 'perl':
                        prefix = 'perl:'
                    case other:
                        pkg.log(f'unhandled lang_module {other}', Logger.WARNING)

                pkg.add_name(prefix + pkgdata['pkg_name'], NameType.STALIX_PKG_NAME)
                pkg.add_name(pkgdata['ix_pkg_name'], NameType.STALIX_IX_PKG_NAME)
                pkg.add_name(pkgdata['ix_pkg_full_name'], NameType.STALIX_IX_PKG_FULL_NAME)
                pkg.set_version(pkgdata['pkg_ver'])
                pkg.add_categories(pkgdata['category'])
                pkg.add_maintainers(pkgdata['maintainers'])
                pkg.add_links(LinkType.UPSTREAM_DOWNLOAD, pkgdata['upstream_urls'])

                yield pkg
