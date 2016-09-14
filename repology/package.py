# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from .util import VersionCompare

class Package:
    def __init__(self):
        self.name = None
        self.version = None
        self.fullversion = None
        self.maintainer = None
        self.category = None
        self.comment = None
        self.homepage = None
        self.license = None
        pass

class MetaPackage:
    def __init__(self):
        self.packages = {}
        pass

    def Add(self, reponame, package):
        self.packages[reponame] = package

    def Get(self, reponame):
        if reponame in self.packages:
            return self.packages[reponame]
        return None

    def GetMaxVersion(self):
        bestversion, bestrepo, bestpackage = None, None, None
        for reponame, package in self.packages.items():
            if package.version is not None:
                if bestversion is None or VersionCompare(package.version, bestversion) > 0:
                    bestversion, bestrepo, bestpackage = package.version, reponame, package

        return bestversion, bestrepo, bestpackage

    def HasMaintainer(self, maintainer):
        for package in self.packages.values():
            if package.maintainer == maintainer:
                return True

        return False

    def GetMaintainers(self):
        maintainers = []
        for package in self.packages.values():
            if package.maintainer is not None:
                maintainer.append(package.maintainer)

        return maintainers

    def HasCategory(self, category):
        for package in self.packages.values():
            if package.category == category:
                return True

        return False

    def HasCategoryLike(self, category):
        for package in self.packages.values():
            if package.category is not None and package.category.find(category) != -1:
                return True

        return False

    def GetNumRepos(self):
        return len(self.packages)

    def HasRepository(self, reponame):
        return reponame in self.packages
