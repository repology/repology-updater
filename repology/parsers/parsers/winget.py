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
    vendor: str
    vendorpath: str

    product: str
    productpath: str

    filename: str
    yamlpath: str


def _iter_packages(path: str) -> Iterable[_PackageLocation]:
    for vendor in os.listdir(os.path.join(path, 'manifests')):
        vendorpath = os.path.join(path, 'manifests', vendor)
        for product in os.listdir(vendorpath):
            productpath = os.path.join(vendorpath, product)
            for filename in os.listdir(productpath):
                yamlpath = os.path.join(productpath, filename)
                if filename.lower().endswith('.yaml'):
                    yield _PackageLocation(
                        vendor,
                        vendorpath,
                        product,
                        productpath,
                        filename,
                        yamlpath
                    )


class WingetGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for pkgloc in _iter_packages(path):
            with factory.begin(os.path.relpath(pkgloc.yamlpath, path)) as pkg:
                try:
                    with open(pkgloc.yamlpath, 'r') as fd:
                        pkgdata = yaml.safe_load(fd)
                except UnicodeDecodeError:
                    pkg.log('Cannot read file, probably UTF-16 garbage', Logger.ERROR)
                    continue

                pkg.add_name(pkgdata['Id'], NameType.WINGET_ID)
                pkg.add_name(pkgdata['Id'].split('.', 1)[-1], NameType.WINGET_ID_NAME)
                pkg.add_name(pkgdata['Name'], NameType.WINGET_NAME)
                pkg.add_name(os.path.join(pkgloc.vendor, pkgloc.product), NameType.WINGET_PATH)

                if isinstance(pkgdata['Version'], float):
                    pkg.log(f'Version {pkgdata["Version"]} is a floating point, should be quoted', Logger.ERROR)

                pkg.set_version(str(pkgdata['Version']))
                pkg.add_homepages(pkgdata.get('Homepage'))

                # pkg.set_summary(pkgdata.get('Description'))  # may be long
                # pkg.add_licenses(pkgdata['License'])  # long garbage

                if pkgdata.get('Tags'):
                    pkg.add_categories(pkgdata['Tags'].split(','))

                pkg.add_downloads(installer['Url'] for installer in pkgdata['Installers'])

                yield pkg
