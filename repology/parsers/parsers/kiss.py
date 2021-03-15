# Copyright (C) 2019-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import subprocess
from typing import Iterable

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.patches import add_patch_files
from repology.parsers.walk import walk_tree
from repology.transformer import PackageTransformer


class KissGitParser(Parser):
    _maintainer_from_git: bool

    def __init__(self, maintainer_from_git: bool = False):
        self._maintainer_from_git = maintainer_from_git

    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for versionpath in walk_tree(path, name='version'):
            rootdir = os.path.dirname(versionpath)
            with factory.begin(os.path.relpath(rootdir, path)) as pkg:
                pkg.add_name(os.path.basename(rootdir), NameType.KISS_NAME)

                with open(versionpath) as f:
                    version, revision = f.read().strip().split()
                    pkg.set_version(version)

                with open(os.path.join(rootdir, 'sources')) as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue

                        url, *rest = line.split()

                        if '://' in url:
                            pkg.add_downloads(url)

                pkgpath = os.path.relpath(rootdir, path)

                subrepo = os.path.split(pkgpath)[0]

                pkg.set_extra_field('path', pkgpath)
                pkg.set_subrepo(subrepo)

                if self._maintainer_from_git:
                    command = ['git', 'log', '-1', '--format=tformat:%ae', os.path.relpath(versionpath, path)]
                    with subprocess.Popen(command,
                                          stdout=subprocess.PIPE,
                                          encoding='utf-8',
                                          errors='ignore',
                                          cwd=path) as git:
                        lastauthor, _ = git.communicate()

                    pkg.add_maintainers(extract_maintainers(lastauthor))

                add_patch_files(pkg, os.path.join(rootdir, 'patches'))

                yield pkg
