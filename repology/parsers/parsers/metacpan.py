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

from libversion import version_compare

from repology.package import Package, PackageFlags
from repology.parsers import Parser


def ensure_str(v):
    if v is None:
        return None
    if isinstance(v, list):
        assert(len(v) == 1)
        return str(v[0])
    return str(v)


def ensure_list(v):
    if v is None:
        return []
    if not isinstance(v, list):
        return [v]
    return v


class MetacpanAPIParser(Parser):
    def __init__(self):
        pass

    @staticmethod
    def parse_package(fields):
        pkg = Package()

        pkg.name = ensure_str(fields['distribution'])
        pkg.version = ensure_str(fields['version'])
        pkg.maintainers = [ensure_str(fields['author']).lower() + '@cpan']
        pkg.licenses = ensure_list(fields['license'])
        pkg.comment = ensure_str(fields.get('abstract'))
        pkg.homepage = ensure_str(fields.get('resources.homepage'))
        pkg.downloads = ensure_list(fields.get('download_url'))

        return pkg

    @staticmethod
    def parse_latest_packages(hits, latest_versions):
        for hit in hits:
            fields = hit['fields']

            # only take latest versions (there's only one of them per distribution)
            if ensure_str(fields['status']) != 'latest':
                continue

            pkg = MetacpanAPIParser.parse_package(fields)

            if not pkg.version:
                print('{}: empty version {}'.format(pkg.name, pkg.version), file=sys.stderr)
                continue

            latest_versions[pkg.name] = pkg.version
            yield pkg

    @staticmethod
    def parse_devel_packages(hits, latest_versions):
        for hit in hits:
            fields = hit['fields']

            if ensure_str(fields['maturity']) != 'developer':
                continue

            pkg = MetacpanAPIParser.parse_package(fields)

            if not pkg.version:
                print('{}: empty version {}'.format(pkg.name, pkg.version), file=sys.stderr)
                continue

            if version_compare(pkg.version, latest_versions.get(pkg.name, '0')) > 0:
                pkg.SetFlag(PackageFlags.devel)
                yield pkg

    def iter_parse(self, path):
        latest_versions = {}

        # Pass 1: process latest versions
        for filename in os.listdir(path):
            if not filename.endswith('.json'):
                continue

            with open(os.path.join(path, filename), 'r') as jsonfile:
                yield from MetacpanAPIParser.parse_latest_packages(json.load(jsonfile), latest_versions)

        # Pass 2: process devel versions
        for filename in os.listdir(path):
            if not filename.endswith('.json'):
                continue

            with open(os.path.join(path, filename), 'r') as jsonfile:
                yield from MetacpanAPIParser.parse_devel_packages(json.load(jsonfile), latest_versions)
