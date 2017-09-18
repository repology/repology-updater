#!/usr/bin/env python3
#
# Copyright (C) 2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import unittest

from repology.package import Package, VersionClass
from repology.packageproc import FillPackagesetVersions


class TestPackageProc(unittest.TestCase):
    def test_version_classes(self):
        packages = [
            # Package A

            # Reference repo
            (Package(repo='1', family='1', name='a', version='2.2.20990101', ignoreversion=True), VersionClass.ignored),
            (Package(repo='1', family='1', name='a', version='2.2beta1', devel=True), VersionClass.devel),
            (Package(repo='1', family='1', name='a', version='2.2alpha1.20990101', ignoreversion=True), VersionClass.legacy),
            (Package(repo='1', family='1', name='a', version='2.2alpha1', devel=True), VersionClass.legacy),
            (Package(repo='1', family='1', name='a', version='2.1.20990101', ignoreversion=True), VersionClass.legacy),
            (Package(repo='1', family='1', name='a', version='2.1'), VersionClass.newest),
            (Package(repo='1', family='1', name='a', version='2.0.20990101', ignoreversion=True), VersionClass.legacy),
            (Package(repo='1', family='1', name='a', version='2.0'), VersionClass.legacy),

            (Package(repo='1', family='1', name='a', version='1.2.20990101', ignoreversion=True), VersionClass.legacy),
            (Package(repo='1', family='1', name='a', version='1.2beta1', devel=True), VersionClass.legacy),
            (Package(repo='1', family='1', name='a', version='1.2alpha1.20990101', ignoreversion=True), VersionClass.legacy),
            (Package(repo='1', family='1', name='a', version='1.2alpha1', devel=True), VersionClass.legacy),
            (Package(repo='1', family='1', name='a', version='1.1.20990101', ignoreversion=True), VersionClass.legacy),
            (Package(repo='1', family='1', name='a', version='1.1'), VersionClass.legacy),
            (Package(repo='1', family='1', name='a', version='1.0.20990101', ignoreversion=True), VersionClass.legacy),
            (Package(repo='1', family='1', name='a', version='1.0'), VersionClass.legacy),

            # devel + legacy
            (Package(repo='2', family='2', name='a', version='2.2beta1', devel=True), VersionClass.devel),
            (Package(repo='2', family='2', name='a', version='2.0'), VersionClass.legacy),

            # devel + newest + legacy
            (Package(repo='3', family='3', name='a', version='2.2beta1', devel=True), VersionClass.devel),
            (Package(repo='3', family='3', name='a', version='2.1'), VersionClass.newest),
            (Package(repo='3', family='3', name='a', version='2.0'), VersionClass.legacy),

            # newest + legacy
            (Package(repo='4', family='4', name='a', version='2.1'), VersionClass.newest),
            (Package(repo='4', family='4', name='a', version='2.0'), VersionClass.legacy),

            # outdated + legacy
            (Package(repo='5', family='5', name='a', version='1.1'), VersionClass.outdated),
            (Package(repo='5', family='5', name='a', version='1.0'), VersionClass.legacy),

            # outdated outdated/ignored + legacy
            (Package(repo='6', family='6', name='a', version='1.1.20990101', ignoreversion=True), VersionClass.outdated),
            (Package(repo='6', family='6', name='a', version='1.1'), VersionClass.outdated),
            (Package(repo='6', family='6', name='a', version='1.0'), VersionClass.legacy),

            # devel class should be ignored for newest version
            (Package(repo='7', family='7', name='a', version='2.1', devel=True), VersionClass.newest),

            # ignored classes are unignored when they are backed with real classes
            (Package(repo='8', family='8', name='a', version='2.2beta1', ignoreversion=True), VersionClass.devel),

            (Package(repo='9', family='9', name='a', version='2.1', ignoreversion=True), VersionClass.newest),

            (Package(repo='10', family='10', name='a', version='2.0', ignoreversion=True), VersionClass.outdated),
            (Package(repo='10', family='10', name='a', version='1.9', ignoreversion=True), VersionClass.outdated),
        ]

        FillPackagesetVersions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))


if __name__ == '__main__':
    unittest.main()
