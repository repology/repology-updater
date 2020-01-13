# Copyright (C) 2017-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


class KaOSHTMLParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for row in lxml.html.parse(path).getroot().xpath('.//table[@class="ctable"]')[0].xpath('./form/tr[position()>3 and position()<last()-3]'):
            pkg = factory.begin()

            name, version, revision = row.xpath('./td[1]/a')[0].text.rsplit('-', 2)

            # entries on kaosx.tk inconsistently have .pkg.tar.zst suffix, get rid of it
            revision = revision.split('.pkg.')[0]

            pkg.add_name(name, NameType.KAOS_NAME)
            pkg.set_version(version.split(':', 1)[-1])
            pkg.set_rawversion(version + '-' + revision)

            yield pkg
