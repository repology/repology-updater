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


class OpenVSXParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        with open(path, 'r') as extdatafile:
            extension_data = json.load(extdatafile)
            raw_extensions = extension_data['extensions']

        for extension in raw_extensions:
            with factory.begin() as pkg:
                # TODO: More metadata is available, it's just harder to fetch and will require its own fetcher, in all likelihood
                pkg.add_name('vscode-extension:{namespace}-{name}'.format(**extension), NameType.GENERIC_SRC_NAME)
                pkg.set_version(extension['version'])
                pkg.set_summary(extension['description'])
                pkg.add_maintainers('{namespace}@openvsx'.format(**extension))
                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, 'https://open-vsx.org/extension/{namespace}/{name}'.format(**extension))
                pkg.add_links(LinkType.UPSTREAM_DOWNLOAD, extension['files']['download'])

                yield pkg
