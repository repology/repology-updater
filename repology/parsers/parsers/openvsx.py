# Copyright (C) 2024 Gavin John <gavinnjohn@gmail.com>
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

from typing import Iterable

from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_list


class OpenVSXParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for extension in iter_json_list(path, ('extensions', None)):
            with factory.begin() as pkg:
                # TODO: More metadata is available, it's just harder to fetch and will require its own fetcher, in all likelihood
                namespace = extension['namespace']
                name = extension['name']
                pkg.add_name(f'{namespace}.{name}', NameType.OPENVSX_NAMESPACE_DOT_NAME)
                pkg.add_name(f'{namespace}/{name}', NameType.OPENVSX_NAMESPACE_SLASH_NAME)
                pkg.add_name(extension.get('displayName', name), NameType.OPENVSX_DISPLAYNAME)
                pkg.set_version(extension['version'])
                pkg.set_summary(extension.get('description'))
                pkg.add_maintainers(f'{namespace}@openvsx')

                if not extension['files']:
                    continue

                pkg.add_links(LinkType.PROJECT_DOWNLOAD, extension['files']['download'])
                pkg.add_links(LinkType.PACKAGE_RECIPE_RAW, extension['files']['download'].rsplit('/', 1)[0] + '/package.json')

                yield pkg
