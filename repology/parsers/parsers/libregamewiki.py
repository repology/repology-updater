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
import xml.etree.ElementTree
from typing import Iterable
from urllib.parse import unquote

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser


class LibreGameWikiParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        root = xml.etree.ElementTree.parse(path)

        content = root.find('.//div[@id="mw-content-text"]')
        if content is None:
            raise RuntimeError('Cannot find <div id="mw-content-text"> element')

        for item in content.findall('.//div[@style="float:left; width:25.3em; height:8.5em; border:1px solid #ccc; padding:0.1em; margin-bottom: 2em; margin-right: 1em; overflow:hidden"]'):
            pkg = factory.begin()

            # name
            cell = item.find('./p[1]/b[1]/a[1]')

            if cell is None or not cell.text:
                continue

            pkg.add_name(cell.text, NameType.WIKI_TITLE)
            pkg.add_name(unquote(cell.attrib['href'].rsplit('/', 1)[-1]), NameType.WIKI_PAGE)

            # version
            cell = item.find('./p[2]')
            if cell is None or not cell.text:
                continue

            version = cell.text

            match = re.match('(.*) \\(.*\\)$', version)
            if match:
                pkg.set_version(match.group(1))
                pkg.set_rawversion(version)
            else:
                pkg.set_version(version)

            # www
            for a in item.findall('./p[2]/a'):
                if a.text == 'Website':
                    pkg.add_homepages(a.attrib['href'])

            # category
            pkg.add_categories('games')

            yield pkg
