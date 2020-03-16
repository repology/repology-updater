# Copyright (C) 2019-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Any, Dict, Iterable, List

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


class UpdateProcess:
    _database: Database
    _logger: Logger

    _enable_partial_update: bool = True
    _enable_explicit_analyze: bool = False
    _history_cutoff_timestamp: int = 0

    def __init__(self, database: Database, logger: Logger) -> None:
        self._database = database
        self._logger = logger

    def _start_update(self) -> None:
        self._logger.log('starting the update')
        self._database.update_start()

    def _push_packages(self, projects: Iterable[List[Package]]) -> None:
        self._logger.log('updating projects')

        field_stats_per_repo: Dict[str, FieldStatistics] = defaultdict(FieldStatistics)
        stats = ProjectsChangeStatistics()

        prev_total = 0

        changed_projects = ChangedProjectsAccumulator(self._database)

        for change in iter_changed_projects(iter_project_hashes(self._database), projects, stats):
            if isinstance(change, UpdatedProject):
                fill_packageset_versions(change.packages)
                self._database.add_packages(change.packages)
                self._database.update_project_hash(change.effname, change.hash_)

                for package in change.packages:
                    field_stats_per_repo[package.repo].add(package)

            elif isinstance(change, RemovedProject):
                self._database.remove_project_hash(change.effname)

            changed_projects.add(change.effname)

            if stats.total - prev_total >= 10000 or prev_total == 0:
                self._logger.log(f'  at "{change.effname}": {stats}')
                prev_total = stats.total

        changed_projects.flush()
        self._logger.log(f'  done: {stats}')

        self._logger.log('updating field statistics')
        for repo, field_stats in field_stats_per_repo.items():
            self._database.update_repository_used_package_fields(repo, field_stats.get_used_fields())

        # Fraction picked experimentally: at change size of around 100k of 400k projects
        # time of partial update of most binding tables approaches or exceeds full update
        # time. In fact this doesn't matter much, as general update is arond 0.001 (0.1%),
        # and a few cases of > 0.01 (1%) are when new repositories are added, othewise it's
        # 1 (100%) when Package format changes or when database is filled for the first time.
        self._enable_partial_update = stats.change_fraction < 0.25

        # This was picked randomly
        self._enable_explicit_analyze = stats.change_fraction > 0.05

    def _finish_update(self) -> None:
        self._logger.log(
            f'update mode is {"partial" if self._enable_partial_update else "full"},'
            f'explicit analyze is {"enabled" if self._enable_explicit_analyze else "disabled"}'
        )

        self._logger.log('preparing updated packages')
        self._database.update_prepare_packages(self._enable_partial_update)

        self._logger.log('updating projects')
        self._database.update_projects(self._enable_partial_update, self._enable_explicit_analyze)

        self._logger.log('updating maintainers (precreate)')
        self._database.update_maintainers_precreate(self._enable_explicit_analyze)

        self._logger.log('updating maintainers')
        self._database.update_maintainers_2(self._enable_explicit_analyze)

        self._logger.log('updating tracks')
        self._database.update_tracks(self._enable_partial_update, self._enable_explicit_analyze)

        self._logger.log('updating track versions')
        self._database.update_track_versions(self._enable_partial_update, self._enable_explicit_analyze)

        self._logger.log('updating project releases')
        self._database.update_project_releases(self._enable_partial_update, self._enable_explicit_analyze)

        self._logger.log('updating project events')
        self._database.update_project_events(self._history_cutoff_timestamp)

        self._logger.log('updating maintainer events')
        self._database.update_maintainer_events()

        self._logger.log('updating repositry events')
        self._database.update_repository_events()

        self._logger.log('updating projects turnover')
        self._database.update_projects_turnover()

        self._logger.log('updating links')
        self._database.update_links()

        self._logger.log('updating statistics (delta)')
        self._database.update_statistics_delta()

        self._logger.log('updating redirects')
        self._database.update_redirects(self._enable_partial_update, self._enable_explicit_analyze)

        # Note: before this, packages table still contains old versions of packages,
        # while new versions reside in incoming_packages temporary table
        self._logger.log('applying updated packages')
        self._database.update_apply_packages(self._enable_partial_update, self._enable_explicit_analyze)
        # Note: after this, packages table contain new versions of packages

        self._logger.log('updating repositories')
        self._database.update_repositories()

        self._logger.log('updating maintainers (legacy)')
        self._database.update_maintainers()

        self._logger.log('updating binding table repo_metapackages')
        self._database.update_binding_repo_metapackages(self._enable_partial_update, self._enable_explicit_analyze)

        self._logger.log('updating binding table category_metapackages')
        self._database.update_binding_category_metapackages(self._enable_partial_update, self._enable_explicit_analyze)

        self._logger.log('updating binding table maintainer_metapackages')
        self._database.update_binding_maintainer_metapackages(self._enable_partial_update, self._enable_explicit_analyze)

        self._logger.log('updating binding table maintainer_and_repo_metapackages')
        self._database.update_binding_maintainer_and_repo_metapackages(self._enable_partial_update, self._enable_explicit_analyze)

        self._logger.log('updating url relations (all)')
        self._database.update_url_relations_all(self._enable_partial_update, self._enable_explicit_analyze)

        self._logger.log('updating url relations (filtered)')
        self._database.update_url_relations_filtered(self._enable_partial_update, self._enable_explicit_analyze)

        self._logger.log('updating projects has_related flag')
        self._database.update_projects_has_related()

        self._logger.log('updating problems')
        self._database.update_problems(self._enable_partial_update, self._enable_explicit_analyze)

        self._logger.log('updating problem counts')
        self._database.update_repositories_problem_counts()

        self._logger.log('updating statistics (global)')
        self._database.update_statistics_global()

        self._logger.log('updating histories')
        self._database.update_histories()

        self._logger.log('finalizing the update')
        self._database.update_finish()

    class UpdateManipulator:
        _update: 'UpdateProcess'

        def __init__(self, update: 'UpdateProcess') -> None:
            self._update = update

        def push_packages(self, projects: Iterable[List[Package]]) -> None:
            self._update._push_packages(projects)

        def set_history_cutoff_timestamp(self, timestamp: int) -> None:
            self._update._history_cutoff_timestamp = timestamp

    def __enter__(self) -> 'UpdateProcess.UpdateManipulator':
        self._start_update()

        return UpdateProcess.UpdateManipulator(self)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is None:
            self._finish_update()
