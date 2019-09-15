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

from repologyapp.package import AnyPackageDataMinimal, PackageStatus, package_version_compare


def packageset_sort_by_version(packages: Iterable[AnyPackageDataMinimal]) -> List[AnyPackageDataMinimal]:
    return sorted(packages, key=cmp_to_key(package_version_compare), reverse=True)


def packageset_to_best(packages: Iterable[AnyPackageDataMinimal], allow_ignored: bool = False) -> Optional[AnyPackageDataMinimal]:
    sorted_packages = packageset_sort_by_version(packages)

    if not sorted_packages:
        return None

    # if allowed, return first package regardless of status
    if allow_ignored:
        return sorted_packages[0]

    # otherwise, return first non-ignore package
    for package in sorted_packages:
        if not PackageStatus.is_ignored(package.versionclass):
            return package

    # fallback to first package
    return sorted_packages[0]


def packageset_to_best_by_repo(packages: Iterable[AnyPackageDataMinimal], allow_ignored: bool = False) -> Dict[str, AnyPackageDataMinimal]:
    state_by_repo: Dict[str, AnyPackageDataMinimal] = {}

    for package in packageset_sort_by_version(packages):
        # start with first package
        if package.repo not in state_by_repo:
            state_by_repo[package.repo] = package
            continue

        # replace by non-ignored if needed and possible
        if not allow_ignored and PackageStatus.is_ignored(state_by_repo[package.repo].versionclass):
            if not PackageStatus.is_ignored(package.versionclass):
                state_by_repo[package.repo] = package

    return state_by_repo


def packageset_sort_by_name_version(packages: Iterable[AnyPackageDataMinimal]) -> List[AnyPackageDataMinimal]:
    def compare(p1: AnyPackageDataMinimal, p2: AnyPackageDataMinimal) -> int:
        if p1.name < p2.name:
            return -1
        if p1.name > p2.name:
            return 1
        return -package_version_compare(p1, p2)

    return sorted(packages, key=cmp_to_key(compare))


@dataclass
class VersionAggregation:
    version: str
    versionclass: int
    numfamilies: int


def packageset_aggregate_by_version(packages: Iterable[AnyPackageDataMinimal], classmap: Dict[int, int] = {}) -> List[VersionAggregation]:
    def create_version_aggregation(packages: Iterable[AnyPackageDataMinimal]) -> Iterable[VersionAggregation]:
        aggregated: Dict[Tuple[str, int], List[AnyPackageDataMinimal]] = defaultdict(list)

        for package in packages:
            aggregated[
                (package.version, classmap.get(package.versionclass, package.versionclass))
            ].append(package)

        for (version, versionclass), packages in sorted(aggregated.items()):
            yield VersionAggregation(version=version, versionclass=versionclass, numfamilies=len(set([package.family for package in packages])))

    def post_sort_same_version(versions: Iterable[VersionAggregation]) -> List[VersionAggregation]:
        return sorted(versions, key=lambda v: (v.numfamilies, v.version, v.versionclass), reverse=True)

    def aggregate_by_version(packages: Iterable[AnyPackageDataMinimal]) -> Iterable[List[VersionAggregation]]:
        current: List[AnyPackageDataMinimal] = []
        for package in packageset_sort_by_version(packages):
            if not current or package_version_compare(current[0], package) == 0:
                current.append(package)
            else:
                yield post_sort_same_version(create_version_aggregation(current))
                current = [package]

        if current:
            yield post_sort_same_version(create_version_aggregation(current))

    return sum(aggregate_by_version(packages), [])
