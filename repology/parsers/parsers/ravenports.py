# Copyright (C) 2017-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import json

from repology.parsers import Parser


class RavenportsJsonParser(Parser):
    def iter_parse(self, path, factory, transformer):
        jsondata = None
        with open(path, 'r', encoding='utf-8') as jsonfile:
            jsondata = json.load(jsonfile)

        for packagedata in jsondata['ravenports']:
            pkg = factory.begin()

            pkg.set_name(packagedata['namebase'])
            pkg.set_version(packagedata['version'])
            pkg.add_categories(packagedata['keywords'])
            pkg.add_homepages(packagedata.get('homepage'))

            pkg.add_downloads(packagedata['distfile'])
            pkg.set_summary(packagedata['variants'][0]['sdesc'])
            pkg.add_maintainers(map(lambda contact: contact.get('email'), packagedata.get('contacts', [])))

            pkg.set_extra_field('bucket', packagedata['bucket'])
            pkg.set_extra_field('variant', packagedata['variants'][0]['label'])

            yield pkg
