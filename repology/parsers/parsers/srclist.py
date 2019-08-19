# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import rpm

from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.nevra import nevra_construct
from repology.transformer import PackageTransformer


class SrcListParser(Parser):
    def __init__(self, encoding: str = 'utf-8') -> None:
        self.encoding = encoding

    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for header in rpm.readHeaderListFromFile(path):
            with factory.begin() as pkg:
                fields = {
                    key: str(header[key], self.encoding) if header[key] is not None else None
                    for key in ['name', 'version', 'release', 'packager', 'group', 'summary', 'arch']
                }

                pkg.set_name(fields['name'])
                pkg.set_version(fields['version'])  # XXX: handle release

                if fields['version'] is None:
                    raise RuntimeError('version not defined')

                pkg.set_rawversion(nevra_construct(None, header['epoch'], fields['version'], fields['release']))

                if fields['packager']:
                    pkg.add_maintainers(extract_maintainers(fields['packager']))  # XXX: may have multiple maintainers

                pkg.add_categories(fields['group'])
                pkg.set_summary(fields['summary'])
                pkg.set_arch(fields['arch'])

                yield pkg
