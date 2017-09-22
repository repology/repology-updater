# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import sys

from functools import cmp_to_key

from repology.package import *
from repology.version import VersionCompare


def PackagesMerge(packages):
    aggregated = {}

    # aggregate by subrepo/name/version
    # this is just to make merging faster, as packages
    # with same subrepo/name/version may or may not merge
    for package in packages:
        key = (package.subrepo, package.name, package.version)
        aggregated.setdefault(key, []).append(package)

    outpkgs = []
    for packages in aggregated.values():
        while packages:
            nextpackages = []
            merged = packages[0]
            for package in packages[1:]:
                if not merged.TryMerge(package):
                    nextpackages.append(package)

            outpkgs.append(merged)
            packages = nextpackages

    return outpkgs


def PackagesetCheckFilters(packages, *filters):
    for filt in filters:
        if not filt.Check(packages):
            return False

    return True


def FillPackagesetVersions(packages):
    # helpers
    def AggregateBySameVersion(packages):
        current = None
        for package in packages:
            if current is None:
                current = [package]
            elif VersionCompare(current[0].version, package.version) == 0:
                current.append(package)
            else:
                yield current
                current = [package]

        if current is not None:
            yield current

    class Branch:
        __slots__ = ['bestversion', 'versionclass']

        def __init__(self, bestversion, versionclass):
            self.bestversion = bestversion
            self.versionclass = versionclass

        def VersionCompare(self, version):
            return VersionCompare(version, self.bestversion) if self.bestversion is not None else 1

    # we always work on packages sorted by version
    packages = PackagesetSortByVersions(packages)

    # first, determine best version for each branch and # of families
    branches = []
    families = set()
    packages_by_repo = {}
    state = 0  # 0 = default, 1 = devel, 2 = non-devel
    for verpackages in AggregateBySameVersion(packages):
        has_non_ignored = False
        has_devel = False
        has_default = False

        for package in verpackages:
            families.add(package.family)
            packages_by_repo.setdefault(package.repo, []).append(package)

            if not package.ignoreversion:
                has_non_ignored = True

            if package.devel:
                has_devel = True
            else:
                has_default = True

        if has_non_ignored:
            if state == 0 and has_devel and not has_default:
                branches.append(Branch(verpackages[0].version, VersionClass.devel))
                state = 1
            elif state <= 1 and has_default:
                branches.append(Branch(verpackages[0].version, VersionClass.newest))
                state = 2

    # handle unique package
    metapackage_is_unique = len(families) == 1

    # we should always have at least one branch
    if not branches:
        branches.append(Branch(None, VersionClass.newest))

    # now fill in classes
    for repo, repo_packages in packages_by_repo.items():
        current_branch = 0
        first_in_branch = True

        for package in repo_packages:  # these are still sorted by version
            current_comparison = branches[current_branch].VersionCompare(package.version)

            while True:
                if current_comparison > 0:
                    # only possible before first branch
                    package.versionclass = VersionClass.ignored
                    break

                if current_comparison == 0:
                    package.versionclass = VersionClass.unique if metapackage_is_unique else branches[current_branch].versionclass
                    first_in_branch = False
                    break

                if current_branch == len(branches) - 1:
                    # last branch
                    package.versionclass = VersionClass.outdated if first_in_branch else VersionClass.legacy
                    first_in_branch = False
                    break

                next_comparison = branches[current_branch + 1].VersionCompare(package.version)

                if next_comparison > 0:
                    # still not in next branch
                    package.versionclass = VersionClass.outdated if first_in_branch else VersionClass.legacy
                    first_in_branch = False
                    break

                # otherwise, we need to advance to the next branch
                first_in_branch = True
                current_branch += 1
                current_comparison = next_comparison


def PackagesetToBestByRepo(packages):
    state_by_repo = {}

    for package in PackagesetSortByVersions(packages):
        if package.repo not in state_by_repo or (state_by_repo[package.repo].versionclass == VersionClass.ignored and package.versionclass != VersionClass.ignored):
            state_by_repo[package.repo] = package

    return state_by_repo


def PackagesetSortByVersions(packages):
    def packages_version_cmp_reverse(p1, p2):
        return VersionCompare(p2.version, p1.version)

    return sorted(packages, key=cmp_to_key(packages_version_cmp_reverse))


def PackagesetToFamilies(packages):
    return set([package.family for package in packages])


def PackagesetAggregateByVersions(packages, classmap={}):
    def MapClass(versionclass):
        return classmap.get(versionclass, versionclass)

    versions = {}
    for package in packages:
        key = (package.version, MapClass(package.versionclass))
        if key not in versions:
            versions[key] = []
        versions[key].append(package)

    def key_cmp_reverse(v1, v2):
        return VersionCompare(v2[0], v1[0])

    return [
        {
            'version': key[0],
            'versionclass': key[1],
            'packages': versions[key]
        } for key in sorted(versions.keys(), key=cmp_to_key(key_cmp_reverse))
    ]
