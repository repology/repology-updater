# Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Dict, Iterable, List

from repology.logger import Logger
from repology.package import PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.walk import walk_tree
from repology.transformer import PackageTransformer


def _parse_descfile(path: str, logger: Logger) -> Dict[str, List[str]]:
    data: Dict[str, List[str]] = {}

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

            if line.startswith('#'):
                continue

            match = re.fullmatch('\\[([^\\[\\]]+)\\]\\s*(.*?)', line, re.DOTALL)

            if match:
                tag = match.group(1).lower()
                tag = tag_map.get(tag, tag)
                data.setdefault(tag, []).append(match.group(2))
            elif line:
                logger.log('unexpected line "{}"'.format(line), Logger.WARNING)

    return data


class T2DescParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for filename in walk_tree(path, suffix='.desc'):
            rel_filename = os.path.relpath(filename, path)
            with factory.begin(rel_filename) as pkg:
                pkgpath = os.path.dirname(rel_filename)
                name = os.path.basename(pkgpath)

                if name + '.desc' != os.path.basename(rel_filename):
                    raise RuntimeError('Path inconsistency (expected .../foo/foo.desc)')

                data = _parse_descfile(filename, pkg)

                pkg.add_name(name, NameType.T2_NAME)
                pkg.add_name(pkgpath, NameType.T2_FULL_NAME)
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

                    if url.startswith('cvs') or url.startswith('git') or url.startswith('svn') or url.startswith('hg'):
                        # snapshots basically
                        pkg.set_flags(PackageFlags.UNTRUSTED)

                    pkg.add_downloads(url)

                yield pkg
