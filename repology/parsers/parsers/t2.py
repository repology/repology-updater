# Copyright (C) 2019-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import re
from collections import defaultdict
from typing import Iterable

from repology.logger import Logger
from repology.package import PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.patches import add_patch_files
from repology.parsers.walk import walk_tree


def _parse_descfile(path: str, logger: Logger) -> dict[str, list[str]]:
    data: dict[str, list[str]] = defaultdict(list)

    # http://t2sde.org/handbook/html/t2.package.desc.html
    tag_map = {
        'i': 'title',
        't': 'text',
        'u': 'url',
        'a': 'author',
        'm': 'maintainer',
        'c': 'category',
        'f': 'flag',
        'r': 'architecture',
        'arch': 'architecture',
        'k': 'kernel',
        'kern': 'kernel',
        'e': 'dependency',
        'dep': 'dependency',
        'l': 'license',
        's': 'status',
        'v': 'version',
        'ver': 'version',
        'p': 'priority',
        'pri': 'priority',
        'o': 'conf',
        'd': 'download',
        'down': 'download',
        #'s': 'source',  # duplicate - documentation is incorrect?
        'src': 'source',
    }

    with open(path, 'r', encoding='latin1') as descfile:
        for line in descfile:
            line = line.strip()

            if not line.startswith('[') or line.startswith('[['):
                continue

            match = re.fullmatch(r'\[([^\[\]]+)\]\s*(.*?)', line, re.DOTALL)

            if match:
                tag = match.group(1).lower()
                tag = tag_map.get(tag, tag)
                data[tag].append(match.group(2))
            else:
                logger.log('unexpected line "{}"'.format(line), Logger.WARNING)

    return data


class T2DescParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for desc_path in walk_tree(path, suffix='.desc'):
            rel_desc_path = os.path.relpath(desc_path, path)
            with factory.begin(rel_desc_path) as pkg:
                pkgpath = os.path.dirname(rel_desc_path)
                subdir = os.path.basename(pkgpath)
                name = os.path.basename(rel_desc_path).removesuffix('.desc')

                if subdir != name:
                    raise RuntimeError(f'recipe name "{name}" is different from its subdirectory name "{subdir}", this is not expected; see https://github.com/rxrbln/t2sde/issues/173')

                data = _parse_descfile(desc_path, pkg)

                pkg.add_name(name, NameType.T2_NAME)
                pkg.set_extra_field('path', pkgpath)
                pkg.set_version(data['version'][0])
                pkg.set_summary(data['title'][0])

                pkg.add_homepages((url.split()[0] for url in data.get('url', []) if url))
                #pkg.add_homepages(data.get('cv-url'))  # url used by version checker; may be garbage
                pkg.add_licenses(data['license'])
                pkg.add_maintainers(map(extract_maintainers, data['maintainer']))
                pkg.add_categories(data['category'])

                for cksum, filename, url, *rest in (line.split() for line in data.get('download', [])):
                    url = url.lstrip('-!')

                    if url.endswith('/'):
                        url += filename

                    pkg.add_downloads(url)

                add_patch_files(pkg, os.path.dirname(desc_path), '*.patch')

                yield pkg
