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

import xml.etree.ElementTree

from repology.parsers import Parser


def _iter_package_entries(path):
    """Return all <Package> elements from XML.

    The purpose is to clear the element after processing, so
    processed elements don't fill up the memory
    """
    for _, elem in xml.etree.ElementTree.iterparse(path):
        if elem.tag == 'Package':
            yield elem
            elem.clear()


def _expand_multiline_licenses(text):
    return (license.lstrip('- ') for license in text.split('\n'))


class SolusIndexParser(Parser):
    def iter_parse(self, path, factory, transformer):
        for entry in _iter_package_entries(path):
            with factory.begin() as pkg:
                namenode = entry.find('./Name')

                if namenode is None:
                    continue

                pkg.set_name(namenode.text)
                pkg.set_summary(entry.find('Summary').text)
                pkg.add_licenses((_expand_multiline_licenses(elt.text) for elt in entry.findall('License')))
                pkg.add_categories((elt.text for elt in entry.findall('PartOf')))

                for update in entry.find('History').findall('Update'):
                    pkg.set_version(update.find('Version').text)
                    break

                pkg.set_basename(entry.find('Source').find('Name').text)
                pkg.add_maintainers(entry.find('Source').find('Packager').find('Email').text)

                yield pkg
