# Copyright (C) 2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from repology.transformer import PackageTransformer


@dataclass
class _PackageLocation:
    product: str
    productpath: str

    filename: str
    yamlpath: str


def _iter_packages(path: str) -> Iterable[_PackageLocation]:
    rootdir = os.path.join(path, 'manifests')
    for product in os.listdir(rootdir):
        productpath = os.path.join(path, 'manifests', product)
        for filename in os.listdir(productpath):
            yamlpath = os.path.join(productpath, filename)
            if filename.lower().endswith('.yaml'):
                yield _PackageLocation(
                    product,
                    productpath,
                    filename,
                    yamlpath
                )


class AppgetGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for pkgloc in _iter_packages(path):
            with factory.begin(os.path.relpath(pkgloc.yamlpath, path)) as pkg:
                try:
                    with open(pkgloc.yamlpath, 'r') as fd:
                        pkgdata = yaml.safe_load(fd)
                except UnicodeDecodeError:
                    pkg.log('Cannot read file, probably UTF-16 garbage', Logger.ERROR)
                    continue

                pkg.add_name(pkgdata['id'], NameType.APPGET_ID)
                pkg.add_name(pkgdata['name'], NameType.APPGET_NAME)

                pkg.set_extra_field('yamlname', pkgloc.filename[:-5])

                if 'version' not in pkgdata:
                    pkg.log('No version, skipping', Logger.ERROR)
                    continue

                if isinstance(pkgdata['version'], float):
                    pkg.log(f'Version {pkgdata["version"]} is a floating point, should be quoted', Logger.ERROR)

                pkg.set_version(str(pkgdata['version']))
                pkg.add_homepages(pkgdata.get('home'), pkgdata.get('repo'))

                pkg.add_licenses(pkgdata.get('license'))

                pkg.add_downloads(installer['location'] for installer in pkgdata['installers'])

                yield pkg
