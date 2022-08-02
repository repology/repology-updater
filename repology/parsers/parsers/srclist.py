# Copyright (C) 2016-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Any, Iterable

import rpm

from repology.logger import Logger
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.nevra import nevra_construct
from repology.parsers.versions import parse_rpm_version, parse_rpm_vertags


class SrcListParser(Parser):
    _encoding: str
    _vertags: list[str]

    def __init__(self, encoding: str = 'utf-8', vertags: Any = None) -> None:
        self._encoding = encoding
        self._vertags = parse_rpm_vertags(vertags)

    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for header in rpm.readHeaderListFromFile(path):
            with factory.begin() as pkg:
                assert header.isSource()  # binary packages not supported yet

                def sanitize_key(key: Any) -> Any:
                    return rpm.tagnames[key].lower() if key in rpm.tagnames else key

                def sanitize_value(value: Any) -> Any:
                    return value.decode(self._encoding, errors='ignore') if isinstance(value, bytes) else value

                pkgdata = {
                    sanitize_key(key): sanitize_value(value) for key, value in dict(header).items()
                }

                # For Sisyphus (but not PCLinuxOS), there is pkgdata[1000011], which contains
                # a different name (for instance, for GLEW there is libGLEW-devel)
                # May use is for some other purposes

                pkg.add_name(pkgdata['name'], NameType.SRCRPM_NAME)

                if pkgdata['version'] is None:
                    raise RuntimeError('version not defined')

                version, flags = parse_rpm_version(self._vertags, pkgdata['version'], pkgdata['release'])
                pkg.set_version(version)
                pkg.set_rawversion(nevra_construct(None, header['epoch'], pkgdata['version'], pkgdata['release']))
                pkg.set_flags(flags)

                if 'packager' in pkgdata:
                    pkg.add_maintainers(extract_maintainers(pkgdata['packager']))  # XXX: may have multiple maintainers

                pkg.add_categories(pkgdata['group'])

                try:
                    # e.g. PCLinuxOS summaries may contain surrogate garbage
                    pkgdata['summary'].encode('utf-8')
                    pkg.set_summary(pkgdata['summary'])
                except:
                    pkg.log('incorrect UTF in summary', Logger.ERROR)

                pkg.set_arch(pkgdata['arch'])

                yield pkg
