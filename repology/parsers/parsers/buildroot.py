# Copyright (C) 2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


class BuildrootJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for pkgname, pkgdata in iter_json_dict(path, ('packages', None)):
            with factory.begin(pkgname) as pkg:
                if not pkgdata['current_version']:
                    pkg.log('no version', Logger.ERROR)
                    continue

                pkg.add_name(pkgname, NameType.BUILDROOT_NAME)
                pkg.set_version(pkgdata['current_version'])
                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, pkgdata['url'])
                pkg.add_licenses(pkgdata['license'])
                pkg.set_extra_field('path', pkgdata['path'])

                if cpeid := pkgdata['cpeid']:
                    cpe_components = cpeid.split(':')
                    pkg.add_cpe(cpe_components[3], cpe_components[4])

                pkg.set_extra_field('pkg_path', pkgdata['pkg_path'])
                if patch_files := pkgdata['patch_files']:
                    pkg.set_extra_field('patch', patch_files)

                yield pkg
