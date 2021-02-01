# Copyright (C) 2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Iterable, Optional

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.versions import VersionStripper
from repology.parsers.walk import walk_tree
from repology.transformer import PackageTransformer


def _parse_upstream_url(pkgpath: str) -> Optional[str]:
    checksums_path = os.path.join(pkgpath, 'checksums.ini')
    if not os.path.exists(checksums_path):
        return None

    with open(checksums_path) as fd:
        for line in fd:
            k, v = map(str.strip, line.split('=', 1))
            if k == 'upstream_url':
                return v

        return None


class SageMathParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right('.p')

        for versionfile in walk_tree(path, name='package-version.txt'):
            pkgpath = os.path.dirname(versionfile)
            with factory.begin(pkgpath) as pkg:
                pkg.add_name(os.path.basename(pkgpath), NameType.SAGEMATH_NAME)

                projectname = os.path.basename(pkgpath)
                if os.path.exists(os.path.join(pkgpath, 'install-requires.txt')):
                    projectname = 'python:' + projectname

                pkg.add_name(projectname, NameType.SAGEMATH_PROJECT_NAME)

                with open(versionfile) as fd:
                    pkg.set_version(fd.read().strip(), normalize_version)

                if upstream_url := _parse_upstream_url(pkgpath):
                    pkg.add_downloads(
                        upstream_url.replace(
                            'VERSION',
                            pkg.rawversion
                        )
                    )

                yield pkg
