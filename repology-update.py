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
import traceback
from timeit import default_timer as timer

import repology.config
from repology.database import Database
from repology.logger import *
from repology.packageproc import FillPackagesetVersions
from repology.repoman import RepositoryManager
from repology.transformer import PackageTransformer


def ProcessRepositories(options, logger, repoman, transformer):
    repositories_updated = []
    repositories_not_updated = []

    for reponame in repoman.GetNames(reponames=options.reponames):
        repo_logger = logger.GetPrefixed(reponame + ': ')
        repo_logger.Log('started')
        try:
            if options.fetch:
                repoman.Fetch(reponame, update=options.update, logger=repo_logger.GetIndented())
            if options.parse:
                repoman.ParseAndSerialize(reponame, transformer=transformer, logger=repo_logger.GetIndented())
            elif options.reprocess:
                repoman.Reprocess(reponame, transformer=transformer, logger=repo_logger.GetIndented())
        except KeyboardInterrupt:
            logger.Log('interrupted')
            return 1
        except:
            repo_logger.Log('failed, exception follows')
            for item in traceback.format_exception(*sys.exc_info()):
                for line in item.split('\n'):
                    if line:
                        repo_logger.GetIndented().Log(line)
            repositories_not_updated.append(reponame)
        else:
            repo_logger.Log('complete')
            repositories_updated.append(reponame)

    logger.Log('{}/{} repositories processed successfully'.format(len(repositories_updated), len(repositories_updated) + len(repositories_not_updated)))
    if repositories_not_updated:
        logger.Log('  failed repositories: {}'.format(', '.join(sorted(repositories_not_updated))))

    return repositories_updated, repositories_not_updated


def ProcessDatabase(options, logger, repoman, repositories_updated):
    logger.Log('connecting to database')

    db_logger = logger.GetIndented()

    database = Database(options.dsn, readonly=False)
    if options.initdb:
        db_logger.Log('(re)initializing database schema')
        database.CreateSchema()

        db_logger.Log('committing changes')
        database.Commit()

    if options.database:
        db_logger.Log('clearing the database')
        database.Clear()

        package_queue = []
        num_pushed = 0

        def PackageProcessor(packageset):
            nonlocal package_queue, num_pushed
            FillPackagesetVersions(packageset)
            package_queue.extend(packageset)

            if len(package_queue) >= 10000:
                database.AddPackages(package_queue)
                num_pushed += len(package_queue)
                package_queue = []
                db_logger.Log('  pushed {} packages'.format(num_pushed))

        db_logger.Log('pushing packages to database')
        repoman.StreamDeserializeMulti(processor=PackageProcessor, reponames=options.reponames)

        # process what's left in the queue
        database.AddPackages(package_queue)

        if options.fetch and options.update and options.parse:
            db_logger.Log('recording repo updates')
            database.MarkRepositoriesUpdated(repositories_updated)
        else:
            db_logger.Log('not recording repo updates, need --fetch --update --parse')

        db_logger.Log('updating views')
        database.UpdateViews()
        database.ExtractLinks()

        db_logger.Log('updating history')
        database.SnapshotHistory()

        db_logger.Log('committing changes')
        database.Commit()

    logger.Log('database processing complete')


def ShowUnmatchedRules(options, logger, transformer, reliable):
    unmatched = transformer.GetUnmatchedRules()
    if len(unmatched):
        wlogger = logger.GetPrefixed('WARNING: ')
        wlogger.Log('unmatched rules detected!')
        if not reliable:
            wlogger.Log('this information is not reliable because not all repositories were updated!')

        for rule in unmatched:
            wlogger.Log(rule)


def Main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-S', '--statedir', default=repology.config.STATE_DIR, help='path to directory with repository state')
    parser.add_argument('-L', '--logfile', help='path to log file (log to stderr by default)')
    parser.add_argument('-E', '--repos-dir', default=repology.config.REPOS_DIR, help='path to directory with repository configs')
    parser.add_argument('-U', '--rules-dir', default=repology.config.RULES_DIR, help='path to directory with rules')
    parser.add_argument('-D', '--dsn', default=repology.config.DSN, help='database connection params')

    actions_grp = parser.add_argument_group('Actions')
    actions_grp.add_argument('-l', '--list', action='store_true', help='list repositories repology will work on')

    actions_grp.add_argument('-f', '--fetch', action='store_true', help='fetching repository data')
    actions_grp.add_argument('-u', '--update', action='store_true', help='when fetching, allow updating (otherwise, only fetch once)')
    actions_grp.add_argument('-p', '--parse', action='store_true', help='parse, process and serialize repository data')

    # XXX: this is dangerous as long as ignored packages are removed from dumps
    actions_grp.add_argument('-P', '--reprocess', action='store_true', help='reprocess repository data')
    actions_grp.add_argument('-i', '--initdb', action='store_true', help='(re)initialize database schema')
    actions_grp.add_argument('-d', '--database', action='store_true', help='store in the database')

    actions_grp.add_argument('-r', '--show-unmatched-rules', action='store_true', help='show unmatched rules when parsing')

    parser.add_argument('reponames', default=repology.config.REPOSITORIES, metavar='repo|tag', nargs='*', help='repository or tag name to process')
    options = parser.parse_args()

    repoman = RepositoryManager(options.repos_dir, options.statedir)

    if options.list:
        print('\n'.join(sorted(repoman.GetNames(reponames=options.reponames))))
        return 0

    transformer = PackageTransformer(options.rules_dir)

    logger = StderrLogger()
    if options.logfile:
        logger = FileLogger(options.logfile)

    repositories_updated = []
    repositories_not_updated = []

    start = timer()
    if options.fetch or options.parse or options.reprocess:
        repositories_updated, repositories_not_updated = ProcessRepositories(options=options, logger=logger, repoman=repoman, transformer=transformer)

    if options.initdb or options.database:
        ProcessDatabase(options=options, logger=logger, repoman=repoman, repositories_updated=repositories_updated)

    if (options.parse or options.reprocess) and (options.show_unmatched_rules):
        ShowUnmatchedRules(options=options, logger=logger, transformer=transformer, reliable=repositories_not_updated == [])

    logger.Log('total time taken: {:.2f} seconds'.format((timer() - start)))

    return 1 if repositories_not_updated else 0


if __name__ == '__main__':
    os.sys.exit(Main())
