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
from typing import Dict, Iterable, List, MutableSet, Optional, Sequence, Tuple, cast

from repology.package import Package, PackageFlags, PackageStatus


def packageset_deduplicate(packages: Sequence[Package]) -> List[Package]:
    aggregated: Dict[Tuple[str, Optional[str], Optional[str], str], List[Package]] = defaultdict(list)

    # aggregate by subset of fields to make O(n²) merge below faster
    for package in packages:
        key = (package.repo, package.subrepo, package.name, package.version)
        aggregated[key].append(package)

    outpkgs = []
    for packages in aggregated.values():
        while packages:
            nextpackages = []
            for package in packages[1:]:
                if package != packages[0]:
                    nextpackages.append(package)

            outpkgs.append(packages[0])
            packages = nextpackages

    return outpkgs


def packageset_is_unique(packages: Sequence[Package]) -> bool:
    if len(packages) <= 1:
        return True

    for package in packages[1:]:
        if package.family != packages[0].family:
            return False

    return True


def packageset_may_be_unignored(packages: Sequence[Package]) -> bool:
    if len(packages) <= 1:
        return True

    for package in packages:
        # condition 1: must be unique
        if package.family != packages[0].family:
            return False
        # condition 2: must consist of ignored packages only
        if not package.has_flag(PackageFlags.ANY_IGNORED):
            return False

    return True


def aggregate_by_same_version(packages: Iterable[Package]) -> Iterable[List[Package]]:
    current: List[Package] = []

    for package in packages:
        if not current:
            current = [package]
        elif current[0].version_compare(package) == 0:
            current.append(package)
        else:
            yield current
            current = [package]

    if current:
        yield current


@dataclass
class _Branch:
    newest_status: int
    order: int
    first: Optional[Package] = None
    altfirst: Optional[Package] = None
    last: Optional[Package] = None

    def include(self, package: Package, alt: bool = False) -> None:
        if self.first is None and not alt:
            self.first = package
        if self.altfirst is None:
            self.altfirst = package

        self.last = package

    def is_empty(self) -> bool:
        return self.altfirst is None

    def preceeds(self, package: Package) -> int:
        assert(self.last)
        return self.last.version_compare(package) > 0

    def compared_to_best(self, package: Package, alt: bool = False) -> int:
        if alt:
            assert(self.altfirst)
            return package.version_compare(self.altfirst)
        else:
            assert(self.first)
            return package.version_compare(self.first)


def fill_packageset_versions(packages: Sequence[Package]) -> None:
    # global flags #1
    project_is_unique = packageset_is_unique(packages)

    # preprocessing: rolling versions
    packages_to_process = []

    for package in packages:
        if package.has_flag(PackageFlags.ROLLING):
            package.versionclass = PackageStatus.ROLLING
        else:
            packages_to_process.append(package)

    # we always work on packages sorted by version
    packages = packageset_sort_by_version(packages_to_process)

    # global flags #2

    # The idea here is that if package versions are compared only within a single family
    # (so this is calculated after rolling packages are removed, since they do not
    # participate in comparison), and all versions are ignored, it makes sense to unignore
    # them, because unique/latest/outdated versions are more informative than just ignored
    # (the best part is actually a possibility of outdated packages)
    #
    # Actually, this is a hack to partially revert the effect of global ignore of .*git.*
    # versions. That is why I couldn't decide on whether only `ignored` status or all ignored-
    # like statuses may be unignored.
    #
    # The proper solution would be to allow rules decide whether they may be unignored. This,
    # however, brings in more complex flag handling, as in `soft` and `hard` ignores, so I'd
    # like to postpone it for now
    project_should_unignore = packageset_may_be_unignored(packages)

    #
    # Pass 1: calculate branch boundaries
    #
    packages_by_repo: Dict[str, List[Package]] = defaultdict(list)

    devel_branch = _Branch(newest_status=PackageStatus.DEVEL, order=0)
    main_branch = _Branch(newest_status=PackageStatus.NEWEST, order=1)

    current_branch = devel_branch

    first_package_in_legacy_branch: Dict[str, Package] = {}

    for verpackages in aggregate_by_same_version(packages):
        all_flags = 0
        has_non_devel = False
        version_totally_ignored = not project_should_unignore
        legacy_branch_names = set()

        for package in verpackages:
            packages_by_repo[package.repo].append(package)

            all_flags |= package.flags

            if not package.has_flag(PackageFlags.ANY_IGNORED):
                version_totally_ignored = False

            if not package.has_flag(PackageFlags.DEVEL | PackageFlags.WEAK_DEVEL):
                has_non_devel = True

            if package.branch is not None:
                legacy_branch_names.add(package.branch)

        is_devel = (
            all_flags & PackageFlags.DEVEL or (
                all_flags & PackageFlags.WEAK_DEVEL and not has_non_devel
            )
        ) and not all_flags & PackageFlags.STABLE

        #
        # The important logic of branch bounds handling follows
        #

        # 1. Choose suitable branch naively
        #    The following code may use different branch as it enforces branch order, e.g.
        #    devel may not follow main
        target_branch = devel_branch if is_devel else main_branch

        # 2. Debase ignored versions
        #    These may only be added to the bottom of their designated branch, otherwise
        #    they do not affect branch bounds
        if version_totally_ignored:
            if current_branch == target_branch and not current_branch.is_empty():
                current_branch.include(verpackages[0], cast(bool, all_flags & PackageFlags.ALTVER))
            continue

        # 3. Switch to the next branch when needed
        if target_branch.order > current_branch.order:
            current_branch = target_branch

        # 4. Assign the version to the current branch (effectively update branch bounds)
        current_branch.include(verpackages[0], cast(bool, all_flags & PackageFlags.ALTVER))

        # 5. Update legacy branches
        for legacy_branch_name in legacy_branch_names:
            if legacy_branch_name not in first_package_in_legacy_branch:
                first_package_in_legacy_branch[legacy_branch_name] = verpackages[0]

    #
    # Pass 2: fill version classes
    #
    for repo, repo_packages in packages_by_repo.items():
        current_branch = devel_branch
        first_package_in_branch_per_flavor: Dict[str, Package] = {}
        seen_legacy_branches: MutableSet[str] = set()

        for package in repo_packages:  # these are still sorted by version
            do_switch_to_devel = (
                current_branch is devel_branch and
                (current_branch.is_empty() or current_branch.preceeds(package)) and
                not main_branch.is_empty()
            )
            if do_switch_to_devel:
                # switch from devel to main branch
                current_branch = main_branch
                first_package_in_branch_per_flavor = {}

            # chose version class based on comparison to branch best version
            if current_branch.is_empty():
                current_comparison = 1
            else:
                current_comparison = current_branch.compared_to_best(package, cast(bool, package.flags & PackageFlags.ALTVER))

            if current_comparison > 0:
                # Note that the order here determines class priority when multiple
                # flags are present
                # - noscheme beats everything else - if there's no versioning scheme,
                #   it's meaningless to talk about any kind of version correctness
                # - incorrect beats untrusted as more specific
                # - everything else is generic ignored
                if package.has_flag(PackageFlags.NOSCHEME):
                    package.versionclass = PackageStatus.NOSCHEME
                elif package.has_flag(PackageFlags.INCORRECT):
                    package.versionclass = PackageStatus.INCORRECT
                elif package.has_flag(PackageFlags.UNTRUSTED):
                    package.versionclass = PackageStatus.UNTRUSTED
                else:
                    package.versionclass = PackageStatus.IGNORED
            else:
                flavor = '_'.join(package.flavors)  # already sorted and unicalized in RepoProcessor

                if current_comparison == 0:
                    package.versionclass = PackageStatus.UNIQUE if project_is_unique else current_branch.newest_status
                else:
                    non_first_in_branch = (
                        flavor in first_package_in_branch_per_flavor and
                        first_package_in_branch_per_flavor[flavor].version_compare(package) != 0
                    )

                    non_first_in_legacy_branch = (
                        package.branch is not None and
                        package.branch not in seen_legacy_branches and
                        first_package_in_legacy_branch[package.branch].version_compare(package) > 0
                    )

                    legacy_allowed = (
                        (non_first_in_branch and not non_first_in_legacy_branch) or
                        package.has_flag(PackageFlags.LEGACY)
                    )

                    package.versionclass = PackageStatus.LEGACY if legacy_allowed else PackageStatus.OUTDATED

                if flavor not in first_package_in_branch_per_flavor:
                    first_package_in_branch_per_flavor[flavor] = package

            if package.branch is not None:
                seen_legacy_branches.add(package.branch)


def packageset_sort_by_version(packages: Sequence[Package]) -> List[Package]:
    def compare(p1: Package, p2: Package) -> int:
        return p2.version_compare(p1)

    return sorted(packages, key=cmp_to_key(compare))
