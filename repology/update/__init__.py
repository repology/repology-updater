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
from timeit import default_timer as timer
from typing import Dict, Iterable, List

from repology.database import Database
from repology.fieldstats import FieldStatistics
from repology.logger import Logger
from repology.package import Package
from repology.packageproc import fill_packageset_versions


def calculate_project_classless_hash(packages: Iterable[Package]) -> int:
    total_hash = 0
    seen_hashes: Set[int] = set()

    for package in packages:
        package_hash = package.get_classless_hash()

        if package_hash in seen_hashes:
            raise RuntimeError(f'duplicate hash for package {package}')
        else:
            seen_hashes.add(package_hash)

        total_hash ^= package_hash

    return total_hash


def update_repology(database: Database, projects: Iterable[List[Package]], logger: Logger) -> None:
    logger.log('clearing the database')
    database.update_start()

    package_queue = []
    num_pushed = 0
    start_time = timer()

    logger.log('pushing packages to database')

    field_stats_per_repo: Dict[str, FieldStatistics] = defaultdict(FieldStatistics)

    for packageset in projects:
        fill_packageset_versions(packageset)
        package_queue.extend(packageset)

        for package in packageset:
            field_stats_per_repo[package.repo].add(package)

        database.update_project_hash(packageset[0].effname, calculate_project_classless_hash(packageset))

        if len(package_queue) >= 10000:
            database.add_packages(package_queue)
            num_pushed += len(package_queue)
            package_queue = []
            logger.get_indented().log('pushed {} packages, {:.2f} packages/second'.format(num_pushed, num_pushed / (timer() - start_time)))

    # process what's left in the queue
    database.add_packages(package_queue)

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
