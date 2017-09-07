# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from repology.version import VersionCompare


class FreshcodeParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = {}

        # note that we actually parse database prepared by
        # fetcher, not the file we've downloaded
        with open(path, 'r', encoding='utf-8') as jsonfile:
            for entry in json.load(jsonfile)['releases']:
                pkg = Package()

                pkg.name = entry['name']
                pkg.version = entry['version']

                if not pkg.name or not pkg.version:
                    continue

                homepage = entry.get('homepage')
                summary = entry.get('summary')
                description = entry.get('description')
                #submitter = entry.get('submitter')
                #download = entry.get('download')
                license_ = entry.get('license')

                if homepage:
                    pkg.homepage = homepage

                if summary:
                    pkg.comment = summary
                elif description:
                    pkg.comment = description  # multiline

                if license_:
                    pkg.licenses = [license_]

                # unfiltered garbage
                #if submitter:
                #    pkg.maintainers = [submitter + '@freshcode']

                # ignore for now, may contain download page urls instead of file urls
                #if download
                #    pkg.downloads = [download]

                if pkg.name not in result or VersionCompare(pkg.version, result[pkg.name].version) > 0:
                    result[pkg.name] = pkg

        return result.values()
