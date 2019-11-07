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

# flake8: noqa

import xml.etree.ElementTree
from typing import Iterable

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.walk import walk_tree
from repology.transformer import PackageTransformer


class NSTPkgInfoXMLParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for filename in walk_tree(path, suffix='pkginfo.xml'):
            root = xml.etree.ElementTree.parse(filename)
            # XXX: fails on unknown entity NST_RELEASE_SUFFIX
            # and dtd is not usable as it needs preprocessing

        yield from []
