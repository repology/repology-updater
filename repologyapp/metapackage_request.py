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


def split_range(s):
    comps = s.split('-', 1)
    if len(comps) == 1:
        comps.append(comps[0])
    return tuple(int(comp) if comp.isdecimal() else None for comp in comps)


class MetapackageRequest:
    def __init__(self):
        # effname filtering
        self.pivot = None
        self.reverse = False

        self.search = None

        # package (packages table)
        self.package = None

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

    def Bound(self, bound):
        if not bound:
            pass
        elif bound.startswith('..'):
            self.NameTo(bound[2:])
        else:
            self.NameFrom(bound)

    def NameFrom(self, name):
        if self.pivot:
            raise RuntimeError('duplicate effname condition')
        if name is not None:
            self.pivot = name
            self.reverse = False

    def NameTo(self, name):
        if self.pivot:
            raise RuntimeError('duplicate effname condition')
        if name is not None:
            self.pivot = name
            self.reverse = True

    def NameSubstring(self, substring):
        if self.search:
            raise RuntimeError('duplicate effname substring condition')
        self.search = substring

    def Package(self, substring):
        if self.package:
            raise RuntimeError('duplicate package substring condition')
        self.package = substring

    def Maintainer(self, maintainer):
        if self.maintainer:
            raise RuntimeError('duplicate maintainer condition')
        self.maintainer = maintainer

    def InRepo(self, repo):
        if self.inrepo:
            raise RuntimeError('duplicate repository condition')
        self.inrepo = repo

    def NotInRepo(self, repo):
        if self.notinrepo:
            raise RuntimeError('duplicate not-in-repository condition')
        self.notinrepo = repo

    def Category(self, category):
        if self.category:
            raise RuntimeError('duplicate category condition')
        self.category = category

    def Repos(self, rng):
        self.min_repos, self.max_repos = split_range(rng)

    def Families(self, rng):
        self.min_families, self.max_families = split_range(rng)

    def ReposNewest(self, rng):
        self.min_repos_newest, self.max_repos_newest = split_range(rng)

    def FamiliesNewest(self, rng):
        self.min_families_newest, self.max_families_newest = split_range(rng)

    def Newest(self):
        self.newest = True

    def Outdated(self):
        self.outdated = True

    def Problematic(self):
        self.problematic = True

    def HasRelated(self):
        self.has_related = True
