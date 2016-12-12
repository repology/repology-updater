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
from repology.packageproc import *
from repology.filters import ShadowFilter


def Main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--statedir', default='_state', help='path to directory with repository state')
    parser.add_argument('-l', '--logfile', help='path to log file (log to stderr by default)')
    parser.add_argument('-m', '--mode', choices=['batch', 'stream'], default='stream', help='processing mode')
    parser.add_argument('-d', '--dsn', default='dbname=repology user=repology password=repology', help='database connection params')

    parser.add_argument('-i', '--init', action='store_true', help='(re)init the database by (re)creating all tables')

    parser.add_argument('-S', '--no-shadow', action='store_true', help='treat shadow repositories as normal')

    parser.add_argument('reponames', metavar='repo|tag', nargs='*', help='repository or tag name to process')
    options = parser.parse_args()

    if not options.reponames:
        options.reponames = ["all"]

    logger = StderrLogger()
    if options.logfile:
        logger = FileLogger(options.logfile)

    repoman = RepositoryManager(options.statedir)
    filters = [] if options.no_shadow else [ShadowFilter()]

    logger.Log("connecting to database...")
    database = Database(options.dsn)
    if options.init:
        logger.Log("(re)initializing the database...")
        database.CreateSchema()
    database.Clear()

    package_queue = []

    def PackageProcessor(packageset):
        nonlocal package_queue
        FillPackagesetVersions(packageset)
        package_queue.extend(packageset)

        if len(package_queue) >= 1000:
            database.AddPackages(package_queue)
            package_queue = []

    if options.mode == 'stream':
        logger.Log("pushing packages to database...")
        repoman.StreamDeserializeMulti(processor=PackageProcessor, reponames=options.reponames)
    else:
        logger.Log("loading packages...")
        all_packages = repoman.DeserializeMulti(reponames=options.reponames, logger=logger)
        logger.Log("merging packages...")
        metapackages = MergeMetapackages(all_packages)
        logger.Log("pushing packages to database...")
        for metaname, packages in sorted(metapackages.items()):
            PackageProcessor(packages)

    # process what's left in the queue
    database.AddPackages(package_queue)

    logger.Log("updating views...")
    database.UpdateViews()

    logger.Log("committing changes...")
    database.Commit()

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
