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
from functools import cmp_to_key
from typing import Iterable

from libversion import version_compare

from repology.logger import Logger
from repology.package import LinkType, PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


def _iter_packages(path: str) -> Iterable[dict[str, str]]:
    with open(path, 'r', encoding='utf-8') as jsonfile:
        for item in json.load(jsonfile)['results']['bindings']:
            yield {
                key: item[key]['value'] for key in item.keys()
            }


class WikidataJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        total_entries = 0

        for packagedata in _iter_packages(path):
            entity = packagedata['project'].rsplit('/', 1)[-1]  # this is URL, take only the ID from it
            label = packagedata['projectLabel']

            with factory.begin('{} ({})'.format(entity, label)) as pkg:
                pkg.add_name(entity, NameType.WIKIDATA_ENTITY)
                pkg.add_name(label, NameType.WIKIDATA_LABEL)
                pkg.set_summary(packagedata.get('projectDescription'))
                pkg.add_licenses(sorted(packagedata.get('licenses', '').split('␞')))
                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, sorted(packagedata.get('websites', '').split('␞')))
                pkg.add_links(LinkType.UPSTREAM_REPOSITORY, sorted(packagedata.get('repositories', '').split('␞')))

                names = sorted(packagedata['repology_projects'].split('␞'))

                if len(names) > 1:
                    pkg.log('multiple Repology project names: {}'.format(','.join(names)), severity=Logger.WARNING)

                total_entries += 1

                pkgs_preferred = []
                pkgs_normal = []

                # generate a package for each version
                for version in sorted(packagedata['versions'].split('␞')):
                    version, *flags = version.split('|')

                    verpkg = pkg.clone()

                    is_version_stable = 'S' in flags
                    is_version_unstable = 'U' in flags
                    is_version_bad = 'X' in flags
                    is_foreign_os_release = 'o' in flags and 'O' not in flags
                    is_foreign_platform_release = 'p' in flags and 'P' not in flags
                    is_preferred = 'R' in flags

                    if is_foreign_os_release:
                        verpkg.log('version {} skipped due to bad OS'.format(version), severity=Logger.NOTICE)
                        continue

                    if is_foreign_platform_release:
                        verpkg.log('version {} skipped due to bad Platform'.format(version), severity=Logger.NOTICE)
                        continue

                    if is_version_bad:
                        verpkg.log('version {} skipped due to bad Version Type'.format(version), severity=Logger.ERROR)
                        continue

                    verpkg.set_flags(PackageFlags.DEVEL, is_version_unstable and not is_version_stable)
                    verpkg.set_version(version)
                    pkg.add_links(LinkType.UPSTREAM_DOWNLOAD, sorted(flag for flag in flags if len(flag) > 1))

                    # generate package for each repology project
                    for name in names:
                        namepkg = verpkg.clone()
                        namepkg.add_name(name, NameType.WIKIDATA_REPOLOGY_PROJECT_NAME)
                        if is_preferred:
                            pkgs_preferred.append(namepkg)
                        else:
                            pkgs_normal.append(namepkg)

                if pkgs_preferred:
                    # temporary diagnostics until Wikidata usage in Wikipedia gains more momentum
                    # before that, we can/have to help keeping it up to date
                    max_preferred_version = max((pkg.version for pkg in pkgs_preferred), key=cmp_to_key(version_compare))
                    max_normal_version = max((pkg.version for pkg in pkgs_normal if not pkg.flags & PackageFlags.DEVEL), key=cmp_to_key(version_compare), default=None)
                    max_devel_version = max((pkg.version for pkg in pkgs_normal if pkg.flags & PackageFlags.DEVEL), key=cmp_to_key(version_compare), default=None)

                    if max_normal_version and version_compare(max_preferred_version, max_normal_version) < 0:
                        pkg.log('preferred version {} < normal {} (may need rank update)'.format(max_preferred_version, max_normal_version), severity=Logger.WARNING)

                    if max_devel_version and version_compare(max_devel_version, max_preferred_version) > 0:
                        pkg.log('devel version {} < preferred {} (may need preferred rank for devel version)'.format(max_devel_version, max_preferred_version), severity=Logger.WARNING)

                    yield from pkgs_preferred
                else:
                    num_devel = 0
                    num_stable = 0
                    for pkg in pkgs_normal:
                        if pkg.flags & PackageFlags.DEVEL:
                            num_devel += 1
                        else:
                            num_stable += 1

                    if num_devel > len(names):
                        pkg.log('no preferred devel version(s) set (out of {})'.format(num_devel // len(names)), severity=Logger.WARNING)

                    if num_stable > len(names):
                        pkg.log('no preferred stable version(s) set (out of {})'.format(num_stable // len(names)), severity=Logger.WARNING)

                    yield from pkgs_normal

        factory.log('{} total entries'.format(total_entries))
