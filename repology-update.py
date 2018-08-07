#!/usr/bin/env python3
#
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

import argparse
import os
from timeit import default_timer as timer

from repology.config import config
from repology.database import Database
from repology.dblogger import LogRunManager
from repology.logger import FileLogger, Logger, StderrLogger
from repology.packageproc import FillPackagesetVersions
from repology.querymgr import QueryManager
from repology.repomgr import RepositoryManager
from repology.repoproc import RepositoryProcessor
from repology.transformer import PackageTransformer


def cached_method(method):
    def wrapper(self, *args, **kwargs):
        name = '_' + method.__name__ + '_state'

        res = getattr(self, name, None)
        if res is None:
            res = method(self, *args, **kwargs)
            setattr(self, name, res)

        return res

    return wrapper


class Environment:
    def __init__(self, options):
        self.options = options

    @cached_method
    def get_query_manager(self):
        return QueryManager(self.options.sql_dir)

    @cached_method
    def get_main_database_connection(self):
        return Database(self.options.dsn, self.get_query_manager(), readonly=False, application_name='repology-update')

    @cached_method
    def get_logging_database_connection(self):
        return Database(self.options.dsn, self.get_query_manager(), readonly=False, autocommit=True, application_name='repology-update-logging')

    @cached_method
    def get_repo_manager(self):
        return RepositoryManager(self.options.repos_dir)

    @cached_method
    def get_repo_processor(self):
        return RepositoryProcessor(self.get_repo_manager(), self.options.statedir, safety_checks=self.options.enable_safety_checks)

    @cached_method
    def get_package_transformer(self):
        return PackageTransformer(self.get_repo_manager(), self.options.rules_dir)

    @cached_method
    def get_enabled_repo_names(self):
        return self.get_repo_manager().GetNames(reponames=self.options.enabled_repositories)

    @cached_method
    def get_processable_repo_names(self):
        enabled = set(self.get_enabled_repo_names())
        return [reponame for reponame in self.get_repo_manager().GetNames(reponames=self.options.reponames) if reponame in enabled]

    @cached_method
    def get_main_logger(self):
        return FileLogger(self.options.logfile) if self.options.logfile else StderrLogger()

    def get_options(self):
        return self.options


def process_repositories(env):
    for reponame in env.get_processable_repo_names():
        env.get_main_logger().log('processing {}'.format(reponame))

        try:
            if env.get_options().fetch:
                with LogRunManager(env, reponame, 'fetch') as logger:
                    env.get_repo_processor().Fetch(reponame, update=env.get_options().update, logger=logger)
            if env.get_options().parse:
                with LogRunManager(env, reponame, 'parse') as logger:
                    env.get_repo_processor().ParseAndSerialize(reponame, transformer=env.get_package_transformer(), logger=logger)

            env.get_main_logger().log('processing {} done'.format(reponame))
        except KeyboardInterrupt:
            raise
        except:
            env.get_main_logger().log('processing {} failed'.format(reponame), severity=Logger.ERROR)
            pass


def database_init(env):
    logger = env.get_main_logger()
    database = env.get_main_database_connection()

    logger.log('(re)initializing database schema')
    database.create_schema()

    logger.get_indented().log('committing changes')
    database.commit()


def database_update_pre(env):
    logger = env.get_main_logger()
    database = env.get_main_database_connection()

    logger.log('updating repositories metadata')
    database.deprecate_repositories()
    database.add_repositories(env.get_repo_manager().GetMetadatas(env.get_enabled_repo_names()))

    logger.get_indented().log('committing changes')
    database.commit()


def database_update(env):
    logger = env.get_main_logger()
    database = env.get_main_database_connection()

    logger.log('clearing the database')
    database.update_start()

    package_queue = []
    num_pushed = 0
    start_time = timer()

    def package_processor(packageset):
        nonlocal package_queue, num_pushed, start_time
        FillPackagesetVersions(packageset)
        package_queue.extend(packageset)

        if len(package_queue) >= 10000:
            database.add_packages(package_queue)
            num_pushed += len(package_queue)
            package_queue = []
            logger.get_indented().log('pushed {} packages, {:.2f} packages/second'.format(num_pushed, num_pushed / (timer() - start_time)))

    logger.log('pushing packages to database')
    env.get_repo_processor().StreamDeserializeMulti(processor=package_processor, reponames=env.get_enabled_repo_names(), logger=logger)

    # process what's left in the queue
    database.add_packages(package_queue)

    logger.log('updating views')
    database.update_finish()

    logger.log('committing changes')
    database.commit()


def database_update_post(env):
    logger = env.get_main_logger()
    database = env.get_main_database_connection()

    logger.log('performing database post-update actions')
    database.update_post()

    logger.get_indented().log('committing changes')
    database.commit()


def show_unmatched_rules(env):
    unmatched = env.get_package_transformer().GetUnmatchedRules()
    if not unmatched:
        return

    logger = env.get_main_logger()
    logger.log('unmatched rules detected!', severity=Logger.WARNING)

    for rule in unmatched:
        logger.log(rule, severity=Logger.WARNING)


def parse_arguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-S', '--statedir', default=config['STATE_DIR'], help='path to directory with repository state')
    parser.add_argument('-L', '--logfile', help='path to log file (log to stderr by default)')
    parser.add_argument('-E', '--repos-dir', default=config['REPOS_DIR'], help='path to directory with repository configs')
    parser.add_argument('-U', '--rules-dir', default=config['RULES_DIR'], help='path to directory with rules')
    parser.add_argument('-Q', '--sql-dir', default=config['SQL_DIR'], help='path to directory with sql queries')
    parser.add_argument('-D', '--dsn', default=config['DSN'], help='database connection params')
    parser.add_argument('--enabled-repositories', default=config['REPOSITORIES'], metavar='repo|tag', nargs='*', help='repository or tag name(s) which are enabled and shown in repology')

    actions_grp = parser.add_argument_group('Actions')
    actions_grp.add_argument('-l', '--list', action='store_true', help='list repositories repology will work on')

    actions_grp.add_argument('-f', '--fetch', action='store_true', help='fetching repository data')
    actions_grp.add_argument('-u', '--update', action='store_true', help='when fetching, allow updating (otherwise, only fetch once)')
    actions_grp.add_argument('-p', '--parse', action='store_true', help='parse, process and serialize repository data')

    # XXX: this is dangerous as long as ignored packages are removed from dumps
    actions_grp.add_argument('-i', '--initdb', action='store_true', help='(re)initialize database schema')
    actions_grp.add_argument('-d', '--database', action='store_true', help='store in the database')
    actions_grp.add_argument('-o', '--postupdate', action='store_true', help='perform post-update actions')

    actions_grp.add_argument('-r', '--show-unmatched-rules', action='store_true', help='show unmatched rules when parsing')

    flags_grp = parser.add_argument_group('Flags')
    flags_grp.add_argument('--enable-safety-checks', action='store_true', dest='enable_safety_checks', default=config['ENABLE_SAFETY_CHECKS'], help='enable safety checks on processed repository data')
    flags_grp.add_argument('--disable-safety-checks', action='store_false', dest='enable_safety_checks', default=not config['ENABLE_SAFETY_CHECKS'], help='disable safety checks on processed repository data')

    parser.add_argument('reponames', default=config['REPOSITORIES'], metavar='repo|tag', nargs='*', help='repository or tag name(s) to process')

    return parser.parse_args()


def main():
    options = parse_arguments()

    env = Environment(options)

    if options.list:
        print('\n'.join(env.get_processable_repo_names()))
        return 0

    start = timer()

    if options.initdb:
        database_init(env)

    if options.parse:
        # preload them here, otherwise they will lazy load at the start of first repo parsing,
        # and this will look loke a hang, and parse run duration will be incorrect
        env.get_main_logger().log('loading rules')
        env.get_repo_processor()

    if options.fetch or options.parse or options.database or options.postupdate:
        database_update_pre(env)

    if options.fetch or options.parse:
        process_repositories(env)

    if options.database:
        database_update(env)

    if options.postupdate:
        database_update_post(env)

    if options.show_unmatched_rules:
        show_unmatched_rules(env)

    env.get_main_logger().log('total time taken: {:.2f} seconds'.format((timer() - start)))

    return 0


if __name__ == '__main__':
    os.sys.exit(main())
