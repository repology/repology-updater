# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import re
import xml.etree.ElementTree

from repology.package import Package


def SanitizeVersion(version):
    origversion = version

    match = re.match('(.*)-[0-9]+\\.[0-9a-f]{7,}$', origversion)
    if match:
        version = match.group(1)

    if version != origversion:
        return version, origversion
    else:
        return version, None


class GuixParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        for filename in os.listdir(path):
            if not filename.endswith('.html'):
                continue

            root = xml.etree.ElementTree.parse(os.path.join(path, filename))

            table = root.find('.//table[@id="packages"]')

            first = True
            for row in table.findall('tr'):
                if first:
                    first = False
                    continue

                pkg = Package()

                # name + version
                cell = row.find('./td[2]/a')
                pkg.name, version = cell.text.split(' ', 1)
                pkg.version, pkg.origversion = SanitizeVersion(version)

                # summary
                cell = row.find('./td[3]/span')
                pkg.comment = cell.text

                # licenses
                for cell in row.findall('./td[3]/div[1]/div[2]/a[@title="Link to the full license"]'):
                    pkg.licenses.append(cell.text)

                # www
                cell = row.find('./td[3]/div[1]/a[@title="Link to the package\'s website"]')
                pkg.homepage = cell.attrib['href']

                result.append(pkg)

        return result
