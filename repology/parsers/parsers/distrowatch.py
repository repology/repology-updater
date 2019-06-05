# Copyright (C) 2017-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import lxml.html

from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


class DistrowatchPackagesParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for row in lxml.html.parse(path).getroot().xpath('.//table[@class="Auto"]')[0].xpath('./tr[position()>1]'):
            pkg = factory.begin()

            # name + version
            cell = row.xpath('./th[1]/a[@href]')[0]
            pkg.set_name(cell.text)
            pkg.add_homepages(cell.attrib['href'])

            # summary
            cell = row.xpath('./td[1]/a')[0]
            pkg.set_version(cell.text)
            pkg.add_downloads(cell.attrib['href'])

            # summary
            cell = row.xpath('./td[2]')[0]
            pkg.set_summary(cell.text)

            yield pkg
