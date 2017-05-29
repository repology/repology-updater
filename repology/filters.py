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

from repology.package import PackageVersionClass


class MaintainerFilter:
    def __init__(self, maintainer):
        self.maintainer = maintainer

    def Check(self, packages):
        for package in packages:
            if package.ignored:
                continue

            if self.maintainer in package.maintainers:
                return True

        return False


class CategoryFilter:
    def __init__(self, category):
        self.category = category

    def Check(self, packages):
        for package in packages:
            if package.category and package.category.lower().find(self.category) != -1:
                return True

        return False


class FamilyCountFilter:
    def __init__(self, more=None, less=None):
        self.more = more
        self.less = less

    def Check(self, packages):
        families = set()

        for package in packages:
            families.add(package.family)

        if self.more is not None and len(families) >= self.more:
            return True
        if self.less is not None and len(families) <= self.less:
            return True

        return False


class RepoCountFilter:
    def __init__(self, more=None, less=None):
        self.more = more
        self.less = less

    def Check(self, packages):
        repos = set()

        for package in packages:
            repos.add(package.repo)

        if self.more is not None and len(repos) >= self.more:
            return True
        if self.less is not None and len(repos) <= self.less:
            return True

        return False


class InRepoFilter:
    def __init__(self, repo):
        self.repo = repo

    def Check(self, packages):
        for package in packages:
            if package.repo == self.repo:
                return True

        return False


class NotInRepoFilter:
    def __init__(self, repo):
        self.repo = repo

    def Check(self, packages):
        for package in packages:
            if package.repo == self.repo:
                return False

        return True


class OutdatedInRepoFilter:
    def __init__(self, repo):
        self.repo = repo

    def Check(self, packages):
        for package in packages:
            if package.repo == self.repo and package.versionclass == PackageVersionClass.outdated:
                return True

        return False


class ShadowFilter:
    def __init__(self):
        pass

    def Check(self, packages):
        for package in packages:
            if not package.shadow:
                return True

        return False


class InAnyRepoFilter:
    def __init__(self, reponames):
        self.reponames = set()
        for reponame in reponames:
            self.reponames.add(reponame)

    def Check(self, packages):
        for package in packages:
            if package.repo in self.reponames:
                return True

        return False
