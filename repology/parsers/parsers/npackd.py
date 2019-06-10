# Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Dict, Iterable, List, Tuple

from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.xml import iter_xml_elements_at_level
from repology.transformer import PackageTransformer


_BLACKLISTED_CATEGORIES = set([
    'auto-create-versions',
    'end-of-life',
    'libs',
    'reupload',
    'same-url',
    'stable',
    'stable64',
    'unstable',
])


def _filter_categories(categories: Iterable[str]) -> Iterable[str]:
    yield from set(categories) - _BLACKLISTED_CATEGORIES


class NpackdXmlParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        licenses: Dict[str, str] = {}
        packages: Dict[str, Tuple[str, List[str], List[str]]] = {}

        for entry in iter_xml_elements_at_level(path, 1, ['license', 'package', 'version']):
            if entry.tag == 'license':
                licenses[entry.get('name')] = entry.findtext('title')
            elif entry.tag == 'package':
                packages[entry.get('name')] = (
                    entry.findtext('title'),
                    [e.text for e in entry.findall('license') if e.text],
                    [e.text for e in entry.findall('category') if e.text],
                )
            elif entry.tag == 'version':
                pkgname = entry.get('package')
                version = entry.get('name')

                with factory.begin(pkgname + ' ' + version) as pkg:
                    # XXX: there's discrepancy between naming schemes:
                    # - kdenlive (plain package name)
                    # - com.abisource.abiword (domain-based)
                    # - quazip-dev-i686-w64-dw2-posix-7.4-qt-5.12-static (plain, but broken if we try to split by dot)
                    # Because of that we can't normalize names, so we just define repos as shadow,
                    # hiding packages with insane naming schemes
                    pkg.set_name(pkgname)
                    pkg.set_version(version)

                    pkg.add_downloads((e.text for e in entry.findall('url')))

                    # from previously parsed <license> and <package> entries
                    pkg.set_summary(packages[pkgname][0])
                    pkg.add_licenses(licenses[l] for l in packages[pkgname][1])
                    pkg.add_categories(_filter_categories(packages[pkgname][2]))

                yield pkg
