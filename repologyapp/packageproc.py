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

from collections import defaultdict
from dataclasses import dataclass
from functools import cmp_to_key
from typing import Dict, Iterable, List, Optional, Tuple

from repology.package import Package, PackageStatus


def packageset_sort_by_version(packages: Iterable[Package]) -> List[Package]:
    def compare(p1: Package, p2: Package) -> int:
        return p2.version_compare(p1)

    return sorted(packages, key=cmp_to_key(compare))


def packageset_to_best(packages: Iterable[Package]) -> Optional[Package]:
    sorted_packages = packageset_sort_by_version(packages)

    for package in sorted_packages:
        if not PackageStatus.is_ignored(package.versionclass):
            return package

    return None


def packageset_to_best_by_repo(packages: Iterable[Package]) -> Dict[str, Package]:
    state_by_repo: Dict[str, Package] = {}

    for package in packageset_sort_by_version(packages):
        if package.repo not in state_by_repo or (PackageStatus.is_ignored(state_by_repo[package.repo].versionclass) and not PackageStatus.is_ignored(package.versionclass)):
            state_by_repo[package.repo] = package

    return state_by_repo


def packageset_sort_by_name_version(packages: Iterable[Package]) -> List[Package]:
    def compare(p1: Package, p2: Package) -> int:
        if p1.name < p2.name:
            return -1
        if p1.name > p2.name:
            return 1
        return p2.version_compare(p1)

    return sorted(packages, key=cmp_to_key(compare))


@dataclass
class VersionAggregation:
    version: str
    versionclass: int
    numfamilies: int


def packageset_aggregate_by_version(packages: Iterable[Package], classmap: Dict[int, int] = {}) -> List[VersionAggregation]:
    def create_version_aggregation(packages: Iterable[Package]) -> Iterable[VersionAggregation]:
        aggregated: Dict[Tuple[str, int], List[Package]] = defaultdict(list)

        for package in packages:
            aggregated[
                (package.version, classmap.get(package.versionclass, package.versionclass))
            ].append(package)

        for (version, versionclass), packages in sorted(aggregated.items()):
            yield VersionAggregation(version=version, versionclass=versionclass, numfamilies=len(set([package.family for package in packages])))

    def post_sort_same_version(versions: Iterable[VersionAggregation]) -> List[VersionAggregation]:
        return sorted(versions, key=lambda v: (v.numfamilies, v.version, v.versionclass), reverse=True)

    def aggregate_by_version(packages: Iterable[Package]) -> Iterable[List[VersionAggregation]]:
        current: List[Package] = []
        for package in packageset_sort_by_version(packages):
            if not current or current[0].version_compare(package) == 0:
                current.append(package)
            else:
                yield post_sort_same_version(create_version_aggregation(current))
                current = [package]

        if current:
            yield post_sort_same_version(create_version_aggregation(current))

    return sum(aggregate_by_version(packages), [])
