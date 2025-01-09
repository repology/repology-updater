# Copyright (C) 2016-2019,2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.versions import VersionStripper


class AURJsonParser(Parser):
    _maintainer_host: str

    def __init__(self, maintainer_host: str) -> None:
        self._maintainer_host = maintainer_host

    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right_greedy('-').strip_left(':').strip_right_greedy('+')

        for pkgdata in iter_json_list(path, (None,)):
            with factory.begin() as pkg:
                pkg.add_name(pkgdata['Name'], NameType.ARCH_NAME)

                pkg.set_version(pkgdata['Version'], normalize_version)
                pkg.set_summary(pkgdata['Description'])
                pkg.add_homepages(pkgdata['URL'])
                pkg.add_licenses(pkgdata.get('License'))

                if maintainer := pkgdata.get('Maintainer'):
                    pkg.add_maintainers(extract_maintainers(f'{maintainer}@{self._maintainer_host}'))

                if comaintainers := pkgdata.get('CoMaintainers'):
                    pkg.add_maintainers(extract_maintainers(f'{maintainer}@{self._maintainer_host}') for maintainer in comaintainers)

                if 'PackageBase' in pkgdata and pkgdata['PackageBase']:
                    pkg.add_name(pkgdata['PackageBase'], NameType.ARCH_BASENAME)

                # XXX: enable when we support multiple categories
                #if 'Keywords' in pkgdata and pkgdata['Keywords']:
                #    pkg.add_categories(pkgdata['Keywords'])

                yield pkg
