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
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Iterator

import yaml

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.walk import walk_tree


@dataclass
class _VersionInfo:
    version: str
    url: str

def _extract_version_infos(huntercmake: str) -> Iterator[_VersionInfo]:
    regex = r"hunter_add_version\((.*?)\)"
    matches = re.finditer(regex, huntercmake, re.DOTALL)

    for matchNum, match in enumerate(matches, start=0):        
        for groupNum in range(0, len(match.groups())):
            groupNum = groupNum + 1
            
            group = match.group(groupNum)
            print ("Group {groupNum} found at {start}-{end}: {group}".format(groupNum = groupNum, start = match.start(groupNum), end = match.end(groupNum), group = group))
            
            args = group.replace(' ', '').split('\n')
            version_index = args.index('VERSION')
            url_index = args.index('URL')
            print(f'version={args[version_index+1]}, url={args[url_index+1]}')

            yield _VersionInfo(args[version_index+1].replace('"', ''), args[url_index+1].replace('"', ''))


class HunterGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for huntercmake_abs_path in walk_tree(os.path.join(path, 'cmake', 'projects'), name='hunter.cmake'):
            huntercmake_rel_path = os.path.relpath(huntercmake_abs_path, path)

            with factory.begin(huntercmake_rel_path) as pkg:
                pkg.add_name(huntercmake_rel_path.split('/')[2], NameType.HUNTER_PROJECT_NAME)

                with open(huntercmake_abs_path) as fd:
                    huntercmake = fd.read()

                for version_info in _extract_version_infos(huntercmake):
                    verpkg = pkg.clone(append_ident=':' + version_info.version)

                    verpkg.set_version(version_info.version)
                    verpkg.add_downloads(version_info.url)

                    yield verpkg
