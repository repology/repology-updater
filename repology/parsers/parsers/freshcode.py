# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from libversion import version_compare

from repology.parsers import Parser


class FreshcodeParser(Parser):
    def iter_parse(self, path, factory):
        result = {}

        # note that we actually parse database prepared by
        # fetcher, not the file we've downloaded
        with open(path, 'r', encoding='utf-8') as jsonfile:
            for entry in json.load(jsonfile)['releases']:
                pkg = factory.begin()

                pkg.set_name(entry['name'])
                pkg.set_version(entry['version'])

                if not pkg.check_sanity(verbose=False):
                    continue

                pkg.add_homepages(entry.get('homepage'))
                pkg.set_summary(entry.get('summary'))
                if not pkg.comment:
                    pkg.set_summary(entry.get('description'))  # multiline
                #pkg.add_maintainers(entry.get('submitter') + '@freshcode')  # unfiltered garbage
                #pkg.add_downloads(entry.get('download'))  # ignore for now, may contain download page urls instead of file urls
                pkg.add_licenses(entry.get('license'))

                # take latest known versions
                if pkg.name not in result or version_compare(pkg.version, result[pkg.name].version) > 0:
                    result[pkg.name] = pkg

        yield from result.values()
