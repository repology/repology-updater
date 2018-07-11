# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import lxml.html

from repology.package import Package
from repology.parsers import Parser


def SanitizeVersion(version):
    origversion = version

    match = re.match('(.*)-[0-9]+\\.[0-9a-f]{7,}$', origversion)
    if match:
        version = match.group(1)

    if version != origversion:
        return version, origversion
    else:
        return version, None


class GuixParser(Parser):
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        for filename in os.listdir(path):
            if not filename.endswith('.html'):
                continue

            root = None
            with open(os.path.join(path, filename), encoding='utf-8') as htmlfile:
                root = lxml.html.document_fromstring(htmlfile.read())

            for row in root.xpath('.//div[@class="package-preview"]'):
                pkg = Package()

                # header
                cell = row.xpath('./h3[@class="package-name"]')[0]
                pkg.name, version = cell.text.split(' ', 1)
                pkg.version, pkg.origversion = SanitizeVersion(version.strip())
                pkg.comment = cell.xpath('./span[@class="package-synopsis"]')[0].text.strip().strip('—').strip() or None

                # details
                for cell in row.xpath('./ul[@class="package-info"]/li'):
                    key = cell.xpath('./b')[0].text

                    if key == 'License:':
                        pkg.licenses = [a.text for a in cell.xpath('./a')]
                    elif key == 'Website:':
                        pkg.homepage = cell.xpath('./a')[0].attrib['href']
                    elif key == 'Package source:':
                        pkg.extrafields['source'] = cell.xpath('./a')[0].text

                result.append(pkg)

        return result
