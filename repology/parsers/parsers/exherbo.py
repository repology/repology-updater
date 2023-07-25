# Copyright (C) 2016-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import re
from typing import Iterable

from repology.package import LinkType
from repology.package import PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_list


def _normalize_version(version: str) -> str:
    return re.sub('-r[0-9]+$', '', version)


class ExherboJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for packagedata in iter_json_list(path, (None,)):
            with factory.begin() as pkg:
                pkg.add_name(packagedata['name'], NameType.EXHERBO_NAME)
                pkg.add_name(packagedata['category'] + '/' + packagedata['name'], NameType.EXHERBO_FULL_NAME)
                pkg.set_version(packagedata['version'], _normalize_version)
                pkg.add_categories(packagedata['category'])
                pkg.add_homepages(packagedata['homepage'].split())
                pkg.add_downloads(packagedata['downloads'].split())
                pkg.set_subrepo(packagedata['repository'])
                pkg.set_summary(packagedata['summary'])
                pkg.add_links(LinkType.PACKAGE_RECIPE, packagedata['exheres_url'])
                pkg.add_links(LinkType.PACKAGE_RECIPE_RAW, packagedata['exheres_url_raw'])

                if pkg.version == 'scm' or pkg.version.endswith('-scm'):  # XXX: to rules?
                    pkg.set_flags(PackageFlags.ROLLING)

                yield pkg
