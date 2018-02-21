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

from repology.config import config
from repology.database import Database
from repology.logger import *
from repology.packageproc import FillPackagesetVersions
from repology.querymgr import QueryManager
from repology.repoman import RepositoryManager
from repology.repoproc import RepositoryProcessor
from repology.transformer import PackageTransformer


def ProcessRepositories(options, logger, repoproc, transformer, reponames):
    repositories_updated = []
    repositories_not_updated = []

    for reponame in reponames:
        repo_logger = logger.GetPrefixed(reponame + ': ')
        repo_logger.Log('started')
        try:
            if options.fetch:
                repoproc.Fetch(reponame, update=options.update, logger=repo_logger.GetIndented())
            if options.parse:
                repoproc.ParseAndSerialize(reponame, transformer=transformer, logger=repo_logger.GetIndented())
            elif options.reprocess:
                repoproc.Reprocess(reponame, transformer=transformer, logger=repo_logger.GetIndented())
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


def ProcessDatabase(options, logger, repoproc, repositories_updated):
    logger.Log('connecting to database')

    db_logger = logger.GetIndented()

    querymgr = QueryManager(options.sql_dir)
    database = Database(options.dsn, querymgr, readonly=False, application_name='repology-update')
    if options.initdb:
        db_logger.Log('(re)initializing database schema')
        database.create_schema()

        db_logger.Log('committing changes')
        database.commit()

    if options.database:
        db_logger.Log('clearing the database')
        database.update_start()

        package_queue = []
        num_pushed = 0
        start_time = timer()

        def PackageProcessor(packageset):
            nonlocal package_queue, num_pushed, start_time
            FillPackagesetVersions(packageset)
            package_queue.extend(packageset)

            if len(package_queue) >= 10000:
                database.add_packages(package_queue)
                num_pushed += len(package_queue)
                package_queue = []
                db_logger.Log('  pushed {} packages, {:.2f} packages/second'.format(num_pushed, num_pushed / (timer() - start_time)))

        db_logger.Log('pushing packages to database')
        repoproc.StreamDeserializeMulti(processor=PackageProcessor, reponames=options.reponames)

        # process what's left in the queue
        database.add_packages(package_queue)

        if options.fetch and options.update and options.parse:
            db_logger.Log('recording repo updates')
            database.mark_repositories_updated(repositories_updated)
        else:
            db_logger.Log('not recording repo updates, need --fetch --update --parse')

        db_logger.Log('updating views')
        database.update_finish()

        db_logger.Log('committing changes')
        database.commit()

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


def ParseArguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-S', '--statedir', default=config['STATE_DIR'], help='path to directory with repository state')
    parser.add_argument('-L', '--logfile', help='path to log file (log to stderr by default)')
    parser.add_argument('-E', '--repos-dir', default=config['REPOS_DIR'], help='path to directory with repository configs')
    parser.add_argument('-U', '--rules-dir', default=config['RULES_DIR'], help='path to directory with rules')
    parser.add_argument('-Q', '--sql-dir', default=config['SQL_DIR'], help='path to directory with sql queries')
    parser.add_argument('-D', '--dsn', default=config['DSN'], help='database connection params')

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

    parser.add_argument('reponames', default=config['REPOSITORIES'], metavar='repo|tag', nargs='*', help='repository or tag name to process')

    return parser.parse_args()


def Main():
    options = ParseArguments()

    repoman = RepositoryManager(options.repos_dir)
    repoproc = RepositoryProcessor(repoman, options.statedir)

    if options.list:
        print('\n'.join(repoman.GetNames(reponames=options.reponames)))
        return 0

    transformer = PackageTransformer(repoman, options.rules_dir)

    logger = StderrLogger()
    if options.logfile:
        logger = FileLogger(options.logfile)

    repositories_updated = []
    repositories_not_updated = []

    start = timer()
    if options.fetch or options.parse or options.reprocess:
        repositories_updated, repositories_not_updated = ProcessRepositories(options=options, logger=logger, repoproc=repoproc, transformer=transformer, reponames=repoman.GetNames(reponames=options.reponames))

    if options.initdb or options.database:
        ProcessDatabase(options=options, logger=logger, repoproc=repoproc, repositories_updated=repositories_updated)

    if (options.parse or options.reprocess) and (options.show_unmatched_rules):
        ShowUnmatchedRules(options=options, logger=logger, transformer=transformer, reliable=repositories_not_updated == [])

    logger.Log('total time taken: {:.2f} seconds'.format((timer() - start)))

    return 1 if repositories_not_updated else 0


if __name__ == '__main__':
    os.sys.exit(Main())
