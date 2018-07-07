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


class ScoopGitParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        for root, dirs, files in os.walk(path):
            for filename in files:
                jsonpath = os.path.join(root, filename)
                if not jsonpath.endswith('.json'):
                    continue

                jsondata = None
                with open(jsonpath, 'r', encoding='utf-8') as jsonfile:
                    jsondata = json.load(jsonfile, strict=False)

                pkg = Package()

                pkg.name = filename[:-5]
                pkg.version = jsondata['version']

                if 'url' in jsondata:
                    pkg.downloads = jsondata['url'] if isinstance(jsondata['url'], list) else [jsondata['url']]

                if 'homepage' in jsondata:
                    pkg.homepage = jsondata['homepage']

                if 'license' in jsondata:
                    pkg.licenses = [jsondata['license']]

                pkg.extrafields = {'path': os.path.relpath(jsonpath, path)}

                result.append(pkg)

        return result
