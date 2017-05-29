#!/usr/bin/env python3
#
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

import argparse
import os
import sys
from timeit import default_timer as timer

import repology.config
from repology.database import *
from repology.queryfilters import *


class StatCounter():
    def __init__(self):
        self.count = 0
        self.min_time = None
        self.max_time = None
        self.total_time = None
        self.min_packages = None
        self.max_packages = None
        self.total_packages = None
        self.min_metapackages = None
        self.max_metapackages = None
        self.total_metapackages = None

    def Count(self, time, packages, metapackages):
        if self.count == 0:
            self.min_time = self.max_time = self.total_time = time
            self.min_packages = self.max_packages = self.total_packages = packages
            self.min_metapackages = self.max_metapackages = self.total_metapackages = metapackages
        else:
            self.min_time = min(self.min_time, time)
            self.max_time = max(self.max_time, time)
            self.total_time += time

            self.min_packages = min(self.min_packages, packages)
            self.max_packages = max(self.max_packages, packages)
            self.total_packages += packages

            self.min_metapackages = min(self.min_metapackages, metapackages)
            self.max_metapackages = max(self.max_metapackages, metapackages)
            self.total_metapackages += metapackages

        self.count += 1

    def Print(self):
        print('        Time: {:.2f}ms/{:.2f}ms/{:.2f}ms'.format(self.min_time * 1000.0, self.total_time / self.count * 1000.0, self.max_time * 1000.0))
        print('    Packages: {}/{:.0f}/{}'.format(self.min_packages, self.total_packages / self.count, self.max_packages))
        print('Metapackages: {}/{:.0f}/{}'.format(self.min_metapackages, self.total_metapackages / self.count, self.max_metapackages))


def RunTest(database, title, pagefilter, *filters):
    print('===> ' + title)

    sc = StatCounter()
    for letter in ['0'] + [chr(c) for c in range(ord('a'), ord('z'))]:
        start = timer()
        packages = database.GetMetapackages(pagefilter(letter), *filters, limit=500)
        timedelta = timer() - start

        effnames = set()
        for package in packages:
            effnames.add(package.effname)

        sc.Count(timedelta, len(packages), len(effnames))

    sc.Print()


def Main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-D', '--dsn', default=repology.config.DSN, help='database connection params')
    options = parser.parse_args()

    database = Database(options.dsn)

    print('==> Core requests')

    RunTest(database, 'No filter (pagination only): starting', NameStartingQueryFilter)
    RunTest(database, 'No filter (pagination only): before', NameBeforeQueryFilter)
    RunTest(database, 'No filter (pagination only): after', NameAfterQueryFilter)

    RunTest(database, 'Maintainer', NameStartingQueryFilter, MaintainerQueryFilter('amdmi3@freebsd.org'))
    RunTest(database, 'InRepo', NameStartingQueryFilter, InRepoQueryFilter('freebsd'))
    RunTest(database, 'Outdated', NameStartingQueryFilter, OutdatedInRepoQueryFilter('freebsd'))
    RunTest(database, 'NotInRepo', NameStartingQueryFilter, NotInRepoQueryFilter('freebsd'))
    RunTest(database, 'NumFamilies', NameStartingQueryFilter, InNumFamiliesQueryFilter(more=10))

    print('==> Advanced filtering')

    RunTest(database, 'Maintainer + InRepo', NameStartingQueryFilter, MaintainerQueryFilter('amdmi3@freebsd.org'), InRepoQueryFilter('freebsd'))
    RunTest(database, 'InRepo + Maintainer', NameStartingQueryFilter, InRepoQueryFilter('freebsd'), MaintainerQueryFilter('amdmi3@freebsd.org'))

    RunTest(database, 'NotInRepo + NumFamilies', NameStartingQueryFilter, NotInRepoQueryFilter('freebsd'), InNumFamiliesQueryFilter(more=5))

    return 0


if __name__ == '__main__':
    os.sys.exit(Main())
