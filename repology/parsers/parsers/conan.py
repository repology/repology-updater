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
from typing import Any, Dict, Iterable, Iterator, List

import yaml

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.walk import walk_tree
from repology.transformer import PackageTransformer


@dataclass
class _UrlInfo:
    tags: List[str]
    url: str


@dataclass
class _VersionInfo:
    version: str
    url_infos: List[_UrlInfo]


def _extract_url_infos_from_arbitrary_structure(data: Any, tags: List[str]) -> Iterator[_UrlInfo]:
    # processes arbitrary nested structure of dicts and lists which
    # is possible in conandata.yaml files

    if isinstance(data, list):
        for item in data:
            yield from _extract_url_infos_from_arbitrary_structure(item, tags)
    elif isinstance(data, dict):
        for key, item in data.items():
            yield from _extract_url_infos_from_arbitrary_structure(item, tags + [key])
    elif isinstance(data, str):
        # note that 'url' may appear more than once, see android-ndk/all/conandata.yml
        if 'url' in tags and 'sha256' not in tags:
            yield _UrlInfo(tags, data)


def _extract_version_infos(conandata: Dict[str, Any]) -> Iterator[_VersionInfo]:
    for version, data in conandata['sources'].items():
        yield _VersionInfo(
            version,
            list(_extract_url_infos_from_arbitrary_structure(data, []))
        )


def _extract_patches(conandata: Dict[str, Any]) -> Dict[str, List[str]]:
    if 'patches' not in conandata:
        return {}

    return {
        version:
            [patch['patch_file'] for patch in patches]
            if isinstance(patches, list)
            else [patches['patch_file']]
        for version, patches in conandata['patches'].items()
    }


class ConanGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for conandata_abs_path in walk_tree(path, name='conandata.yml'):
            conandata_rel_path = os.path.relpath(conandata_abs_path, path)

            with factory.begin(conandata_rel_path) as pkg:
                pkg.add_name(conandata_rel_path.split('/')[1], NameType.CONAN_RECIPE_NAME)

                with open(conandata_abs_path) as fd:
                    conandata = yaml.safe_load(fd)

                patches = _extract_patches(conandata)

                for version_info in _extract_version_infos(conandata):
                    verpkg = pkg.clone(append_ident=':' + version_info.version)

                    verpkg.set_version(version_info.version)

                    # XXX: we may create more subpackages here based on url_info.tags
                    # which may contain various OSes, architectures, compilers and probably
                    # other specifics (see cspice/all/conandata.yml for example)
                    for url_info in version_info.url_infos:
                        verpkg.add_downloads(url_info.url)

                    if version_info.version in patches:
                        verpkg.set_extra_field('patch', patches[version_info.version])

                    verpkg.set_extra_field('folder', conandata_rel_path.split('/')[2])

                    yield verpkg
