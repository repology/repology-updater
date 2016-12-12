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

from repology.packageproc import *


def PackagesToMetapackages(*packagess):
    metapackages = {}

    for packages in packagess:
        for package in packages:
            if package.effname not in metapackages:
                metapackages[package.effname] = []
            metapackages[package.effname].append(package)

    return metapackages


def FilterMetapackages(metapackages, *filters):
    filtered_metapackages = {}

    for name, packages in metapackages.items():
        passes = True
        for filt in filters:
            if not filt.Check(packages):
                passes = False
                break
        if passes:
            filtered_metapackages[name] = packages

    return filtered_metapackages


def FillMetapackagesVersions(metapackages):
    for packageset in metapackages.values():
        FillVersionInfos(packageset)


def MetapackagesToMetasummaries(metapackages):
    metasummaries = {}

    for metapackage_name, packageset in metapackages.items():
        metasummaries[metapackage_name] = PackagesetToSummaries(packageset)

    return metasummaries
