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

import re
import xml.etree.ElementTree
from typing import Iterable

from repology.package import PackageFlags
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.nevra import nevra_construct, nevra_parse
from repology.transformer import PackageTransformer


class RosaInfoXmlParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        root = xml.etree.ElementTree.parse(path)

        for info in root.findall('./info'):
            with factory.begin() as pkg:
                name, epoch, version, release, arch = nevra_parse(info.attrib['fn'])

                pkg.set_name(name)
                pkg.set_version(version)
                pkg.set_rawversion(nevra_construct(None, epoch, version, release))
                pkg.set_arch(arch)

                # What we do here is we try to extract prerelease part
                # and mark version as ignored with non-trivial ROSAREV,
                # as it it likely a snapshot and trus cannot be trusted
                if not version.isdecimal():
                    pkg.set_flags(PackageFlags.IGNORE)
                    match = re.search('\\b(a|alpha|b|beta|pre|rc)[0-9]+', version.lower())
                    if match:
                        pkg._package.version += match.group(0)  # XXX: encapsulation violation

                pkg.add_homepages(info.attrib['url'])
                pkg.add_licenses(info.attrib['license'])

                yield pkg
