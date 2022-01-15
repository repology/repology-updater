# Copyright (C) 2018-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.xml import safe_findalltexts, safe_findtext


class OpenPkgRdfParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        root = xml.etree.ElementTree.parse(path)

        repository = root.find('{http://www.openpkg.org/xml-rdf-index/0.9}Repository')

        assert(repository is not None)

        for item in repository.findall('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description'):
            with factory.begin() as pkg:
                pkg.add_name(safe_findtext(item, '{http://www.openpkg.org/xml-rdf-index/0.9}Name'), NameType.SRCRPM_NAME)
                pkg.set_version(safe_findtext(item, '{http://www.openpkg.org/xml-rdf-index/0.9}Version'))
                pkg.add_licenses(item.findtext('{http://www.openpkg.org/xml-rdf-index/0.9}License'))
                pkg.set_summary(item.findtext('{http://www.openpkg.org/xml-rdf-index/0.9}Summary'))
                pkg.add_categories(item.findtext('{http://www.openpkg.org/xml-rdf-index/0.9}Group'))
                pkg.add_homepages(item.findtext('{http://www.openpkg.org/xml-rdf-index/0.9}URL'))

                for source in safe_findalltexts(item, './{http://www.openpkg.org/xml-rdf-index/0.9}Source/{http://www.w3.org/1999/02/22-rdf-syntax-ns#}bag/{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li'):
                    if (source.startswith('https://') or source.startswith('http://') or source.startswith('ftp://')) and 'openpkg.org' not in source:
                        pkg.add_downloads(source)

                release = safe_findtext(item, '{http://www.openpkg.org/xml-rdf-index/0.9}Release')
                if pkg.version.endswith(release):
                    pkg.set_flags(PackageFlags.UNTRUSTED)

                yield pkg
