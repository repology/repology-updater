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
from typing import Any, Dict, Iterable, List, Tuple, Union

import yaml

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.walk import walk_tree
from repology.transformer import PackageTransformer


def _extract_version_urls(conandata: Dict[str, Any]) -> Iterable[Tuple[str, Union[str, List[str]]]]:
    for key, value in conandata['sources'].items():
        if isinstance(value, dict) and 'url' in value:
            # {version: {"url": "...", "sha256": "..."}}
            yield key, value['url']
        elif isinstance(value, list):
            # {version: [{"url": "...", "sha256": "..."}]} - tweetnacl
            yield key, [item['url'] for item in value]
        elif isinstance(value, dict):
            # nested dict (for instance, by arch) - strawberryperl
            yield from _extract_version_urls(value)
        else:
            raise RuntimeError('unexpected conandata.yml format')


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

                for version, urls in _extract_version_urls(conandata):
                    verpkg = pkg.clone(append_ident=version)

                    verpkg.set_version(version)
                    verpkg.add_downloads(urls)

                    if version in patches:
                        verpkg.set_extra_field('patch', patches[version])

                    verpkg.set_extra_field('folder', conandata_rel_path.split('/')[2])

                    yield verpkg
