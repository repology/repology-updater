# Copyright (C) 2018-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from repology.parsers.nevra import nevra_construct, nevra_parse
from repology.transformer import PackageTransformer


class SophieHTMLParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for item in lxml.html.parse(path).getroot().xpath('.//div[@id="rpms_list"]/ul/li/a'):
            nevra = nevra_parse(item.text)

            pkg = factory.begin()

            pkg.set_name(nevra[0])
            pkg.set_version(nevra[2])
            pkg.set_rawversion(nevra_construct(None, nevra[1], nevra[2], nevra[3]))

            yield pkg
