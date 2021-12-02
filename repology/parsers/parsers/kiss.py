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
import subprocess
from typing import Iterable, Iterator

from repology.logger import Logger
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.patches import add_patch_files
from repology.parsers.walk import walk_tree


def read_version(path: str) -> str:
    with open(path) as fd:
        return fd.read().strip().split(None, 1)[0]


def iter_sources(path: str) -> Iterator[str]:
    with open(path) as fd:
        for line in fd:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            url = line.split()[0]

            # KISS introduced substitution variables (see #1166) which
            # we won't support, detect these and refuse to parse.
            # Check for numerics additionally, as there may be verbatim
            # VERSION in the url which affects carbs.
            if 'VERSION' in url and not any(filter(str.isnumeric, url)):  # type: ignore
                raise RuntimeError(f'substitution detected in url: "{url}", refusing to continue')

            if '://' in url:
                yield url


def read_carbs_meta(path: str) -> dict[str, str]:
    meta = {}
    with open(path) as fd:
        for line in fd:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            key, value = map(str.strip, line.split(':', 1))
            meta[key] = value

    return meta


class KissGitParser(Parser):
    _maintainer_from_git: bool
    _use_meta: bool

    def __init__(self, maintainer_from_git: bool = False, use_meta: bool = False):
        self._maintainer_from_git = maintainer_from_git
        self._use_meta = use_meta

    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for version_path_abs in walk_tree(path, name='version'):
            version_path_rel = os.path.relpath(version_path_abs, path)

            package_path_abs = os.path.dirname(version_path_abs)
            package_path_rel = os.path.relpath(package_path_abs, path)
            package_path_rel_comps = os.path.split(package_path_rel)

            sources_path_abs = os.path.join(package_path_abs, 'sources')

            meta_path_abs = os.path.join(package_path_abs, 'meta')

            patches_path_abs = os.path.join(package_path_abs, 'patches')

            with factory.begin(package_path_rel) as pkg:
                pkg.add_name(package_path_rel_comps[-1], NameType.KISS_NAME)
                pkg.set_version(read_version(version_path_abs))

                if not os.path.exists(sources_path_abs):
                    pkg.log('skipping sourceless package', Logger.ERROR)
                    continue

                pkg.add_downloads(iter_sources(sources_path_abs))

                pkg.set_extra_field('path', package_path_rel)
                pkg.set_subrepo(package_path_rel_comps[0])

                if self._maintainer_from_git:
                    command = ['git', 'log', '-1', '--format=tformat:%ae', version_path_rel]
                    with subprocess.Popen(command,
                                          stdout=subprocess.PIPE,
                                          encoding='utf-8',
                                          errors='ignore',
                                          cwd=path) as git:
                        lastauthor, _ = git.communicate()

                    pkg.add_maintainers(extract_maintainers(lastauthor))

                if self._use_meta and os.path.exists(meta_path_abs):
                    meta = read_carbs_meta(meta_path_abs)
                    pkg.set_summary(meta.get('description'))
                    pkg.add_licenses(meta.get('license', '').split(','))
                    pkg.add_maintainers(extract_maintainers(meta.get('maintainer')))

                add_patch_files(pkg, patches_path_abs)

                yield pkg
