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
from repology.packageproc import FillPackagesetVersions
from repology.logger import *


def ProcessRepositories(options, logger, repoman, transformer):
    repositories_updated = []
    repositories_not_updated = []

    for reponame in repoman.GetNames(reponames=options.reponames):
        repo_logger = logger.GetPrefixed(reponame + ": ")
        repo_logger.Log("started")
        try:
            if options.fetch:
                repoman.Fetch(reponame, update=(options.fetch >= 2), logger=repo_logger.GetIndented())
            if options.parse:
                repoman.ParseAndSerialize(reponame, transformer=transformer, logger=repo_logger.GetIndented())
            elif options.reprocess:
                repoman.Reprocess(reponame, transformer=transformer, logger=repo_logger.GetIndented())
        except KeyboardInterrupt:
            logger.Log("interrupted")
            return 1
        except:
            repo_logger.Log("failed, exception follows")
            for item in traceback.format_exception(*sys.exc_info()):
                for line in item.split('\n'):
                    if line:
                        repo_logger.GetIndented().Log(line)
            repositories_not_updated.append(reponame)
        else:
            repo_logger.Log("complete")
            repositories_updated.append(reponame)

    logger.Log("{}/{} repositories processed successfully".format(len(repositories_updated), len(repositories_updated) + len(repositories_not_updated)))
    if repositories_not_updated:
        logger.Log("  failed repositories: {}".format(', '.join(sorted(repositories_not_updated))))

    return repositories_updated, repositories_not_updated


def ProcessDatabase(options, logger, repoman, repositories_updated):
    logger.Log("connecting to database")

    db_logger = logger.GetIndented()

    database = Database(options.dsn, readonly=False)
    if options.database > 1:
        db_logger.Log("(re)initializing database schema")
        database.CreateSchema()
    database.Clear()

    package_queue = []
    num_pushed = 0

    def PackageProcessor(packageset):
        nonlocal package_queue, num_pushed
        FillPackagesetVersions(packageset)
        package_queue.extend(packageset)

        if len(package_queue) >= 1000:
            database.AddPackages(package_queue)
            num_pushed += len(package_queue)
            package_queue = []
            db_logger.Log("  pushed {} packages".format(num_pushed))

    db_logger.Log("pushing packages to database")
    repoman.StreamDeserializeMulti(processor=PackageProcessor, reponames=options.reponames)

    # process what's left in the queue
    database.AddPackages(package_queue)

    if options.fetch >= 2 and options.parse:
        db_logger.Log("recording repo updates")
        database.MarkRepositoriesUpdated(repositories_updated)
    else:
        db_logger.Log("not recording repo updates, need fetch + update + parse")

    db_logger.Log("updating views")
    database.UpdateViews()

    db_logger.Log("committing changes")
    database.Commit()

    logger.Log("database processing complete")


def ShowUnmatchedRules(options, logger, transformer):
    if (options.parse or options.reprocess) and (options.unmatched_rules):
        unmatched = transformer.GetUnmatchedRules()
        if len(unmatched):
            wlogger = logger.GetPrefixed("WARNING: ")
            wlogger.Log("unmatched rules detected!")

            for rule in unmatched:
                wlogger.Log(rule)


def Main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--statedir', default='_state', help='path to directory with repository state')
    parser.add_argument('-l', '--logfile', help='path to log file (log to stderr by default)')
    parser.add_argument('-U', '--rules', default='rules.yaml', help='path to name transformation rules yaml')
    parser.add_argument('-D', '--dsn', default='dbname=repology user=repology password=repology', help='database connection params')

    actions_grp = parser.add_argument_group('Actions')
    actions_grp.add_argument('-f', '--fetch', action='count', help='allow fetching repository data (twice to also update)')
    actions_grp.add_argument('-p', '--parse', action='store_true', help='parse, process and serialize repository data')

    # XXX: this is dangerous as long as ignored packages are removed from dumps
    actions_grp.add_argument('-P', '--reprocess', action='store_true', help='reprocess repository data')
    actions_grp.add_argument('-d', '--database', action='count', help='store in the database (twice to reinit the database)')

    actions_grp.add_argument('-u', '--unmatched-rules', action='store_true', help='show unmatched rules when parsing')

    parser.add_argument('reponames', metavar='repo|tag', nargs='*', help='repository or tag name to process')
    options = parser.parse_args()

    if not options.reponames:
        options.reponames = ["all"]

    logger = StderrLogger()
    if options.logfile:
        logger = FileLogger(options.logfile)

    repoman = RepositoryManager(options.statedir)
    transformer = PackageTransformer(options.rules)

    repositories_updated, repositories_not_updated = ProcessRepositories(options=options, logger=logger, repoman=repoman, transformer=transformer)
    if options.database:
        ProcessDatabase(options=options, logger=logger, repoman=repoman, repositories_updated=repositories_updated)
    ShowUnmatchedRules(options=options, logger=logger, transformer=transformer)

    return 1 if repositories_not_updated else 0

if __name__ == '__main__':
    os.sys.exit(Main())
