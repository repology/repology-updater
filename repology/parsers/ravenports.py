# Copyright (C) 2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


from repology.package import Package


class RavenportsJsonParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        jsondata = None
        with open(path, 'r', encoding='utf-8') as jsonfile:
            jsondata = json.load(jsonfile)

        for packagedata in jsondata['ravenports']:
            pkg = Package()

            pkg.name = packagedata['namebase']
            pkg.version = packagedata['version']
            pkg.category = packagedata['keywords'][0]
            if 'homepage' in packagedata:
                pkg.homepage = packagedata['homepage']

            pkg.downloads = packagedata['distfile']
            pkg.comment = packagedata['variants'][0]['sdesc']

            pkg.extrafields['bucket'] = packagedata['bucket']
            pkg.extrafields['variant'] = packagedata['variants'][0]['label']

            result.append(pkg)

        return result
