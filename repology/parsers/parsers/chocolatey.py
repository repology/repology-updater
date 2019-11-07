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

import os
import xml.etree.ElementTree
from typing import Iterable

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


class ChocolateyParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for pagepath in os.listdir(path):
            if not pagepath.endswith('.xml'):
                continue

            root = xml.etree.ElementTree.parse(os.path.join(path, pagepath))

            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                pkg = factory.begin()

                pkg.add_name(entry.find('{http://www.w3.org/2005/Atom}title').text, NameType.GENERIC_PKGNAME)  # type: ignore
                pkg.set_version(entry.find('{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties/{http://schemas.microsoft.com/ado/2007/08/dataservices}Version').text)  # type: ignore
                pkg.add_homepages(entry.find('{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties/{http://schemas.microsoft.com/ado/2007/08/dataservices}ProjectUrl').text)  # type: ignore

                commentnode = entry.find('{http://www.w3.org/2005/Atom}summary')
                if commentnode is not None:
                    pkg.set_summary(commentnode.text)

                yield pkg
