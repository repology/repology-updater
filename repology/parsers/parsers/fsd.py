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

from typing import Iterable, List

from repology.package import PackageFlags
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.xml import XmlElement, iter_xml_elements_at_level
from repology.transformer import PackageTransformer


def _get_attrs(elt: XmlElement, path: str, attrname: str) -> List[str]:
    res = []

    for e in elt.findall(path):
        attr = e.get(attrname, None)
        if attr is not None:
            res.append(attr)

    return res


class FreeSoftwareDirectoryXMLParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        # All encounered version_status values:
        # alpha, beta, developmental, historical, mature, planning, rolling, stable, testing, unknown, unstable
        _unstable_versions = {'alpha', 'beta', 'developmental', 'planning', 'testing', 'unstable'}

        for entry in iter_xml_elements_at_level(path, 1, ['{http://semantic-mediawiki.org/swivt/1.0#}Subject']):
            label = entry.findtext('{http://www.w3.org/2000/01/rdf-schema#}label')
            with factory.begin(label) as pkg:
                name = entry.findtext('{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Name')
                version = entry.findtext('{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Version_identifier')

                if name is None or version is None:
                    continue

                if entry.findtext('{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Import_source') == 'Debian':  # 'Debian import' seems OK though
                    continue

                if entry.findtext('{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Decommissioned_or_Obsolete') == 'Yes':
                    continue

                version_status = entry.findtext('{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Version_status')

                if version_status in _unstable_versions:
                    pkg.set_flags(PackageFlags.DEVEL)
                elif version_status == 'rolling':
                    pkg.set_flags(PackageFlags.ROLLING)

                pkg.set_name(name)
                pkg.set_version(version)
                pkg.set_summary(entry.findtext('{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Short_description'))

                pkg.add_homepages(_get_attrs(entry, '{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Homepage_URL', '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'))
                pkg.add_downloads(_get_attrs(entry, '{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Version_download', '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'))

                pkg.set_extra_field('page', _get_attrs(entry, '{http://semantic-mediawiki.org/swivt/1.0#}page', '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')[0].split('/')[-1])

                yield pkg
