# Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from collections import defaultdict
from typing import Dict, Iterable, List

from repology.database import Database
from repology.fieldstats import FieldStatistics
from repology.logger import Logger
from repology.package import Package
from repology.packageproc import fill_packageset_versions
from repology.update.changes import ProjectsChangeStatistics, RemovedProject, UpdatedProject, iter_changed_projects
from repology.update.hashes import iter_project_hashes


class ChangedProjectsAccumulator:
    _BATCH_SIZE = 1000

    _database: Database
    _effnames: List[str]

    def __init__(self, database: Database) -> None:
        self._database = database
        self._effnames = []

    def add(self, effname: str) -> None:
        self._effnames.append(effname)

        if len(self._effnames) >= ChangedProjectsAccumulator._BATCH_SIZE:
            self.flush()

    def flush(self) -> None:
        if self._effnames:
            self._database.queue_project_changes(self._effnames)
            self._effnames = []


def update_project(database: Database, change: UpdatedProject) -> None:
    fill_packageset_versions(change.packages)

    database.add_packages(change.packages)

    database.update_project_hash(change.effname, change.hash)


def remove_project(database: Database, change: RemovedProject) -> None:
    database.remove_project_hash(change.effname)


def update_repology(database: Database, projects: Iterable[List[Package]], logger: Logger) -> None:
    logger.log('starting the update')
    database.update_start()

    logger.log('updating projects')

    field_stats_per_repo: Dict[str, FieldStatistics] = defaultdict(FieldStatistics)

    prev_total = 0
    stats = ProjectsChangeStatistics()

    changed_projects = ChangedProjectsAccumulator(database)

    for change in iter_changed_projects(iter_project_hashes(database), projects, stats):
        if isinstance(change, UpdatedProject):
            update_project(database, change)

            for package in change.packages:
                field_stats_per_repo[package.repo].add(package)

        elif isinstance(change, RemovedProject):
            remove_project(database, change)

        changed_projects.add(change.effname)

        if stats.total - prev_total >= 10000 or prev_total == 0:
            logger.log(f'  at "{change.effname}": {stats}')
            prev_total = stats.total

    changed_projects.flush()
    logger.log(f'  done: {stats}')

    # Fraction picked experimentally: at change size of around 100k of 400k projects
    # time of partial update of most binding tables approaches or exceeds full update
    # time. In fact this doesn't matter much, as general update is arond 0.001 (0.1%),
    # and a few cases of > 0.01 (1%) are when new repositories are added, othewise it's
    # 1 (100%) when Package format changes or when database is filled for the first time.
    enable_partial = stats.change_fraction < 0.25

    # This was picked randomly
    enable_analyze = stats.change_fraction > 0.05

    logger.log('updating field statistics')
    for repo, field_stats in field_stats_per_repo.items():
        database.update_repository_used_package_fields(repo, field_stats.get_used_fields())

    logger.log('updating project events')
    database.update_project_events()

    logger.log('updating links')
    database.update_links()

    # Note: before this, packages table still contains old versions of packages,
    # while new versions reside in incoming_packages temporary table
    logger.log('applying updated packages')
    database.update_apply_packages(enable_partial, enable_analyze)
    # Note: after this, packages table contain new versions of packages

    logger.log('updating metapackages')
    database.update_metapackages()

    logger.log('updating repositories')
    database.update_repositories()

    logger.log('updating maintainers')
    database.update_maintainers()

    logger.log('updating binding table repo_metapackages')
    database.update_binding_repo_metapackages(enable_partial, enable_analyze)

    logger.log('updating binding table category_metapackages')
    database.update_binding_category_metapackages(enable_partial, enable_analyze)

    logger.log('updating binding table maintainer_metapackages')
    database.update_binding_maintainer_metapackages(enable_partial, enable_analyze)

    logger.log('updating binding table maintainer_and_repo_metapackages')
    database.update_binding_maintainer_and_repo_metapackages(enable_partial, enable_analyze)

    logger.log('updating url relations')
    database.update_url_relations()

    logger.log('updating projects has_related flag')
    database.update_projects_has_related()

    logger.log('updating problems')
    database.update_problems()

    logger.log('updating statistics')
    database.update_statistics()

    logger.log('updating histories')
    database.update_histories()

    logger.log('finalizing the update')
    database.update_finish()
