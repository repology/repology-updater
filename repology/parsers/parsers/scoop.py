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
import sys

from repology.package import Package
from repology.parsers import Parser


class ScoopGitParser(Parser):
    def iter_parse(self, path, logger):
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
                    if isinstance(jsondata['license'], str):
                        pkg.licenses = [jsondata['license']]
                    elif isinstance(jsondata['license'], dict) and 'identifier' in jsondata['license']:
                        pkg.licenses = [jsondata['license']['identifier']]
                    else:
                        print('WARNING: unsupporte license format for {}'.format(pkg.name), file=sys.stderr)

                pkg.extrafields = {'path': os.path.relpath(jsonpath, path)}

                yield pkg
