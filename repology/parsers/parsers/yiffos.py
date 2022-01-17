# Copyright (C) 2022 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import json
import os
from typing import Iterable

from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.walk import walk_tree


class YiffOSJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for pkginfo_path_abs in walk_tree(path, name='PKGINFO'):
            pkginfo_path_rel = os.path.relpath(pkginfo_path_abs, path)

            with factory.begin(pkginfo_path_rel) as pkg:
                subdir = os.path.dirname(pkginfo_path_rel)

                with open(pkginfo_path_abs) as fd:
                    pkginfo = json.loads(fd.read())

                if subdir != pkginfo['name']:
                    raise RuntimeError(f'subdir "{subdir}" != name "{pkginfo["name"]}"')

                pkg.add_name(pkginfo['name'], NameType.YIFFOS_NAME)
                pkg.set_version(pkginfo['version'])
                pkg.set_summary(pkginfo['description'])
                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, pkginfo['url'])
                pkg.add_licenses(pkginfo['license'])
                pkg.add_maintainers(map(extract_maintainers, pkginfo['maintainers']))

                yield pkg
