#!/usr/bin/env python3
#
# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import os
import sys
import traceback
from argparse import ArgumentParser

from repology.repoman import RepositoryManager
from repology.transformer import PackageTransformer
from repology.database import Database
from repology.logger import *
from repology.package import *
from repology.filters import ShadowFilter


def Main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--statedir', default='_state', help='path to directory with repository state')
    parser.add_argument('-l', '--logfile', help='path to log file (log to stderr by default)')
    parser.add_argument('-m', '--mode', choices=['batch', 'stream'], default='stream', help='processing mode')

    parser.add_argument('-S', '--no-shadow', action='store_true', help='treat shadow repositories as normal')

    parser.add_argument('reponames', metavar='repo|tag', nargs='*', help='repository or tag name to process')
    options = parser.parse_args()

    if not options.reponames:
        options.reponames = ["all"]

    logger = StderrLogger()
    if options.logfile:
        logger = FileLogger(options.logfile)

    repoman = RepositoryManager(options.statedir)

    logger.Log("initializing database...")
    database = Database(host="localhost", db="repology", user="repology", passwd="repology")
    database.CreateTables()

    filters = [] if options.no_shadow else [ShadowFilter()]

    package_queue = []

    def PackageProcessor(packages):
        nonlocal package_queue
        FillVersionInfos(packages)
        package_queue.extend(packages)

        if len(package_queue) >= 1000:
            database.AddPackages(package_queue)
            package_queue = []

    if options.mode == 'stream':
        logger.Log("uploading to database...")
        repoman.StreamDeserializeMulti(processor=PackageProcessor, reponames=options.reponames)
    else:
        logger.Log("loading packages...")
        all_packages = repoman.DeserializeMulti(reponames=options.reponames, logger=logger)
        logger.Log("merging packages...")
        metapackages = MergeMetapackages(all_packages)
        logger.Log("uploading to database...")
        for metaname, packages in sorted(metapackages.items()):
            PackageProcessor(packages)

    # process what's left in the queue
    database.AddPackages(package_queue)

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
