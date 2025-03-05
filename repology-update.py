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
from typing import Any, Callable, Iterable, TypeVar

from repology.config import config
from repology.database import Database
from repology.dblogger import LogRunManager
from repology.logger import FileLogger, Logger, StderrLogger
from repology.maintainermgr import MaintainerManager
from repology.querymgr import QueryManager
from repology.repomgr import RepositoryManager
from repology.repoproc import RepositoryProcessor
from repology.transformer import PackageTransformer
from repology.transformer.ruleset import Ruleset
from repology.update import UpdateProcess
from repology.yamlloader import ParsedConfigCache, YamlConfig


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
    def get_parsed_config_cache(self) -> ParsedConfigCache | None:
        return ParsedConfigCache(self.options.config_cache) if self.options.config_cache else None

    @cached_method
    def get_logging_database_connection(self) -> Database:
        return Database(self.options.dsn, self.get_query_manager(), readonly=False, autocommit=True, application_name='repology-update-logging')

    @cached_method
    def get_repos_config(self) -> YamlConfig:
        return YamlConfig.from_path(self.options.repos_dir, self.get_parsed_config_cache())

    @cached_method
    def get_repo_manager(self) -> RepositoryManager:
        return RepositoryManager(self.get_repos_config())

    @cached_method
    def get_repo_processor(self) -> RepositoryProcessor:
        return RepositoryProcessor(self.get_repo_manager(), self.options.statedir, self.options.parseddir, safety_checks=self.options.enable_safety_checks)

    @cached_method
    def get_rules_config(self) -> YamlConfig:
        return YamlConfig.from_path(self.options.rules_dir, self.get_parsed_config_cache())

    @cached_method
    def get_ruleset(self) -> Ruleset:
        return Ruleset(self.get_rules_config())

    @cached_method
    def get_enabled_repo_names(self) -> list[str]:
        return self.get_repo_manager().get_names(self.options.enabled_repositories)

    @cached_method
    def get_processable_repo_names(self) -> list[str]:
        enabled = set(self.get_enabled_repo_names())
        return [reponame for reponame in self.get_repo_manager().get_names(self.options.reponames) if reponame in enabled]

    @cached_method
    def get_main_logger(self) -> Logger:
        return FileLogger(self.options.logfile) if self.options.logfile else StderrLogger()

    @cached_method
    def get_maintainers_config(self) -> YamlConfig:
        return YamlConfig.from_path(self.options.maintainers_config, self.get_parsed_config_cache())

    @cached_method
    def get_maintainer_manager(self) -> MaintainerManager:
        return MaintainerManager(self.get_maintainers_config())

    def get_options(self) -> argparse.Namespace:
        return self.options


def process_repositories(env: Environment) -> None:
    database = env.get_main_database_connection()

    for reponame in env.get_processable_repo_names():
        repository = env.get_repo_manager().get_repository(reponame)

        update_period = repository.update_period
        since_last_fetched = database.get_repository_since_last_fetched(reponame)

        skip_fetch = since_last_fetched is not None and since_last_fetched < update_period

        if env.get_options().fetch and skip_fetch:
            env.get_main_logger().log(f'not fetching {reponame} to honor update period ({update_period - since_last_fetched} left)'.format(reponame))
        elif env.get_options().fetch:
            env.get_main_logger().log('fetching {}'.format(reponame))

            # make sure hash is reset until it's known that the update did not untroduce any changes
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

            database.mark_repository_fetched(reponame)
            database.commit()

        if env.get_options().parse:
            ruleset = env.get_ruleset()

            ruleset_hash_changed = ruleset.get_hash() != database.get_repository_ruleset_hash(reponame)

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
                transformer = PackageTransformer(ruleset, reponame, repository.ruleset)
                maintainermgr = env.get_maintainer_manager()

                with LogRunManager(env.get_logging_database_connection(), reponame, 'parse') as runlogger:
                    env.get_repo_processor().parse([reponame], transformer=transformer, maintainermgr=maintainermgr, logger=runlogger)

                env.get_main_logger().get_indented().log('done')

                transformer.finalize()
            except KeyboardInterrupt:
                raise
            except Exception as e:
                env.get_main_logger().get_indented().log('failed: ' + str(e), severity=Logger.ERROR)
                if env.get_options().fatal:
                    raise

            database.update_repository_ruleset_hash(reponame, ruleset.get_hash())
            database.mark_repository_parsed(reponame)
            database.commit()


def database_init(env: Environment) -> None:
    logger = env.get_main_logger()
    database = env.get_main_database_connection()

    logger.log('(re)initializing database schema')
    database.create_schema_types()
    database.create_schema_functions()
    database.create_schema_tables()

    logger.get_indented().log('committing changes')
    database.commit()


def update_repositories(env: Environment) -> None:
    logger = env.get_main_logger()
    database = env.get_main_database_connection()

    logger.log('updating repositories metadata')

    config_repos = env.get_repo_manager().get_repositories(env.get_enabled_repo_names())
    db_repos = database.get_repositories_statuses()

    new_reponames = set(repo.name for repo in config_repos) - set(repo['name'] for repo in db_repos)
    deprecated_reponames = set(repo['name'] for repo in db_repos if repo['state'] != 'legacy') - set(repo.name for repo in config_repos)

    for repo in config_repos:
        if repo.name in new_reponames:
            database.add_repository(env.get_repo_manager().get_repository_json(repo.name))
        else:
            database.update_repository(env.get_repo_manager().get_repository_json(repo.name))

    for reponame in deprecated_reponames:
        database.deprecate_repository(reponame)

    logger.get_indented().log('committing changes')
    database.commit()


def handle_totals(env: Environment, do_fix: bool) -> None:
    logger = env.get_main_logger()
    database = env.get_main_database_connection()

    logger.log(f'{"fixing" if do_fix else "checking"} totals')

    def list_discrepancies(where: str, discrepancies: Iterable[Any]) -> None:
        count = 0

        for discrepancy in discrepancies:
            if 'key' in discrepancy:
                logger.get_indented().log(f'discrepancy detected in {where} "{discrepancy["key"]}"')
            else:
                logger.get_indented().log(f'discrepancy detected in {where}')

            if discrepancy['expected'] is None:
                logger.get_indented().get_indented().log('entry not expected')
                continue

            common_keys = set(discrepancy['actual'].keys()) & set(discrepancy['expected'].keys())
            for key in sorted(common_keys):
                actual = discrepancy['actual'].get(key)
                expected = discrepancy['expected'].get(key)

                if actual != expected:
                    logger.get_indented().get_indented().log(f'{key}: "{actual}" != "{expected}"')

            count += 1

        logger.get_indented().log(f'{count or "no"} discrepancies detected in {where}')

    list_discrepancies('repositories', database.totals_repositories(do_fix))
    list_discrepancies('maintainers', database.totals_maintainers(do_fix))
    list_discrepancies('statistics', database.totals_statistics(do_fix))
    list_discrepancies('links', database.totals_links(do_fix))

    database.commit()


def database_update(env: Environment) -> None:
    logger = env.get_main_logger()
    database = env.get_main_database_connection()

    with UpdateProcess(database, logger) as update:
        update.set_history_cutoff_timestamp(env.get_options().history_cutoff_timestamp)

        if not env.get_options().skip_packages:
            update.push_packages(
                env.get_repo_processor().iter_parsed(reponames=env.get_enabled_repo_names(), logger=logger),
                max_updates=env.get_options().max_updates
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


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-S', '--statedir', default=config['STATE_DIR'], help='path to directory with repository state')
    parser.add_argument('-P', '--parseddir', default=config['PARSED_DIR'], help='path to directory with parsed repository data')
    parser.add_argument('-L', '--logfile', help='path to log file (log to stderr by default)')
    parser.add_argument('-E', '--repos-dir', default=config['REPOS_DIR'], help='path to directory with repository configs')
    parser.add_argument('-U', '--rules-dir', default=config['RULES_DIR'], help='path to directory with rules')
    parser.add_argument('-Q', '--sql-dir', default=config['SQL_DIR'], help='path to directory with sql queries')
    parser.add_argument('-D', '--dsn', default=config['DSN'], help='database connection params')
    parser.add_argument('--enabled-repositories', default=config['REPOSITORIES'], metavar='repo|group', nargs='*', help='own or group name(s) of repositories which are enabled and shown in repology')
    parser.add_argument('--config-cache', default=config['CONFIG_CACHE_DIR'], help='path to directory for caching parsed repository and rule data')
    parser.add_argument('--maintainers-config', default=config['MAINTAINERS_CONFIG'], help='path to maintainers.yaml')

    grp = parser.add_argument_group('Initialization actions (destructive!)')
    grp.add_argument('-i', '--initdb', action='store_true', help='(re)initialize database schema')

    grp = parser.add_argument_group('Update actions')
    grp.add_argument('-f', '--fetch', action='count', help='fetch repository data (twice to allow updating)')
    grp.add_argument('-p', '--parse', action='count', help="parse fetched repository data (specify twice to parse even if the fetched data hasn't changed)")
    grp.add_argument('-d', '--database', action='count', help='store in the database (twice to update even if no package changes)')
    grp.add_argument('-o', '--postupdate', action='store_true', help='perform post-update actions')

    grp = parser.add_argument_group('Extra update actions')
    grp.add_argument('-R', '--repositories', action='store_true', help='update repositories')
    grp.add_argument('--check-totals', action='store_true', help='check total counts')
    grp.add_argument('--fix-totals', action='store_true', help='fix total counts')

    grp = parser.add_argument_group('Informational queries')
    grp.add_argument('-l', '--list', action='store_true', help='list repositories repology will work on')
    grp.add_argument('--dump-repositories', action='store_true', help='dump parsed repositories config')
    grp.add_argument('--dump-rules', action='store_true', help='dump parsed rules config')

    grp = parser.add_argument_group('Flags')
    grp.add_argument('--enable-safety-checks', action='store_true', dest='enable_safety_checks', default=config['ENABLE_SAFETY_CHECKS'], help='enable safety checks on processed repository data')
    grp.add_argument('--disable-safety-checks', action='store_false', dest='enable_safety_checks', default=not config['ENABLE_SAFETY_CHECKS'], help='disable safety checks on processed repository data')
    grp.add_argument('--skip-packages', action='store_true', help='skip pushing updated packages, but run update code')
    grp.add_argument('--history-cutoff-timestamp', default=config['HISTORY_CUTOFF_TIMESTAMP'], help='timestamp before which history is untrusted')

    grp.add_argument('--fatal', action='store_true', help='treat single repository processing failure as fatal')

    grp.add_argument('--max-updates', type=int, help='maximal number of project updates to perform')

    parser.add_argument('reponames', default=config['REPOSITORIES'], metavar='repo|group', nargs='*', help='own or group name(s) of repositories to process')

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
        env.get_ruleset()

    if options.fetch or options.parse or options.database or options.repositories:
        update_repositories(env)

    if options.fetch or options.parse:
        process_repositories(env)

    if options.database:
        database_update(env)

    if options.postupdate:
        database_update_post(env)

    if options.check_totals or options.fix_totals:
        handle_totals(env, options.fix_totals)

    if options.dump_repositories:
        print(env.get_repos_config().dump())

    if options.dump_rules:
        print(env.get_rules_config().dump())

    env.get_main_logger().log('total time taken: {:.2f} seconds'.format((timer() - start)))

    return 0


if __name__ == '__main__':
    sys.exit(main())
