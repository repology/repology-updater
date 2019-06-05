# Copyright (C) 2017 Steve Wills <steve@mouf.net>
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

from typing import Iterable, Union

import rubymarshal.reader

from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


def _force_decode(var: Union[str, bytes]) -> str:
    if isinstance(var, str):
        return var
    else:
        return str(var, 'UTF-8')


class RubyGemParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        with open(path, 'rb') as fd:
            for gem in rubymarshal.reader.load(fd):
                pkg = factory.begin()

                pkg.set_name(_force_decode(gem[0]))

                if _force_decode(gem[2]) != 'ruby':
                    pkg.log('skipped, gemplat != ruby')
                    continue

                pkg.set_version(_force_decode(gem[1].values[0]))
                pkg.add_homepages('https://rubygems.org/gems/' + pkg.name)

                yield pkg
