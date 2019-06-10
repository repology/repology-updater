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

import xml.etree.ElementTree
from typing import Iterable

from repology.package import PackageFlags
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


class OpenPkgRdfParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        root = xml.etree.ElementTree.parse(path)

        repository = root.find('{http://www.openpkg.org/xml-rdf-index/0.9}Repository')

        for item in repository.findall('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description'):  # type: ignore
            pkg = factory.begin()

            pkg.set_name(item.find('{http://www.openpkg.org/xml-rdf-index/0.9}Name').text)  # type: ignore
            pkg.set_version(item.find('{http://www.openpkg.org/xml-rdf-index/0.9}Version').text)  # type: ignore
            pkg.add_licenses(item.find('{http://www.openpkg.org/xml-rdf-index/0.9}License').text)  # type: ignore
            pkg.set_summary(item.find('{http://www.openpkg.org/xml-rdf-index/0.9}Summary').text)  # type: ignore
            pkg.add_categories(item.find('{http://www.openpkg.org/xml-rdf-index/0.9}Group').text)  # type: ignore
            pkg.add_homepages(item.find('{http://www.openpkg.org/xml-rdf-index/0.9}URL').text)  # type: ignore

            for source in item.findall('./{http://www.openpkg.org/xml-rdf-index/0.9}Source/{http://www.w3.org/1999/02/22-rdf-syntax-ns#}bag/{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li'):
                text = source.text
                if (text.startswith('https://') or text.startswith('http://') or text.startswith('ftp://')) and 'openpkg.org' not in text:  # type: ignore
                    pkg.add_downloads(text)

            release = item.find('{http://www.openpkg.org/xml-rdf-index/0.9}Release').text  # type: ignore
            if pkg.version.endswith(release):
                pkg.set_flags(PackageFlags.UNTRUSTED)

            yield pkg
