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
from typing import Any, Iterable

from libversion import version_compare

from repology.logger import Logger
from repology.package import LinkType, PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser


def _as_maybe_str(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, list):
        assert len(v) == 1
        return str(v[0])
    return str(v)


def _as_str(v: Any) -> str:
    if v is None:
        raise RuntimeError('unexpected empty value')
    if isinstance(v, list):
        assert len(v) == 1
        return str(v[0])
    return str(v)


def _as_list(v: Any) -> list[Any]:
    if v is None:
        return []
    if not isinstance(v, list):
        return [v]
    return v


def _iter_packages(path: str) -> Iterable[dict[str, Any]]:
    for filename in os.listdir(path):
        if not filename.endswith('.json'):
            continue

        with open(os.path.join(path, filename), 'r') as jsonfile:
            yield from (hit['_source'] for hit in json.load(jsonfile))


def _parse_package(pkg: PackageMaker, fields: dict[str, Any]) -> tuple[str, PackageMaker]:
    distribution = _as_str(fields['distribution'])
    pkg.add_name(distribution, NameType.CPAN_NAME)

    version = _as_str(fields['version'])
    pkg.set_version(version)

    author = _as_maybe_str(fields['author'])
    if author:
        pkg.add_maintainers(author.lower() + '@cpan')

    pkg.add_licenses(_as_list(fields['license']))
    pkg.set_summary(_as_maybe_str(fields.get('abstract')))
    pkg.add_links(LinkType.PROJECT_DOWNLOAD, _as_list(fields.get('download_url')))

    if resources := fields.get('resources'):
        pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, _as_maybe_str(resources.get('homepage')))
        if repository := resources.get('repository'):
            for key in ['web', 'url']:
                if (link := repository.get(key)) is not None:
                    pkg.add_links(LinkType.UPSTREAM_REPOSITORY, link)
                    break

    name = _as_str(fields['name'])
    if version not in name:
        pkg.set_flags(PackageFlags.UNTRUSTED)

    return distribution, pkg


def _parse_latest_packages(packages: Iterable[dict[str, Any]], latest_versions: dict[str, str], factory: PackageFactory) -> Iterable[PackageMaker]:
    for fields in packages:
        # only take latest versions (there's only one of them per distribution)
        if _as_str(fields['status']) != 'latest':
            continue

        distribution, pkg = _parse_package(factory.begin(), fields)

        if not pkg.version:
            pkg.log('empty version', severity=Logger.ERROR)
            continue

        latest_versions[distribution] = pkg.version
        yield pkg


def _parse_devel_packages(packages: Iterable[dict[str, Any]], latest_versions: dict[str, str], factory: PackageFactory) -> Iterable[PackageMaker]:
    for fields in packages:
        if _as_str(fields['maturity']) != 'developer':
            continue

        distribution, pkg = _parse_package(factory.begin(), fields)

        if not pkg.version:
            pkg.log('empty version', severity=Logger.ERROR)
            continue

        if version_compare(pkg.version, latest_versions.get(distribution, '0')) > 0:
            pkg.set_flags(PackageFlags.DEVEL)
            yield pkg


class MetacpanAPIParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        latest_versions: dict[str, str] = {}

        yield from _parse_latest_packages(_iter_packages(path), latest_versions, factory)
        yield from _parse_devel_packages(_iter_packages(path), latest_versions, factory)
