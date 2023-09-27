# Copyright (C) 2017-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.package import LinkType, PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser


class CratesIOParser(Parser):
    def iter_parse_one_file(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        with open(path, 'r', encoding='utf-8', errors='ignore') as pagedata:
            for crate in json.load(pagedata)['crates']:
                with factory.begin(crate.get('id')) as pkg:
                    if crate['id'] != crate['name']:
                        raise RuntimeError('id != name')

                    pkg.add_name(crate['id'], NameType.CRATESIO_ID)

                    pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, crate['homepage'])
                    pkg.add_links(LinkType.UPSTREAM_REPOSITORY, crate['repository'])
                    pkg.add_links(LinkType.UPSTREAM_DOCUMENTATION, crate['documentation'])

                    pkg.set_summary(crate['description'])

                    if crate['max_stable_version'] == crate['max_version']:
                        versions_with_flags = [(crate['max_stable_version'], 0)]
                    elif crate['max_stable_version'] is None:
                        versions_with_flags = [(crate['max_version'], PackageFlags.DEVEL)]
                    else:
                        versions_with_flags = [
                            (crate['max_stable_version'], 0),
                            (crate['max_version'], PackageFlags.DEVEL)
                        ]

                    for version, flags in versions_with_flags:
                        verpkg = pkg.clone()
                        verpkg.set_version(version)
                        verpkg.set_flags(flags)
                        yield verpkg

    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for pagefilename in os.listdir(path):
            if pagefilename.endswith('.json'):
                yield from self.iter_parse_one_file(os.path.join(path, pagefilename), factory)
