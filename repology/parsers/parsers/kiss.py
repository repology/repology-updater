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
from typing import Iterable

from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.walk import walk_tree
from repology.transformer import PackageTransformer


def _is_good_download(download: str) -> bool:
    return '://' in download


class KissGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for versionpath in walk_tree(path, name='version'):
            rootdir = os.path.dirname(versionpath)
            with factory.begin(rootdir) as pkg:
                pkg.set_name(os.path.basename(rootdir))

                with open(versionpath) as f:
                    version, revision = f.read().strip().split()
                    pkg.set_version(version)

                with open(os.path.join(rootdir, 'sources')) as f:
                    pkg.add_downloads(
                        filter(
                            _is_good_download,
                            (line.strip().split()[0] for line in f)
                        )
                    )

                pkgpath = os.path.relpath(rootdir, path)

                subrepo = os.path.split(pkgpath)[0]

                if subrepo == 'testing':
                    continue

                pkg.set_extra_field('path', pkgpath)
                pkg.set_subrepo(subrepo)

                yield pkg
