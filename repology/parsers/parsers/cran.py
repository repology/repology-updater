# Copyright (C) 2017-2019, 2021, 2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser


class CRANCheckSummaryParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        with open(path, 'r', encoding='utf-8') as htmlfile:
            for nline, line in enumerate(htmlfile, 1):
                if not (match := re.search('<tr> <td> <a href="[^"]+"><span class="CRAN">([^<>]+)</span></a> </td> <td>[ ]*([^ <>]+)[ ]*</td>', line)):
                    continue

                with factory.begin(f'line {nline}') as pkg:
                    pkg.add_name(match[1], NameType.CRAN_NAME)
                    pkg.set_version(match[2])

                    yield pkg
