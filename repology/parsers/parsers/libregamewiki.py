# Copyright (C) 2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.package import Package


class LibreGameWikiParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        root = xml.etree.ElementTree.parse(path)

        content = root.find('.//div[@id="mw-content-text"]')

        for item in content.findall('./div[@style="float:left; width:25.3em; height:8.5em; border:1px solid #ccc; padding:0.1em; margin-bottom: 2em; margin-right: 1em; overflow:hidden"]'):
            pkg = Package()

            # name
            cell = item.find('./p[1]/b[1]/a[1]')

            if cell is None or not cell.text:
                continue

            pkg.name = cell.text

            # version
            cell = item.find('./p[2]')
            if cell is None or not cell.text:
                continue

            pkg.version = cell.text

            match = re.match('(.*) \(.*\)$', pkg.version)
            if match:
                pkg.origversion = pkg.version
                pkg.version = match.group(1)

            # www
            for a in item.findall('./p[2]/a'):
                if a.text == 'Website':
                    pkg.homepage = a.attrib['href']

            # category
            pkg.category = 'games'

            result.append(pkg)

        return result
