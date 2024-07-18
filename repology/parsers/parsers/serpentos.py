# Copyright (C) 2024 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import yaml

from repology.logger import Logger
from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.walk import walk_tree


class SerpentOsGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for filename in walk_tree(path, suffix='stone.yaml'):
            relpath = os.path.relpath(filename, path)
            subdir = os.path.basename(os.path.dirname(relpath))

            with factory.begin(relpath) as pkg:
                with open(filename, 'r') as fd:
                    pkgdata = yaml.safe_load(fd)

                if pkgdata['name'] != subdir:
                    RuntimeError(f'subdir "{subdir}" != name "{pkgdata["name"]}"')

                if isinstance(pkgdata['version'], float):
                    pkg.log(f'version "{pkgdata["version"]}" is a floating point, should be quoted in YAML', Logger.ERROR)

                pkg.add_name(pkgdata['name'], NameType.SERPENTOS_NAME)
                pkg.set_version(str(pkgdata['version']))
                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, pkgdata.get('homepage'))
                pkg.add_licenses(pkgdata.get('license'))
                pkg.set_summary(pkgdata.get('summary'))

                if upstreams := pkgdata.get('upstreams'):
                    for upstream in upstreams:
                        for url, checksum in upstream.items():
                            if url.startswith('git|'):
                                pkg.add_links(LinkType.UPSTREAM_REPOSITORY, url[4:])
                            else:
                                pkg.add_links(LinkType.UPSTREAM_DOWNLOAD, url)

                yield pkg
