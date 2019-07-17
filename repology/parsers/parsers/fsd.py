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

import re
from typing import Iterable, List

from repology.package import PackageFlags
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.xml import XmlElement, iter_xml_elements_at_level, safe_findtext
from repology.transformer import PackageTransformer


def _get_attrs(elt: XmlElement, path: str, attrname: str) -> List[str]:
    res = []

    for e in elt.findall(path):
        attr = e.get(attrname, None)
        if attr is not None:
            res.append(attr)

    return res


def _unescape(s: str) -> str:
    return re.sub(b'-([0-9A-F]{2})', lambda m: bytes([int(m.group(1), 16)]), s.encode('ascii')).decode('utf-8')


class FreeSoftwareDirectoryXMLParser(Parser):
    _high_priority: bool

    def __init__(self, high_priority: bool = False) -> None:
        self._high_priority = high_priority

    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        # All encounered version_status values:
        # alpha, beta, developmental, historical, mature, planning, rolling, stable, testing, unknown, unstable
        _unstable_versions = {'alpha', 'beta', 'developmental', 'planning', 'testing', 'unstable'}

        num_total = 0
        num_nover = 0
        num_noneng = 0
        num_debian = 0
        num_obsolete = 0

        num_accepted = 0
        num_devel = 0

        for entry in iter_xml_elements_at_level(path, 1, ['{http://semantic-mediawiki.org/swivt/1.0#}Subject']):
            pages = _get_attrs(entry, '{http://semantic-mediawiki.org/swivt/1.0#}page', '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
            if not pages:
                continue

            page = _unescape(pages[0].split('/')[-1])

            with factory.begin(page) as pkg:
                label = safe_findtext(entry, '{http://www.w3.org/2000/01/rdf-schema#}label')
                name = safe_findtext(entry, '{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Name')
                version = entry.findtext('{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Version_identifier')

                num_total += 1

                if version is None:
                    num_nover += 1
                    continue

                if entry.findtext('{http://semantic-mediawiki.org/swivt/1.0#}wikiPageContentLanguage') != 'en':
                    num_noneng += 1
                    continue

                if entry.findtext('{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Import_source') == 'Debian':  # 'Debian import' seems OK though
                    num_debian += 1
                    continue

                if entry.findtext('{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Decommissioned_or_Obsolete') == 'Yes':
                    num_obsolete += 1
                    continue

                if self._high_priority and entry.findtext('{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Is_High_Priority_Project') != 'true':
                    continue

                version_status = entry.findtext('{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Version_status')

                if version_status in _unstable_versions:
                    num_devel += 1
                    pkg.set_flags(PackageFlags.DEVEL)
                elif version_status == 'rolling':
                    pkg.set_flags(PackageFlags.ROLLING)

                num_accepted += 1

                pkg.set_name(page)
                pkg.set_version(version)
                pkg.set_summary(entry.findtext('{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Short_description'))

                pkg.add_homepages(_get_attrs(entry, '{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Homepage_URL', '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'))
                pkg.add_downloads(_get_attrs(entry, '{http://directory.fsf.org/wiki/Special:URIResolver/Property-3A}Version_download', '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'))

                pkg.set_extra_field('page', page)
                pkg.set_extra_field('name', name)
                pkg.set_extra_field('label', label)

                yield pkg

        factory.log('Total software entries (with Name and Version): {}'.format(num_total))
        factory.log('Dropped entries with no version defined: {}'.format(num_nover))
        factory.log('Dropped non-english pages: {}'.format(num_noneng))
        factory.log('Dropped entries marked as Import_source=Debian: {}'.format(num_debian))
        factory.log('Dropped entries marked as Decommissioned_or_Obsolete: {}'.format(num_obsolete))
        factory.log('Accepted entries: {} ({} unstable)'.format(num_accepted, num_devel))
