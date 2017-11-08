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

    class BranchPrototype:
        __slots__ = ['versionclass', 'check']

        def __init__(self, versionclass, check):
            self.versionclass = versionclass
            self.check = check

        def Check(self, package):
            return self.check(package)

        def CreateBranch(self, bestversion=None):
            return Branch(self.versionclass, bestversion)

    class Branch:
        __slots__ = ['versionclass', 'bestversion', 'lastversion']

        def __init__(self, versionclass, bestversion=None):
            self.versionclass = versionclass
            self.bestversion = bestversion
            self.lastversion = bestversion

        def SetLastVersion(self, lastversion):
            self.lastversion = lastversion

        def BestVersionCompare(self, version):
            return VersionCompare(version, self.bestversion) if self.bestversion is not None else 1

        def IsAfterBranch(self, version):
            return VersionCompare(version, self.lastversion) == -1 if self.lastversion is not None else False

    # we always work on packages sorted by version
    packages = PackagesetSortByVersions(packages)

    # branch prototypes
    default_branchproto = BranchPrototype(VersionClass.newest, lambda package: not package.devel)

    branchprotos = [
        BranchPrototype(VersionClass.devel, lambda package: package.devel),
        default_branchproto,
    ]

    default_branchproto_idx = branchprotos.index(default_branchproto)

    #
    # Pass 1: discover branches
    #
    branches = []
    families = set()
    packages_by_repo = {}
    current_branchproto_idx = None
    for verpackages in AggregateBySameVersion(packages):
        has_non_ignored = False
        matching_branchproto_indexes = set()

        for package in verpackages:
            families.add(package.family)
            packages_by_repo.setdefault(package.repo, []).append(package)

            if not package.ignoreversion:
                has_non_ignored = True

            for branchproto_idx in range(0, len(branchprotos)):
                if branchprotos[branchproto_idx].Check(package):
                    matching_branchproto_indexes.add(branchproto_idx)

        final_branchproto_idx = list(matching_branchproto_indexes)[0] if len(matching_branchproto_indexes) == 1 else default_branchproto_idx

        if final_branchproto_idx == current_branchproto_idx:
            branches[-1].SetLastVersion(verpackages[0].version)
        elif (current_branchproto_idx is None or final_branchproto_idx > current_branchproto_idx) and has_non_ignored:
            branches.append(branchprotos[final_branchproto_idx].CreateBranch(verpackages[0].version))
            current_branchproto_idx = final_branchproto_idx

    # handle unique package
    metapackage_is_unique = len(families) == 1

    # we should always have at least one branch
    if not branches:
        branches = [default_branchproto.CreateBranch()]

    #
    # Pass 2: fill version classes
    #
    for repo, repo_packages in packages_by_repo.items():
        current_branch_idx = 0
        first_version_in_branch_per_flavor = {}

        for package in repo_packages:  # these are still sorted by version
            # switch to next branch when the current one is over, but not past the last branch
            while current_branch_idx < len(branches) - 1 and branches[current_branch_idx].IsAfterBranch(package.version):
                current_branch_idx += 1
                first_version_in_branch_per_flavor = {}

            # chose version class based on comparison to branch best version
            current_comparison = branches[current_branch_idx].BestVersionCompare(package.version)

            if current_comparison > 0:
                package.versionclass = VersionClass.ignored
            else:
                flavor = '_'.join(package.flavors)

                if current_comparison == 0:
                    package.versionclass = VersionClass.unique if metapackage_is_unique else branches[current_branch_idx].versionclass
                else:
                    non_first_in_branch = flavor in first_version_in_branch_per_flavor and VersionCompare(first_version_in_branch_per_flavor[flavor], package.version) != 0
                    package.versionclass = VersionClass.legacy if non_first_in_branch else VersionClass.outdated

                if flavor not in first_version_in_branch_per_flavor:
                    first_version_in_branch_per_flavor[flavor] = package.version


def PackagesetToBestByRepo(packages):
    state_by_repo = {}

    for package in PackagesetSortByVersions(packages):
        if package.repo not in state_by_repo or (state_by_repo[package.repo].versionclass == VersionClass.ignored and package.versionclass != VersionClass.ignored):
            state_by_repo[package.repo] = package

    return state_by_repo


def PackagesetSortByVersions(packages):
    def compare(p1, p2):
        return VersionCompare(p2.version, p1.version)

    return sorted(packages, key=cmp_to_key(compare))


def PackagesetSortByNameVersion(packages):
    def compare(p1, p2):
        if p1.name < p2.name:
            return -1
        if p1.name > p2.name:
            return 1
        return VersionCompare(p2.version, p1.version)

    return sorted(packages, key=cmp_to_key(compare))


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
