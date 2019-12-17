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


def update_project(database: Database, change: UpdatedProject) -> None:
    fill_packageset_versions(change.packages)

    database.remove_packages(change.effname)
    database.add_packages(change.packages)

    database.update_project_hash(change.effname, change.hash)


def remove_project(database: Database, change: RemovedProject) -> None:
    database.remove_packages(change.effname)
    database.remove_project_hash(change.effname)


def update_repology(database: Database, projects: Iterable[List[Package]], logger: Logger) -> None:
    logger.log('starting the update')
    database.update_start()

    logger.log('updating projects')

    field_stats_per_repo: Dict[str, FieldStatistics] = defaultdict(FieldStatistics)

    prev_total = 0
    stats = ProjectsChangeStatistics()

    for change in iter_changed_projects(iter_project_hashes(database), projects, stats):
        if isinstance(change, UpdatedProject):
            update_project(database, change)

            for package in change.packages:
                field_stats_per_repo[package.repo].add(package)

        elif isinstance(change, RemovedProject):
            remove_project(database, change)

        if stats.total - prev_total >= 10000 or prev_total == 0:
            logger.log(f'  at "{change.effname}": {stats}')
            prev_total = stats.total

    logger.log(f'  done: {stats}')

    if stats.change_fraction >= 0.05:
        logger.log('performing extra actions after huge change')
        database.update_handle_huge_change()

    logger.log('updating field statistics')

    for repo, field_stats in field_stats_per_repo.items():
        database.update_repository_used_package_fields(repo, field_stats.get_used_fields())

    logger.log('updating metapackages')
    database.update_metapackages()

    logger.log('updating repositories')
    database.update_repositories()

    logger.log('updating maintainers')
    database.update_maintainers()

    logger.log('updating binding table repo_metapackages')
    database.update_binding_repo_metapackages()

    logger.log('updating binding table category_metapackages')
    database.update_binding_category_metapackages()

    logger.log('updating binding table maintainer_metapackages')
    database.update_binding_maintainer_metapackages()

    logger.log('updating binding table maintainer_and_repo_metapackages')
    database.update_binding_maintainer_and_repo_metapackages()

    logger.log('updating url relations')
    database.update_url_relations()

    logger.log('updating problems')
    database.update_problems()

    logger.log('updating links')
    database.update_links()

    logger.log('updating statistics')
    database.update_statistics()

    logger.log('updating histories')
    database.update_histories()

    logger.log('finalizing the update')
    database.update_finish()

    logger.log('committing changes')
    database.commit()
