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

from google.protobuf.text_format import Parse as ParseTextFormat

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.pb.distri_pb2 import Build as BuildMessage
from repology.parsers.walk import walk_tree
from repology.transformer import PackageTransformer


class DistriGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for protofile in walk_tree(path, name='build.textproto'):
            protofile_rel = os.path.relpath(protofile, path)
            with factory.begin(protofile_rel) as pkg:
                pkgpath = os.path.dirname(protofile_rel)

                pkg.add_name(os.path.basename(pkgpath), NameType.DISTRI_NAME)

                with open(protofile) as f:
                    build = BuildMessage()
                    ParseTextFormat(f.read(), build, allow_unknown_field=True)

                pkg.set_version(build.version, lambda ver: ver.rsplit('-', 1)[0])
                pkg.add_downloads(build.source)
                pkg.set_extra_field('path', pkgpath)

                yield pkg
