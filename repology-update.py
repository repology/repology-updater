#!/usr/bin/env python3
#
# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import sys
from timeit import default_timer as timer
from typing import Any, Callable, List, TypeVar

from repology.config import config
from repology.database import Database
from repology.dblogger import LogRunManager
from repology.logger import FileLogger, Logger, StderrLogger
from repology.querymgr import QueryManager
from repology.repomgr import RepositoryManager
from repology.repoproc import RepositoryProcessor
from repology.transformer import PackageTransformer
from repology.update import update_repology


T = TypeVar('T')


def cached_method(method: Callable[..., T]) -> Callable[..., T]:
    def wrapper(self: 'Environment', *args: Any, **kwargs: Any) -> Any:
        name = '_' + method.__name__ + '_state'

        res = getattr(self, name, None)
        if res is None:
            res = method(self, *args, **kwargs)
            setattr(self, name, res)

        return res

    return wrapper


class Environment:
    options: argparse.Namespace

    def __init__(self, options: argparse.Namespace) -> None:
        self.options = options

    @cached_method
    def get_query_manager(self) -> QueryManager:
        return QueryManager(self.options.sql_dir)

    @cached_method
    def get_main_database_connection(self) -> Database:
        return Database(self.options.dsn, self.get_query_manager(), readonly=False, application_name='repology-update')

    @cached_method
    def get_logging_database_connection(self) -> Database:
        return Database(self.options.dsn, self.get_query_manager(), readonly=False, autocommit=True, application_name='repology-update-logging')

    @cached_method
    def get_repo_manager(self) -> RepositoryManager:
        return RepositoryManager(self.options.repos_dir)

    @cached_method
    def get_repo_processor(self) -> RepositoryProcessor:
        return RepositoryProcessor(self.get_repo_manager(), self.options.statedir, self.options.parseddir, safety_checks=self.options.enable_safety_checks)

    @cached_method
    def get_package_transformer(self) -> PackageTransformer:
        return PackageTransformer(self.get_repo_manager(), self.options.rules_dir)

    @cached_method
    def get_enabled_repo_names(self) -> List[str]:
        return self.get_repo_manager().get_names(reponames=self.options.enabled_repositories)

    @cached_method
    def get_processable_repo_names(self) -> List[str]:
        enabled = set(self.get_enabled_repo_names())
        return [reponame for reponame in self.get_repo_manager().get_names(reponames=self.options.reponames) if reponame in enabled]

    @cached_method
    def get_main_logger(self) -> Logger:
        return FileLogger(self.options.logfile) if self.options.logfile else StderrLogger()

    def get_options(self) -> argparse.Namespace:
        return self.options


def process_repositories(env: Environment) -> None:
    database = env.get_main_database_connection()

    for reponame in env.get_processable_repo_names():
        if env.get_options().fetch:
            env.get_main_logger().log('fetching {}'.format(reponame))

            # make sure hash is reset untill it's known that the update did not untroduce any changes
            old_hash = database.get_repository_ruleset_hash(reponame)
            database.update_repository_ruleset_hash(reponame, None)
            database.commit()

            allow_update = env.get_options().fetch >= 1

            have_changes = False

            try:
                with LogRunManager(env.get_logging_database_connection(), reponame, 'fetch') as runlogger:
                    have_changes = env.get_repo_processor().fetch([reponame], update=allow_update, logger=runlogger)
                    if not have_changes:
                        runlogger.set_no_changes()

                env.get_main_logger().get_indented().log('done' + ('' if have_changes else ' (no changes)'))
            except KeyboardInterrupt:
                raise
            except Exception as e:
                env.get_main_logger().get_indented().log('failed: ' + str(e), severity=Logger.ERROR)
                if env.get_options().fatal:
                    raise

            if not have_changes:
                database.update_repository_ruleset_hash(reponame, old_hash)
                database.commit()

        if env.get_options().parse:
            transformer = env.get_package_transformer()

            ruleset_hash_changed = transformer.get_ruleset_hash() != database.get_repository_ruleset_hash(reponame)

            if ruleset_hash_changed:
                env.get_main_logger().log('parsing {}'.format(reponame))
            elif env.get_options().parse >= 2:
                env.get_main_logger().log('parsing {} (forced)'.format(reponame))
            else:
                env.get_main_logger().log('not parsing {} due to no data changes since last run'.format(reponame))
                continue

            # likewise, make sure hash is reset until the source is successfully reparsed
            database.update_repository_ruleset_hash(reponame, None)
            database.commit()

            try:
                with LogRunManager(env.get_logging_database_connection(), reponame, 'parse') as runlogger:
                    env.get_repo_processor().parse([reponame], transformer=transformer, logger=runlogger)

                env.get_main_logger().get_indented().log('done')
            except KeyboardInterrupt:
                raise
            except Exception as e:
                env.get_main_logger().get_indented().log('failed: ' + str(e), severity=Logger.ERROR)
                if env.get_options().fatal:
                    raise

            database.update_repository_ruleset_hash(reponame, transformer.get_ruleset_hash())
            database.commit()


def database_init(env: Environment) -> None:
    logger = env.get_main_logger()
    database = env.get_main_database_connection()

    logger.log('(re)initializing database schema')
    database.create_schema()

    logger.get_indented().log('committing changes')
    database.commit()


def update_repositories(env: Environment) -> None:
    logger = env.get_main_logger()
    database = env.get_main_database_connection()

    logger.log('updating repositories metadata')

    config_repos = env.get_repo_manager().get_metadatas(env.get_enabled_repo_names())
    db_repos = database.get_repositories_statuses()

    new_reponames = set(repo['name'] for repo in config_repos) - set(repo['name'] for repo in db_repos)
    deprecated_reponames = set(repo['name'] for repo in db_repos if repo['state'] != 'legacy') - set(repo['name'] for repo in config_repos)

    for repo in config_repos:
        if repo['name'] in new_reponames:
            database.add_repository(repo)
        else:
            database.update_repository(repo)

    for reponame in deprecated_reponames:
        database.deprecate_repository(reponame)

    logger.get_indented().log('committing changes')
    database.commit()


def database_update(env: Environment) -> None:
    logger = env.get_main_logger()
    database = env.get_main_database_connection()

    update_repology(
        database=database,
        projects=env.get_repo_processor().iter_parsed(reponames=env.get_enabled_repo_names(), logger=logger),
        logger=logger,
    )

    for reponame in env.get_enabled_repo_names():
        database.mark_repository_updated(reponame)

    logger.log('committing changes')
    database.commit()


def database_update_post(env: Environment) -> None:
    logger = env.get_main_logger()
    database = env.get_main_database_connection()

    logger.log('performing database post-update actions')
    database.update_post()

    logger.get_indented().log('committing changes')
    database.commit()


def dump_rules(env: Environment) -> None:
    statistics = env.get_package_transformer().get_statistics()

    for block in statistics.blocks:
        print('{')
        for rule, checks, matches in block:
            print('    {:7} {:7}  {}'.format(checks, matches, (rule[:80] + '...') if len(rule) > 80 else rule))
        print('}')


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-S', '--statedir', default=config['STATE_DIR'], help='path to directory with repository state')
    parser.add_argument('-P', '--parseddir', default=config['PARSED_DIR'], help='path to directory with parsed repository data')
    parser.add_argument('-L', '--logfile', help='path to log file (log to stderr by default)')
    parser.add_argument('-E', '--repos-dir', default=config['REPOS_DIR'], help='path to directory with repository configs')
    parser.add_argument('-U', '--rules-dir', default=config['RULES_DIR'], help='path to directory with rules')
    parser.add_argument('-Q', '--sql-dir', default=config['SQL_DIR'], help='path to directory with sql queries')
    parser.add_argument('-D', '--dsn', default=config['DSN'], help='database connection params')
    parser.add_argument('--enabled-repositories', default=config['REPOSITORIES'], metavar='repo|tag', nargs='*', help='repository or tag name(s) which are enabled and shown in repology')

    actions_grp = parser.add_argument_group('Actions')
    actions_grp.add_argument('-l', '--list', action='store_true', help='list repositories repology will work on')

    actions_grp.add_argument('-f', '--fetch', action='count', help='fetch repository data (twice to allow updating)')
    actions_grp.add_argument('-p', '--parse', action='count', help="parse fetched repository data (specify twice to parse even if the fetched data hasn't changed)")

    # XXX: this is dangerous as long as ignored packages are removed from dumps
    actions_grp.add_argument('-i', '--initdb', action='store_true', help='(re)initialize database schema')
    actions_grp.add_argument('-d', '--database', action='store_true', help='store in the database')
    actions_grp.add_argument('-o', '--postupdate', action='store_true', help='perform post-update actions')
    actions_grp.add_argument('-R', '--repositories', action='store_true', help='update repositories')

    actions_grp.add_argument('-r', '--dump-rules', action='store_true', help='dump rule statistics')

    flags_grp = parser.add_argument_group('Flags')
    flags_grp.add_argument('--enable-safety-checks', action='store_true', dest='enable_safety_checks', default=config['ENABLE_SAFETY_CHECKS'], help='enable safety checks on processed repository data')
    flags_grp.add_argument('--disable-safety-checks', action='store_false', dest='enable_safety_checks', default=not config['ENABLE_SAFETY_CHECKS'], help='disable safety checks on processed repository data')

    flags_grp.add_argument('--fatal', action='store_true', help='treat single repository processing failure as fatal')

    parser.add_argument('reponames', default=config['REPOSITORIES'], metavar='repo|tag', nargs='*', help='repository or tag name(s) to process')

    return parser.parse_args()


def main() -> int:
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

    if options.fetch or options.parse or options.database or options.postupdate or options.repositories:
        update_repositories(env)

    if options.fetch or options.parse:
        process_repositories(env)

    if options.database:
        database_update(env)

    if options.postupdate:
        database_update_post(env)

    if options.dump_rules:
        dump_rules(env)

    env.get_main_logger().log('total time taken: {:.2f} seconds'.format((timer() - start)))

    return 0


if __name__ == '__main__':
    sys.exit(main())
