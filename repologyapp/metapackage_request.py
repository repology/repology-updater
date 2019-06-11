# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Optional, Tuple


def split_range(s: str) -> Tuple[Optional[int], ...]:
    comps = s.split('-', 1)
    if len(comps) == 1:
        comps.append(comps[0])
    return tuple(int(comp) if comp.isdecimal() else None for comp in comps)


class MetapackageRequest:
    pivot: Optional[str]
    reverse: bool

    search: Optional[str]

    maintainer: Optional[str]

    min_repos: Optional[int]
    max_repos: Optional[int]
    min_families: Optional[int]
    max_families: Optional[int]
    min_repos_newest: Optional[int]
    max_repos_newest: Optional[int]
    min_families_newest: Optional[int]
    max_families_newest: Optional[int]

    inrepo: Optional[str]
    notinrepo: Optional[str]

    category: Optional[str]

    newest: bool
    outdated: bool
    problematic: bool
    has_related: bool

    def __init__(self) -> None:
        # effname filtering
        self.pivot = None
        self.reverse = False

        self.search = None

        # maintainer (maintainer_metapackages)
        self.maintainer = None

        # numbers (metapackages table)
        self.min_repos = None
        self.max_repos = None
        self.min_families = None
        self.max_families = None
        self.min_repos_newest = None
        self.max_repos_newest = None
        self.min_families_newest = None
        self.max_families_newest = None

        # repos (repo_metapackages)
        self.inrepo = None
        self.notinrepo = None

        # category
        self.category = None

        # flags
        self.newest = False
        self.outdated = False
        self.problematic = False
        self.has_related = False

    def set_bound(self, bound: Optional[str]) -> None:
        if not bound:
            pass
        elif bound.startswith('..'):
            self.require_name_to(bound[2:])
        else:
            self.require_name_from(bound)

    def require_name_from(self, name: Optional[str]) -> None:
        if self.pivot:
            raise RuntimeError('duplicate effname condition')
        if name is not None:
            self.pivot = name
            self.reverse = False

    def require_name_to(self, name: Optional[str]) -> None:
        if self.pivot:
            raise RuntimeError('duplicate effname condition')
        if name is not None:
            self.pivot = name
            self.reverse = True

    def require_name_substring(self, substring: str) -> None:
        if self.search:
            raise RuntimeError('duplicate effname substring condition')
        self.search = substring

    def require_maintainer(self, maintainer: str) -> None:
        if self.maintainer:
            raise RuntimeError('duplicate maintainer condition')
        self.maintainer = maintainer

    def require_in_repo(self, repo: str) -> None:
        if self.inrepo:
            raise RuntimeError('duplicate repository condition')
        self.inrepo = repo

    def require_not_in_repo(self, repo: str) -> None:
        if self.notinrepo:
            raise RuntimeError('duplicate not-in-repository condition')
        self.notinrepo = repo

    def require_category(self, category: str) -> None:
        if self.category:
            raise RuntimeError('duplicate category condition')
        self.category = category

    def require_repos(self, rng: str) -> None:
        self.min_repos, self.max_repos = split_range(rng)

    def require_families(self, rng: str) -> None:
        self.min_families, self.max_families = split_range(rng)

    def require_repos_newest(self, rng: str) -> None:
        self.min_repos_newest, self.max_repos_newest = split_range(rng)

    def require_families_newest(self, rng: str) -> None:
        self.min_families_newest, self.max_families_newest = split_range(rng)

    def require_newest(self) -> None:
        self.newest = True

    def require_outdated(self) -> None:
        self.outdated = True

    def require_problematic(self) -> None:
        self.problematic = True

    def require_has_related(self) -> None:
        self.has_related = True
