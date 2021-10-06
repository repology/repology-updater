# Copyright (C) 2019-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


class SalixPackagesJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for item in iter_json_list(path, ('packages', None)):
            with factory.begin() as pkg:
                pkg.add_name(item['name'], NameType.SALIX_NAME)
                pkg.set_version(item['ver'])
                pkg.set_summary(item['descs'])
                pkg.set_arch(item['arch'])

                # May be potentially useful for packagelinks, but not used now
                # as there's no way to generate package-specific link to
                # https://packages.salixos.org/#!
                #pkg.set_extra_field('location', item['loc'])

                yield pkg
