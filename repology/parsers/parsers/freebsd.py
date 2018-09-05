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

from repology.logger import Logger
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers


def SanitizeVersion(version):
    origversion = version

    pos = version.rfind(',')
    if pos != -1:
        version = version[0:pos]

    pos = version.rfind('_')

    if pos != -1:
        version = version[0:pos]

    if version != origversion:
        return version, origversion
    else:
        return version, None


class FreeBSDIndexParser(Parser):
    def iter_parse(self, path, factory):
        with open(path, encoding='utf-8') as indexfile:
            for line in indexfile:
                fields = line.strip().split('|')
                if len(fields) != 13:
                    factory.log('package {} skipped, incorrect number of fields in INDEX'.format(fields[0]), severity=Logger.ERROR)
                    continue

                pkg = factory.begin()

                pkg.name, version = fields[0].rsplit('-', 1)
                pkg.version, pkg.origversion = SanitizeVersion(version)
                pkg.comment = fields[3]
                pkg.maintainers = extract_maintainers(fields[5])
                pkg.category = fields[6].split(' ')[0]

                if fields[9]:
                    pkg.homepage = fields[9]

                path = fields[1].split('/')

                pkg.extrafields['portname'] = path[-1]
                pkg.extrafields['origin'] = '/'.join(path[-2:])

                yield pkg
