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

from typing import Iterable

from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.xml import iter_xml_elements_at_level
from repology.transformer import PackageTransformer


def _expand_multiline_licenses(text: str) -> Iterable[str]:
    return (license.lstrip('- ') for license in text.split('\n'))


class SolusIndexParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for entry in iter_xml_elements_at_level(path, 1, ['Package']):
            with factory.begin() as pkg:
                pkg.set_name(entry.findtext('Name'))
                pkg.set_summary(entry.findtext('Summary'))
                pkg.add_licenses((_expand_multiline_licenses(elt.text) for elt in entry.findall('License') if elt.text))
                pkg.add_categories((elt.text for elt in entry.findall('PartOf')))

                for update in entry.findall('./History/Update'):
                    pkg.set_version(update.findtext('Version'))
                    break

                pkg.set_basename(entry.findtext('./Source/Name'))
                pkg.add_maintainers(entry.findtext('./Source/Packager/Email'))

                yield pkg
