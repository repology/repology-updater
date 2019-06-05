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

import re
from typing import Iterable

from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


class CRANCheckSummaryParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        with open(path, 'r', encoding='utf-8') as htmlfile:
            for nline, line in enumerate(htmlfile, 1):
                match = re.search('<tr> <td> <a href="[^"]+">([^<>]+)</a> </td> <td>[ ]*([^ <>]+)[ ]*</td>', line)
                if match:
                    pkg = factory.begin('line {}'.format(nline))

                    pkg.set_name(match[1])
                    pkg.set_version(match[2])
                    pkg.add_homepages('https://cran.r-project.org/web/packages/{}/index.html'.format(match[1]))

                    yield pkg
