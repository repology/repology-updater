# Copyright (C) 2021 Danil Shein <dshein@altlinux.org>
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

from typing import Any, Iterable

from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_list
from repology.parsers.nevra import nevra_construct
from repology.parsers.versions import parse_rpm_version, parse_rpm_vertags


class SisyphusJsonParser(Parser):
    _vertags: list[str]

    def __init__(self, vertags: Any = None) -> None:
        self._vertags = parse_rpm_vertags(vertags)

    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for packagedata in iter_json_list(path, ('packages', None)):
            with factory.begin() as pkg:
                pkg.add_name(packagedata['name'], NameType.SRCRPM_NAME)
                pkg.add_binnames(binary['name'] for binary in packagedata['binaries'])

                version, flags = parse_rpm_version(self._vertags, packagedata['version'], packagedata['release'])
                pkg.set_version(version)
                pkg.set_rawversion(nevra_construct(None, packagedata['epoch'], packagedata['version'], packagedata['release']))
                pkg.set_flags(flags)

                pkg.add_categories(packagedata['category'])
                pkg.set_summary(packagedata['summary'])
                pkg.add_licenses(packagedata['license'])
                pkg.add_maintainers(packagedata['packager'])

                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, packagedata['url'])
                pkg.add_links(LinkType.PACKAGE_HOMEPAGE, packagedata['homepage'])
                pkg.add_links(LinkType.PACKAGE_RECIPE, packagedata['recipe'])
                pkg.add_links(LinkType.PACKAGE_RECIPE_RAW, packagedata['recipe_raw'])
                pkg.add_links(LinkType.PACKAGE_ISSUE_TRACKER, packagedata['bugzilla'])

                # TODO: parse CPE data when available
                if 'CPE' in packagedata:
                    pass

                yield pkg
