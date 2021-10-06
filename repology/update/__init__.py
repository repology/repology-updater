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
from typing import Any, Iterable

import psycopg2

from repology.classifier import classify_packages
from repology.database import Database
from repology.fieldstats import FieldStatistics
from repology.logger import Logger
from repology.package import Package
from repology.update.changes import ProjectsChangeStatistics, RemovedProject, UpdatedProject, iter_changed_projects
from repology.update.hashes import iter_project_hashes


class ChangedProjectsAccumulator:
    _BATCH_SIZE = 1000

    _database: Database
    _effnames: list[str]

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


def adapt_package(package: Package) -> dict[str, Any]:
    res = package.__dict__
    if (links := res.get('links')) is not None:
        res['links'] = psycopg2.extras.Json(links)
    return res  # type: ignore


class UpdateProcess:
    _database: Database
    _logger: Logger

    _enable_explicit_analyze: bool = False
    _history_cutoff_timestamp: int = 0

    def __init__(self, database: Database, logger: Logger) -> None:
        self._database = database
        self._logger = logger

    def _start_update(self) -> None:
        self._logger.log('starting the update')
        self._database.update_start()

        self._logger.log('forcing update for projects affected by changed CPEs')
        self._database.update_force_project_updates_by_cpe()

    def _push_packages(self, projects: Iterable[list[Package]]) -> None:
        self._logger.log('updating projects')

        field_stats_per_repo: dict[str, FieldStatistics] = defaultdict(FieldStatistics)
        stats = ProjectsChangeStatistics()

        prev_total = 0

        changed_projects = ChangedProjectsAccumulator(self._database)

        # XXX: note that we update packages only when they change in repositories
        # that is, if classification algorithm is changed and this causes package
        # statuses change, it won't be picked up by this process
        for change in iter_changed_projects(iter_project_hashes(self._database), projects, stats):
            if isinstance(change, UpdatedProject):
                if len(change.packages) >= 20000:
                    raise RuntimeError('sanity check failed, more than 20k packages for a single project')

                classify_packages(change.packages)
                self._database.add_packages(map(adapt_package, change.packages))
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
            self._database.update_repository_used_package_fields(
                repo,
                field_stats.get_used_fields(),
                field_stats.get_used_link_types()
            )

        # This was picked randomly
        self._enable_explicit_analyze = stats.change_fraction > 0.05

    def _finish_update(self) -> None:
        self._logger.log(f'explicit analyze is {"enabled" if self._enable_explicit_analyze else "disabled"}')

        # Create new objects referenced from packages by id
        self._logger.log('creating new links')
        self._database.update_create_links(self._enable_explicit_analyze)

        self._logger.log('translating incoming packages')
        self._database.update_translate_packages()

        self._logger.log('preparing updated packages')
        self._database.update_prepare_packages()

        # General update
        self._logger.log('updating CPE information')
        self._database.update_cpe(self._enable_explicit_analyze)

        self._logger.log('updating vulnerabilities')
        self._database.update_vulnerabilities()

        self._logger.log('updating projects')
        self._database.update_projects(self._enable_explicit_analyze)

        self._logger.log('updating maintainers (precreate)')
        self._database.update_maintainers_precreate(self._enable_explicit_analyze)

        self._logger.log('updating maintainers')
        self._database.update_maintainers(self._enable_explicit_analyze)

        self._logger.log('updating repositories')
        self._database.update_repositories()

        self._logger.log('updating tracks')
        self._database.update_tracks(self._enable_explicit_analyze)

        self._logger.log('updating track versions')
        self._database.update_track_versions(self._enable_explicit_analyze)

        self._logger.log('updating project releases')
        self._database.update_project_releases(self._enable_explicit_analyze)

        self._logger.log('updating project events')
        self._database.update_project_events(self._history_cutoff_timestamp)

        self._logger.log('updating maintainer events')
        self._database.update_maintainer_events()

        self._logger.log('updating repository events')
        self._database.update_repository_events()

        self._logger.log('updating projects turnover')
        self._database.update_projects_turnover()

        self._logger.log('updating links')
        self._database.update_links(self._enable_explicit_analyze)

        self._logger.log('updating statistics (delta)')
        self._database.update_statistics_delta()

        self._logger.log('updating redirects')
        self._database.update_redirects(self._enable_explicit_analyze)

        # Note: before this, packages table still contains old versions of packages,
        # while new versions reside in incoming_packages temporary table
        self._logger.log('applying updated packages')
        self._database.update_apply_packages(self._enable_explicit_analyze)
        # Note: after this, packages table contain new versions of packages

        self._logger.log('updating binding table repo_metapackages')
        self._database.update_binding_repo_metapackages(self._enable_explicit_analyze)

        self._logger.log('updating binding table category_metapackages')
        self._database.update_binding_category_metapackages(self._enable_explicit_analyze)

        self._logger.log('updating binding table maintainer_metapackages')
        self._database.update_binding_maintainer_metapackages(self._enable_explicit_analyze)

        self._logger.log('updating binding table maintainer_and_repo_metapackages')
        self._database.update_binding_maintainer_and_repo_metapackages(self._enable_explicit_analyze)

        self._logger.log('updating project names')
        self._database.update_names(self._enable_explicit_analyze)

        self._logger.log('updating url relations (all)')
        self._database.update_url_relations_all(self._enable_explicit_analyze)

        self._logger.log('updating url relations (filtered)')
        self._database.update_url_relations_filtered(self._enable_explicit_analyze)

        self._logger.log('updating projects has_related flag')
        self._database.update_projects_has_related()

        self._logger.log('updating problems')
        self._database.update_problems(self._enable_explicit_analyze)

        self._logger.log('updating repository problem counts')
        self._database.update_repositories_problem_counts()

        self._logger.log('updating repository maintainers')
        self._database.update_repository_maintainers(self._enable_explicit_analyze)

        self._logger.log('updating repository maintainer counts')
        self._database.update_repositories_maintainer_counts()

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

        def push_packages(self, projects: Iterable[list[Package]]) -> None:
            self._update._push_packages(projects)

        def set_history_cutoff_timestamp(self, timestamp: int) -> None:
            self._update._history_cutoff_timestamp = timestamp

    def __enter__(self) -> 'UpdateProcess.UpdateManipulator':
        self._start_update()

        return UpdateProcess.UpdateManipulator(self)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is None:
            self._finish_update()
