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

from repology.logger import Logger
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


class ScoopGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for root, dirs, files in os.walk(path):
            if os.path.basename(root).startswith('.'):
                continue  # e.g. .vscode

            for filename in files:
                if not filename.endswith('.json'):
                    continue

                fullpath = os.path.join(root, filename)
                relpath = os.path.relpath(fullpath, path)

                with factory.begin(relpath) as pkg:
                    with open(fullpath, 'r', encoding='utf-8') as jsonfile:
                        data = json.load(jsonfile, strict=False)

                    pkg.add_name(filename[:-5], NameType.SCOOP_NAME)
                    pkg.set_version(data['version'])

                    pkg.add_homepages(data.get('homepage'))
                    pkg.add_downloads(data.get('url'))

                    if 'architecture' in data:
                        for archdata in data['architecture'].values():
                            pkg.add_downloads(archdata.get('url'))

                    if 'license' in data:
                        if isinstance(data['license'], str):
                            pkg.add_licenses(data['license'])
                        elif isinstance(data['license'], dict) and 'identifier' in data['license']:
                            pkg.add_licenses(data['license']['identifier'])
                        else:
                            pkg.log('unsupported license format', severity=Logger.ERROR)

                    pkg.set_extra_field('path', relpath)

                    yield pkg
