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

from typing import Iterable

import rpm

from repology.packagemaker import NameType, PackageFactory, PackageMaker
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
                assert(header.isSource())  # binary packages not supported yet

                pkgdata = {
                    rpm.tagnames[key].lower() if key in rpm.tagnames else key:
                    value.decode(self.encoding, errors='ignore') if isinstance(value, bytes) else value
                    for key, value in dict(header).items()
                }

                # For Sisyphus (but not PCLinuxOS), there is pkgdata[1000011], which contains
                # a different name (for instance, for GLEW there is libGLEW-devel)
                # May use is for some other purposes

                pkg.add_name(pkgdata['name'], NameType.SRCRPM_NAME)
                pkg.set_version(pkgdata['version'])  # XXX: handle release

                if pkgdata['version'] is None:
                    raise RuntimeError('version not defined')

                pkg.set_rawversion(nevra_construct(None, header['epoch'], pkgdata['version'], pkgdata['release']))

                if 'packager' in pkgdata:
                    pkg.add_maintainers(extract_maintainers(pkgdata['packager']))  # XXX: may have multiple maintainers

                pkg.add_categories(pkgdata['group'])
                pkg.set_summary(pkgdata['summary'])
                pkg.set_arch(pkgdata['arch'])

                yield pkg
