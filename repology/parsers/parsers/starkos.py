# Copyright (C) 2026 starkOS GNU/Linux
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
from repology.parsers.maintainers import extract_maintainers


class StarkosJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for pkgdata in iter_json_list(path, (None,)):
            with factory.begin() as pkg:
                # init scripts for the s6 service manager, these are starkOS
                # specific glue (name-s6 -> service files for name), not
                # packages of an upstream project
                if pkgdata['repo'] == 's6' and pkgdata['name'].endswith('-s6'):
                    continue

                pkg.add_name(pkgdata['name'], NameType.GENERIC_SRC_NAME)
                pkg.set_subrepo(pkgdata['repo'])
                pkg.set_version(pkgdata['version'])
                pkg.set_rawversion(f'{pkgdata["version"]}-{pkgdata["release"]}')
                pkg.set_summary(pkgdata.get('description'))
                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, pkgdata.get('homepage'))

                # "Team name, address@domain" -> address@domain; packages with an
                # empty maintainer fall back to default_maintainer from repos.d
                pkg.add_maintainers(extract_maintainers(pkgdata.get('maintainer')))

                yield pkg
