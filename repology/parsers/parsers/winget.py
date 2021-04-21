# Copyright (C) 2020-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import os
from dataclasses import dataclass
from typing import Iterable

import yaml

from repology.logger import Logger
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.walk import walk_tree
from repology.transformer import PackageTransformer


@dataclass
class _PackageLocation:
    yamlpath_abs: str
    yamlpath_rel: str
    relevant_path: str


def _iter_packages(path: str) -> Iterable[_PackageLocation]:
    for yamlpath_abs in walk_tree(os.path.join(path, 'manifests'), suffix='.yaml'):
        yamlpath_rel = os.path.relpath(yamlpath_abs, path)

        yield _PackageLocation(
            yamlpath_abs=yamlpath_abs,
            yamlpath_rel=yamlpath_rel,
            # skip manifests/ at left
            # skip version directory and yaml filename at right
            relevant_path='/'.join(yamlpath_rel.split('/')[1:-2]),
        )


class WingetGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for pkgloc in _iter_packages(path):
            with factory.begin(pkgloc.yamlpath_rel) as pkg:
                try:
                    with open(pkgloc.yamlpath_abs, 'r') as fd:
                        pkgdata = yaml.safe_load(fd)
                except UnicodeDecodeError:
                    pkg.log('Cannot read file, probably UTF-16 garbage', Logger.ERROR)
                    continue
                except yaml.MarkedYAMLError as e:
                    pkg.log(f'YAML error at line {e.problem_mark.line}: {e.problem}', Logger.ERROR)
                    continue

                if 'PackageName' not in pkgdata:
                    pkg.log('No PackageName defined', Logger.ERROR)
                    continue

                pkg.add_name(pkgdata['PackageIdentifier'], NameType.WINGET_ID)
                pkg.add_name(pkgdata['PackageIdentifier'].split('.', 1)[-1], NameType.WINGET_ID_NAME)
                pkg.add_name(pkgdata['PackageName'], NameType.WINGET_NAME)
                pkg.add_name(pkgloc.relevant_path, NameType.WINGET_PATH)
                # Moniker field is optional and mosty useless

                version = pkgdata['PackageVersion']
                if isinstance(version, float):
                    pkg.log(f'PackageVersion "{version}" is a floating point, should be quoted in YAML', Logger.WARNING)

                pkg.set_version(str(version))
                pkg.add_homepages(pkgdata.get('PackageUrl'))

                # pkg.set_summary(pkgdata.get('Description'))  # may be long
                # pkg.add_licenses(pkgdata['License'])  # long garbage

                pkg.add_categories(map(str, pkgdata.get('Tags', [])))

                if 'Installers' in pkgdata:
                    pkg.add_downloads(installer['InstallerUrl'] for installer in pkgdata['Installers'])

                pkg.set_extra_field('yamlpath', pkgloc.yamlpath_rel)

                yield pkg
