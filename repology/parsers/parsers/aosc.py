# Copyright (C) 2017 Dingyuan Wang <gumblex@aosc.io>
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

from repology.logger import Logger
from repology.package import PackageFlags
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers


def SanitizeVersion(version):
    origversion = version

    pos = version.rfind(':')
    if pos != -1:
        version = version[pos + 1:]

    if version != origversion:
        return version, origversion
    else:
        return version, None


class AoscPkgsParser(Parser):
    def iter_parse(self, path, factory):
        with open(path, 'r', encoding='utf-8') as jsonfile:
            for package in json.load(jsonfile)['packages']:
                pkg = factory.begin()

                pkg.name = package['name']

                if package['version'] is None:
                    factory.log('no version: {}'.format(pkg.name), severity=Logger.ERROR)
                    continue

                pkg.version, _ = SanitizeVersion(package['version'])
                pkg.origversion = package['full_version']
                pkg.category = package['pkg_section'] or package['section']
                pkg.comment = package['description']
                pkg.maintainers = extract_maintainers(package['committer'])

                if pkg.version == '999':
                    pkg.SetFlag(PackageFlags.ignore)  # XXX: rolling? revisit

                yield pkg
