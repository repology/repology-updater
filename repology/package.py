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

from repology.version import VersionCompare


class Package:
    def __init__(self):
        self.name = None
        self.version = None
        self.fullversion = None
        self.maintainers = []
        self.category = None
        self.comment = None
        self.homepage = None
        self.licenses = []
        self.downloads = []

        self.family = None
        self.ignoreversion = False


class MetaPackage:
    def __init__(self, name):
        self.name = name
        self.packages = {}
        self.versions = {}
        self.maintainers = set()

    def GetName(self):
        return self.name

    def Add(self, reponame, package):
        if reponame not in self.packages:
            self.packages[reponame] = []
        self.packages[reponame].append(package)

    def Get(self, reponame):
        if reponame in self.packages:
            return self.packages[reponame]
        return None

    def GetMaxVersion(self):
        bestversion, bestrepo, bestpackage = None, None, None
        for reponame, packagelist in self.packages.items():
            for package in packagelist:
                if package.version is not None and not package.ignoreversion:
                    if bestversion is None or VersionCompare(package.version, bestversion) > 0:
                        bestversion, bestrepo, bestpackage = package.version, reponame, package

        return bestversion, bestrepo, bestpackage

    def GetVersionRangeForRepo(self, reponame):
        if reponame not in self.packages:
            return None, None

        minversion, maxversion = None, None
        for package in self.packages[reponame]:
            if package.version is not None:
                if maxversion is None or VersionCompare(package.version, maxversion) > 0:
                    maxversion = package.version
                if minversion is None or VersionCompare(package.version, minversion) < 0:
                    minversion = package.version

        return minversion, maxversion

    def HasMaintainer(self, maintainer):
        return maintainer in self.maintainers

    def GetMaintainers(self):
        return self.maintainers

    def HasCategory(self, category):
        for packagelist in self.packages.values():
            for package in packagelist:
                if package.category == category:
                    return True

        return False

    def HasCategoryLike(self, category):
        for packagelist in self.packages.values():
            for package in packagelist:
                if package.category is not None and package.category.lower().find(category) != -1:
                    return True

        return False

    def GetNumRepos(self):
        return len(self.packages)

    def GetRepos(self):
        return self.packages.keys()

    def GetFamilies(self):
        families = set()

        for packagelist in self.packages.values():
            for package in packagelist:
                if package.family is not None:
                    families.add(package.family)

        return families

    def HasRepository(self, reponame):
        return reponame in self.packages

    def IsOutdatedInRepository(self, reponame):
        return reponame in self.versions and self.versions[reponame]['class'] == 'bad'

    def FillVersionData(self):
        # fill maintaiers
        for packagelist in self.packages.values():
            for package in packagelist:
                for maintainer in package.maintainers:
                    self.maintainers.add(maintainer)

        # fill versions
        bestversion, _, _ = self.GetMaxVersion()

        numfamilies = len(self.GetFamilies())

        for reponame in self.GetRepos():
            # packages for this repository
            repopackages = self.Get(reponame)

            # determine versions
            repominversion, repomaxversion = self.GetVersionRangeForRepo(reponame)

            bestrepopackage = repopackages[0]
            for package in repopackages:
                if package.version == repomaxversion:
                    bestrepopackage = package

            versionclass = 'bad'
            if bestversion is None:
                versionclass = 'good'
            elif VersionCompare(repomaxversion, bestversion) > 0:  # due to ignore
                versionclass = 'ignore'
            elif VersionCompare(repomaxversion, bestversion) >= 0:
                if VersionCompare(repominversion, bestversion) == 0:
                    versionclass = 'good'
                else:
                    versionclass = 'multi'

            if (versionclass == 'good' or versionclass == 'multi') and numfamilies == 1:
                versionclass = 'lonely'

            self.versions[reponame] = {
                'version': repomaxversion,
                'subpackage': bestrepopackage,
                'class': versionclass,
                'numpackages': len(repopackages)
            }
