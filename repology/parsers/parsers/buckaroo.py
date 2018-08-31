# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.package import Package
from repology.parsers import Parser
from repology.parsers.walk import walk_tree


class BuckarooGitParser(Parser):
    def Parse(self, path):
        result = []

        for filename in walk_tree(path, suffix='.json'):
            data = json.load(open(filename, encoding='utf-8', errors='ignore'))

            if 'versions' not in data:
                continue

            for version, versiondata in data['versions'].items():
                pkg = Package()

                pkg.name = data['name']

                if data['license']:
                    pkg.licenses = [data['license']]

                pkg.homepage = data['url']

                pkg.version = version

                pkg.extrafields['recipe'] = os.path.relpath(filename, path)

                # garbage: links to git:// or specific commits
                #if isinstance(versiondata['source'], str):
                #    pkg.downloads = [versiondata['source']]
                #else:
                #    pkg.downloads = [versiondata['source']['url']]

            result.append(pkg)

        return result
