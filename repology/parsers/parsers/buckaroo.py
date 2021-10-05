# Copyright (C) 2018-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.walk import walk_tree


class BuckarooGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for filename in walk_tree(path, suffix='.json'):
            data = json.load(open(filename, encoding='utf-8', errors='ignore'))

            if 'versions' not in data:
                continue

            with factory.begin(filename) as pkg:
                pkg.add_name(data['name'], NameType.BUCKAROO_NAME)
                pkg.add_name(os.path.basename(filename)[:-5], NameType.BUCKAROO_FILENAME)
                pkg.add_licenses(data['license'])
                pkg.add_homepages(data['url'])

                pkg.set_extra_field('recipe', os.path.relpath(filename, path))

                for version, versiondata in data['versions'].items():
                    verpkg = pkg.clone()
                    verpkg.set_version(version)

                    # not parsing sources as these contain references to specific commit snapshots

                    yield verpkg
