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
import re
from typing import Iterable

import lxml.html

from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_list
from repology.transformer import PackageTransformer


def _normalize_version(version: str) -> str:
    match = re.match('(.*)-[0-9]+\\.[0-9a-f]{7,}$', version)
    if match:
        return match.group(1)
    return version


class GuixJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for pkgdata in iter_json_list(path, (None,)):
            with factory.begin() as pkg:
                pkg.set_name(pkgdata['name'])
                pkg.set_version(pkgdata['version'], _normalize_version)
                pkg.set_summary(pkgdata['synopsis'])
                if pkgdata.get('homepage'):  # may be boolean False
                    pkg.add_homepages(pkgdata['homepage'])
                yield pkg


# Legacy website parser, for reference purposes
class GuixWebsiteParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for filename in os.listdir(path):
            if not filename.endswith('.html'):
                continue

            root = None
            with open(os.path.join(path, filename), encoding='utf-8') as htmlfile:
                root = lxml.html.document_fromstring(htmlfile.read())

            for row in root.xpath('.//div[@class="package-preview"]'):
                pkg = factory.begin()

                # header
                cell = row.xpath('./h3[@class="package-name"]')[0]

                name, version = cell.text.split(None, 1)
                pkg.set_name(name)
                pkg.set_version(version, _normalize_version)

                pkg.set_summary(cell.xpath('./span[@class="package-synopsis"]')[0].text.strip().strip('—'))

                # details
                for cell in row.xpath('./ul[@class="package-info"]/li'):
                    key = cell.xpath('./b')[0].text

                    if key == 'License:':
                        pkg.add_licenses([a.text for a in cell.xpath('./a')])
                    elif key == 'Website:':
                        pkg.add_homepages(cell.xpath('./a')[0].attrib['href'])
                    elif key == 'Package source:':
                        pkg.set_extra_field('source', cell.xpath('./a')[0].text)

                yield pkg
