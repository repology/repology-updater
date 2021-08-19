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
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, cast

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
        # condition 3: must not be noscheme
        if package.has_flag(PackageFlags.NOSCHEME):
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
class _Section:
    newest_status: int
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


def _fill_packageset_versions(packages: Sequence[Package], project_is_unique: bool, project_should_unignore: bool) -> None:
    #
    # Pass 1: calculate section boundaries
    #
    packages_by_repo: Dict[str, List[Package]] = defaultdict(list)

    devel_section = _Section(newest_status=PackageStatus.DEVEL)
    main_section = _Section(newest_status=PackageStatus.NEWEST)

    current_section = devel_section

    best_package_in_branch: Dict[str, Package] = {}

    for verpackages in aggregate_by_same_version(packages):
        all_flags = 0
        has_non_devel = False
        version_totally_ignored = not project_should_unignore
        branches = set()

        for package in verpackages:
            packages_by_repo[package.repo].append(package)

            all_flags |= package.flags

            if not package.has_flag(PackageFlags.ANY_IGNORED):
                version_totally_ignored = False

            if not package.has_flag(PackageFlags.DEVEL | PackageFlags.WEAK_DEVEL):
                has_non_devel = True

            if package.branch is not None:
                branches.add(package.branch)

        is_devel = (
            all_flags & PackageFlags.DEVEL or (
                all_flags & PackageFlags.WEAK_DEVEL and not has_non_devel
            )
        ) and not all_flags & PackageFlags.STABLE

        #
        # The important logic of section bounds handling follows
        #

        # 1. Choose suitable section naively
        #    The following code may use different section as it enforces section order, e.g.
        #    devel may not follow main
        target_section = devel_section if is_devel else main_section

        # 2. Debase ignored versions
        #    These may only be added to the bottom of their designated section, otherwise
        #    they do not affect section bounds
        if version_totally_ignored:
            if current_section is target_section and not current_section.is_empty():
                current_section.include(verpackages[0], cast(bool, all_flags & PackageFlags.ALTVER))
            continue

        # 3. Switch to the next section when needed
        if target_section is not current_section and target_section is main_section:
            current_section = target_section

        # 4. Assign the version to the current section (effectively update section bounds)
        current_section.include(verpackages[0], cast(bool, all_flags & PackageFlags.ALTVER))

        # 5. Update legacy branches
        for branch in branches:
            if branch not in best_package_in_branch and not is_devel:
                best_package_in_branch[branch] = verpackages[0]

    #
    # Pass 2: fill version classes
    #
    for repo, repo_packages in packages_by_repo.items():
        current_section = devel_section
        first_package_in_section: Dict[str, Package] = {}  # by flavor
        first_package_in_branch: Dict[Tuple[Optional[str], str], Package] = {}  # by branch, flavor

        for package in repo_packages:  # these are still sorted by version
            do_switch_to_main_section = (
                current_section is devel_section and
                (current_section.is_empty() or current_section.preceeds(package)) and
                not main_section.is_empty()
            )
            if do_switch_to_main_section:
                # switch from devel to main section
                current_section = main_section
                first_package_in_section = {}

            # chose version class based on comparison to section best version
            if current_section.is_empty():
                current_comparison = 1
            else:
                current_comparison = current_section.compared_to_best(package, cast(bool, package.flags & PackageFlags.ALTVER))

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
                branch_key = (package.branch, flavor)

                if current_comparison == 0:
                    package.versionclass = PackageStatus.UNIQUE if project_is_unique else current_section.newest_status
                else:
                    non_first_in_section = (
                        flavor in first_package_in_section and
                        first_package_in_section[flavor].version_compare(package) != 0
                    )

                    first_but_not_best_in_branch = (
                        (
                            branch_key not in first_package_in_branch or
                            first_package_in_branch[branch_key].version_compare(package) == 0
                        ) and
                        package.branch in best_package_in_branch and
                        best_package_in_branch[package.branch].version_compare(package) > 0
                    )

                    legacy_allowed = (
                        (
                            non_first_in_section and not
                            first_but_not_best_in_branch and not
                            package.has_flag(PackageFlags.NOLEGACY)
                        ) or package.has_flag(PackageFlags.LEGACY)
                    )

                    package.versionclass = PackageStatus.LEGACY if legacy_allowed else PackageStatus.OUTDATED

                if flavor not in first_package_in_section:
                    first_package_in_section[flavor] = package

                if branch_key is not None and branch_key not in first_package_in_branch:
                    first_package_in_branch[branch_key] = package

            if package.has_flag(PackageFlags.OUTDATED) and package.versionclass in (PackageStatus.UNIQUE, PackageStatus.NEWEST, PackageStatus.DEVEL):
                package.versionclass = PackageStatus.OUTDATED


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

    # Process altscheme and normal packages independently
    _fill_packageset_versions(
        [package for package in packages if package.flags & PackageFlags.ALTSCHEME],
        project_is_unique,
        project_should_unignore
    )
    _fill_packageset_versions(
        [package for package in packages if not package.flags & PackageFlags.ALTSCHEME],
        project_is_unique,
        project_should_unignore
    )


def packageset_sort_by_version(packages: Sequence[Package]) -> List[Package]:
    def compare(p1: Package, p2: Package) -> int:
        return p2.version_compare(p1)

    return sorted(packages, key=cmp_to_key(compare))
