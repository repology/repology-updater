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

from repology.logger import Logger
from repology.package import PackageFlags
from repology.parsers import Parser


def _iter_packages(path):
        with open(path, 'r', encoding='utf-8') as jsonfile:
            for item in json.load(jsonfile)['results']['bindings']:
                yield {
                    key: item[key]['value'] for key in item.keys()
                }


class WikidataJsonParser(Parser):
    def iter_parse(self, path, factory):
        for packagedata in _iter_packages(path):
            entity = packagedata['project'].rsplit('/', 1)[-1]  # this is URL, take only the ID from it

            pkg = factory.begin(entity)

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
                    is_foreign_os_release = 'o' in flags and 'O' not in flags
                    is_foreign_platform_release = 'p' in flags and 'P' not in flags

                    if is_foreign_os_release:
                        pkg.log('version {} skipped due to bad OS'.format(version), severity=Logger.WARNING)
                        continue

                    if is_foreign_platform_release:
                        pkg.log('version {} skipped due to bad Platform'.format(version), severity=Logger.WARNING)
                        continue

                    subpkg = pkg.clone()

                    subpkg.set_flags(PackageFlags.devel, is_devel)

                    subpkg.set_name(entity)
                    subpkg.set_effname(name)
                    subpkg.set_version(version)

                    if 'projectDescription' in packagedata:
                        subpkg.set_summary(packagedata['projectDescription'])
                    else:
                        subpkg.set_summary(packagedata['projectLabel'])

                    if packagedata['licenses']:
                        subpkg.add_licenses(packagedata['licenses'].split(', '))

                    if packagedata['websites']:
                        subpkg.add_homepages(packagedata['websites'].split(', '))

                    yield subpkg
