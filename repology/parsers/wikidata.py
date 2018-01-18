# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import sys


from repology.package import Package


def SimplifyResult(injson):
    for item in injson['results']['bindings']:
        yield {
            key: item[key]['value'] for key in item.keys()
        }


class WikidataJsonParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        jsondata = None
        with open(path, 'r', encoding='utf-8') as jsonfile:
            jsondata = json.load(jsonfile)

        for packagedata in SimplifyResult(jsondata):
            entity = packagedata['project'].rsplit('/', 1)[-1]  # this is URL, take only the ID from it

            # use Arch and AUR package names as a name, as they are most non-ambigous
            names = []
            for field in ['arch_packages', 'aur_packages']:
                if packagedata[field]:
                    names = packagedata[field].split(', ')
                    break

            # generate a package for each package name; these will be merged anyway
            for name in set(names):
                # generate a package for each version
                for version in packagedata['versions'].split(', '):
                    version, *flags = version.split('|')

                    is_devel = 'U' in flags
                    is_foreign_os_release = 'O' in flags and 'L' not in flags

                    if is_foreign_os_release:
                        print('WARNING: {} ({}) version {} skipped as non-linux release'.format(packagedata['projectLabel'], entity, version), file=sys.stderr)
                        continue

                    pkg = Package()

                    pkg.devel = is_devel

                    pkg.name = entity
                    pkg.effname = name
                    pkg.version = version

                    if 'projectDescription' in packagedata:
                        pkg.comment = packagedata['projectDescription']
                    else:
                        pkg.comment = packagedata['projectLabel']

                    if packagedata['licenses']:
                        pkg.licenses = packagedata['licenses'].split(', ')

                    if packagedata['websites']:
                        pkg.homepage = packagedata['websites'].split(', ')[0]  # XXX: use all websites when supported

                    result.append(pkg)

        return result
