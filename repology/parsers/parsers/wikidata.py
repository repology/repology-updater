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


_DONOR_REPOS = [
    ('arch_packages', 'arch'),
    ('aur_packages', 'aur'),
]


def _iter_packages(path: str) -> Iterable[Dict[str, str]]:
    with open(path, 'r', encoding='utf-8') as jsonfile:
        for item in json.load(jsonfile)['results']['bindings']:
            yield {
                key: item[key]['value'] for key in item.keys()
            }


class WikidataJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        entries_total = 0
        entries_with_packages = 0
        entries_with_repology_project = 0

        for packagedata in _iter_packages(path):
            entity = packagedata['project'].rsplit('/', 1)[-1]  # this is URL, take only the ID from it

            pkg = factory.begin(entity)
            pkg.set_extra_field('entity', entity)

            pkg.set_name(packagedata['projectLabel'])
            pkg.set_summary(packagedata.get('projectDescription'))
            pkg.add_licenses(packagedata.get('licenses', '').split(', '))
            pkg.add_homepages(packagedata.get('websites', '').split(', '))

            # there's ongoing effort to fill native repology project names in wikidata,
            # for now just check these and gather some statistics
            repology_names = set()
            if packagedata['repology_projects']:
                repology_names.update(packagedata['repology_projects'].split(', '))

            entries_total += 1
            if repology_names:
                entries_with_repology_project += 1
                if len(repology_names) > 1:
                    pkg.log('multiple Repology project names: {}'.format(','.join(repology_names)), severity=Logger.WARNING)

            # but we still use arch/aur package information
            # we have to run it through Transformer when version is defined later
            donor_repo = None

            for fieldname, fakerepo in _DONOR_REPOS:
                if packagedata[fieldname]:
                    donor_repo = fakerepo
                    donor_names = set(packagedata[fieldname].split(', '))
                    break

            if not donor_repo:
                continue

            entries_with_packages += 1

            # generate a package for each version
            for version in sorted(packagedata['versions'].split(', ')):
                version, *flags = version.split('|')

                verpkg = pkg.clone(append_ident=' ' + version)

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

                # extract project name(s) from packages information
                names = set()
                for name in donor_names:
                    fakepkgmaker = verpkg.clone()
                    fakepkgmaker.set_name(name)
                    fakepkg = fakepkgmaker.unwrap()
                    fakepkg.repo = donor_repo
                    transformer.process(fakepkg)
                    names.add(fakepkg.effname)

                if len(names) > 1:
                    verpkg.log('multiple project names extracted from {}: {}'.format(donor_repo, ','.join(names)), severity=Logger.WARNING)

                # generate package for each guessed name; it most cases, these will be merged anyway
                for name in names:
                    namepkg = verpkg.clone()
                    namepkg.set_basename(name)
                    yield namepkg

        factory.log('Entries total: {}'.format(entries_total))
        factory.log('Entries with packages: {}'.format(entries_with_packages))
        factory.log('Entries with Repology project name filled: {}'.format(entries_with_repology_project))
