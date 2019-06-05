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
from functools import cmp_to_key
from typing import Any, Dict, Iterable, List, Tuple

from repology.package import Package, VersionClass


def packageset_sort_by_version(packages: Iterable[Package]) -> List[Package]:
    def compare(p1, p2):
        return p2.version_compare(p1)

    return sorted(packages, key=cmp_to_key(compare))


def packageset_to_best_by_repo(packages: Iterable[Package]) -> Dict[str, Package]:
    state_by_repo: Dict[str, Package] = {}

    for package in packageset_sort_by_version(packages):
        if package.repo not in state_by_repo or (VersionClass.IsIgnored(state_by_repo[package.repo].versionclass) and not VersionClass.IsIgnored(package.versionclass)):
            state_by_repo[package.repo] = package

    return state_by_repo


def packageset_sort_by_name_version(packages: Iterable[Package]) -> List[Package]:
    def compare(p1, p2):
        if p1.name < p2.name:
            return -1
        if p1.name > p2.name:
            return 1
        return p2.version_compare(p1)

    return sorted(packages, key=cmp_to_key(compare))


def packageset_aggregate_by_version(packages: Iterable[Package], classmap: Dict[int, int] = {}) -> List[Dict[str, Any]]:
    def create_version_aggregation(packages: Iterable[Package]) -> Iterable[Dict[str, Any]]:
        aggregated: Dict[Tuple[str, int], List[Package]] = defaultdict(list)

        for package in packages:
            aggregated[
                (package.version, classmap.get(package.versionclass, package.versionclass))
            ].append(package)

        for (version, versionclass), packages in sorted(aggregated.items()):
            yield {  # XXX: use dataclass
                'version': version,
                'versionclass': versionclass,
                'numfamilies': len(set([package.family for package in packages]))
            }

    def post_sort_same_version(versions: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(versions, key=lambda v: (v['numfamilies'], v['version'], v['versionclass']), reverse=True)

    def aggregate_by_version(packages: Iterable[Package]) -> Iterable[List[Dict[str, Any]]]:
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
