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
import os
from typing import Dict, Iterable

from libversion import version_compare

from repology.logger import Logger
from repology.package import PackageFlags
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


def _as_str(v):
    if v is None:
        return None
    if isinstance(v, list):
        assert(len(v) == 1)
        return str(v[0])
    return str(v)


def _as_list(v):
    if v is None:
        return []
    if not isinstance(v, list):
        return [v]
    return v


def _iter_packages(path):
    for filename in os.listdir(path):
        if not filename.endswith('.json'):
            continue

        with open(os.path.join(path, filename), 'r') as jsonfile:
            yield from (hit['fields'] for hit in json.load(jsonfile))


def _parse_package(pkg, fields):
    pkg.set_name(_as_str(fields['distribution']))
    pkg.set_version(_as_str(fields['version']))
    pkg.add_maintainers(_as_str(fields['author']).lower() + '@cpan')
    pkg.add_licenses(_as_list(fields['license']))
    pkg.set_summary(_as_str(fields.get('abstract')))
    pkg.add_homepages(_as_str(fields.get('resources.homepage')))
    pkg.add_downloads(_as_list(fields.get('download_url')))

    return pkg


def _parse_latest_packages(packages, latest_versions, factory):
    for fields in packages:
        # only take latest versions (there's only one of them per distribution)
        if _as_str(fields['status']) != 'latest':
            continue

        pkg = _parse_package(factory.begin(), fields)

        if not pkg.version:
            pkg.log('empty version', severity=Logger.ERROR)
            continue

        latest_versions[pkg.name] = pkg.version
        yield pkg


def _parse_devel_packages(packages, latest_versions, factory):
    for fields in packages:
        if _as_str(fields['maturity']) != 'developer':
            continue

        pkg = _parse_package(factory.begin(), fields)

        if not pkg.version:
            pkg.log('empty version', severity=Logger.ERROR)
            continue

        if version_compare(pkg.version, latest_versions.get(pkg.name, '0')) > 0:
            pkg.set_flags(PackageFlags.DEVEL)
            yield pkg


class MetacpanAPIParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        latest_versions: Dict[str, str] = {}

        yield from _parse_latest_packages(_iter_packages(path), latest_versions, factory)
        yield from _parse_devel_packages(_iter_packages(path), latest_versions, factory)
