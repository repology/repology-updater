# Copyright (C) 2018-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Dict, Iterable

from repology.logger import Logger
from repology.package import PackageFlags
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


def _iter_packages(path: str) -> Iterable[Dict[str, str]]:
    with open(path, 'r', encoding='utf-8') as jsonfile:
        for item in json.load(jsonfile)['results']['bindings']:
            yield {
                key: item[key]['value'] for key in item.keys()
            }


class WikidataJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        entries_good = 0
        entries_missed = 0

        for packagedata in _iter_packages(path):
            entity = packagedata['project'].rsplit('/', 1)[-1]  # this is URL, take only the ID from it

            pkg = factory.begin(entity)
            pkg.set_extra_field('entity', entity)

            pkg.set_name(packagedata['projectLabel'])
            pkg.set_summary(packagedata.get('projectDescription'))
            pkg.add_licenses(packagedata.get('licenses', '').split(', '))
            pkg.add_homepages(packagedata.get('websites', '').split(', '))

            names = set(packagedata['repology_projects'].split(', ')) if packagedata['repology_projects'] else set()

            if not names:
                pkg.log('entry has packages, but not Repology project name', severity=Logger.WARNING)
                entries_missed += 1
                continue
            elif len(names) > 1:
                pkg.log('multiple Repology project names: {}'.format(','.join(sorted(names))), severity=Logger.WARNING)

            entries_good += 1

            # generate a package for each version
            for version in sorted(packagedata['versions'].split(', ')):
                version, *flags = version.split('|')

                verpkg = pkg.clone()

                is_devel = 'U' in flags
                is_foreign_os_release = 'o' in flags and 'O' not in flags
                is_foreign_platform_release = 'p' in flags and 'P' not in flags

                if is_foreign_os_release:
                    verpkg.log('version {} skipped due to bad OS'.format(version), severity=Logger.NOTICE)
                    continue

                if is_foreign_platform_release:
                    verpkg.log('version {} skipped due to bad Platform'.format(version), severity=Logger.NOTICE)
                    continue

                verpkg.set_flags(PackageFlags.DEVEL, is_devel)
                verpkg.set_version(version)

                # generate package for each guessed name; it most cases, these will be merged anyway
                for name in names:
                    namepkg = verpkg.clone()
                    namepkg.set_basename(name)
                    yield namepkg

        factory.log('{} distinct projects accepted, {} potentially missing "Repology project name" property'.format(entries_good, entries_missed))
