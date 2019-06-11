#!/usr/bin/env python3
#
# Copyright (C) 2017-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.package import Package, PackageFlags, PackageStatus
from repology.packageproc import fill_packageset_versions, packageset_is_unique


class TestPackageProc(unittest.TestCase):
    def test_packageset_is_unique(self):
        packages = []
        self.assertEqual(packageset_is_unique(packages), True)

        packages = [Package(family='foo')]
        self.assertEqual(packageset_is_unique(packages), True)

        packages = [Package(family='foo'), Package(family='foo')]
        self.assertEqual(packageset_is_unique(packages), True)

        packages = [Package(family='foo'), Package(family='bar')]
        self.assertEqual(packageset_is_unique(packages), False)

    def test_versionclasses_big(self):
        packages = [
            # Reference repo
            (Package(repo='1', family='1', name='a', version='2.2.20990101', flags=PackageFlags.IGNORE), PackageStatus.IGNORED),
            (Package(repo='1', family='1', name='a', version='2.2beta1', flags=PackageFlags.DEVEL), PackageStatus.DEVEL),
            (Package(repo='1', family='1', name='a', version='2.2alpha1.20990101', flags=PackageFlags.DEVEL | PackageFlags.IGNORE), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='2.2alpha1', flags=PackageFlags.DEVEL), PackageStatus.LEGACY),
            # see #338. There are multiple possible ways to ignored version between branches,
            # we go with ignored for now
            (Package(repo='1', family='1', name='a', version='2.1.20990101', flags=PackageFlags.IGNORE), PackageStatus.IGNORED),
            (Package(repo='1', family='1', name='a', version='2.1'), PackageStatus.NEWEST),
            (Package(repo='1', family='1', name='a', version='2.0.20990101', flags=PackageFlags.IGNORE), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='2.0'), PackageStatus.LEGACY),

            (Package(repo='1', family='1', name='a', version='1.2.20990101', flags=PackageFlags.IGNORE), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='1.2beta1', flags=PackageFlags.DEVEL), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='1.2alpha1.20990101', flags=PackageFlags.DEVEL | PackageFlags.IGNORE), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='1.2alpha1', flags=PackageFlags.DEVEL), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='1.1.20990101', flags=PackageFlags.IGNORE), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='1.1'), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='1.0.20990101', flags=PackageFlags.IGNORE), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='1.0'), PackageStatus.LEGACY),

            # devel + legacy
            (Package(repo='2', family='2', name='a', version='2.2beta1', flags=PackageFlags.DEVEL), PackageStatus.DEVEL),
            (Package(repo='2', family='2', name='a', version='2.0'), PackageStatus.OUTDATED),

            # devel + newest + legacy
            (Package(repo='3', family='3', name='a', version='2.2beta1', flags=PackageFlags.DEVEL), PackageStatus.DEVEL),
            (Package(repo='3', family='3', name='a', version='2.1'), PackageStatus.NEWEST),
            (Package(repo='3', family='3', name='a', version='2.0'), PackageStatus.LEGACY),

            # newest + legacy
            (Package(repo='4', family='4', name='a', version='2.1'), PackageStatus.NEWEST),
            (Package(repo='4', family='4', name='a', version='2.0'), PackageStatus.LEGACY),

            # outdated + legacy
            (Package(repo='5', family='5', name='a', version='1.1'), PackageStatus.OUTDATED),
            (Package(repo='5', family='5', name='a', version='1.0'), PackageStatus.LEGACY),

            # outdated outdated/ignored + legacy
            (Package(repo='6', family='6', name='a', version='1.1.20990101', flags=PackageFlags.IGNORE), PackageStatus.OUTDATED),
            (Package(repo='6', family='6', name='a', version='1.1'), PackageStatus.LEGACY),
            (Package(repo='6', family='6', name='a', version='1.0'), PackageStatus.LEGACY),

            # ignored classes are unignored when they are backed with real classes
            (Package(repo='8', family='8', name='a', version='2.2beta1', flags=PackageFlags.DEVEL | PackageFlags.IGNORE), PackageStatus.DEVEL),

            (Package(repo='9', family='9', name='a', version='2.1', flags=PackageFlags.IGNORE), PackageStatus.NEWEST),

            (Package(repo='10', family='10', name='a', version='2.0', flags=PackageFlags.IGNORE), PackageStatus.OUTDATED),
            (Package(repo='10', family='10', name='a', version='1.9', flags=PackageFlags.IGNORE), PackageStatus.LEGACY),

            # version between newest and devel should be outdated when there's no devel
            (Package(repo='11', family='11', name='a', version='2.2alpha1', flags=PackageFlags.DEVEL), PackageStatus.OUTDATED),

            # outdated in devel and normal at the same time
            (Package(repo='12', family='12', name='a', version='2.2alpha1', flags=PackageFlags.DEVEL), PackageStatus.OUTDATED),
            (Package(repo='12', family='12', name='a', version='2.0'), PackageStatus.OUTDATED),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_versionclass_single_branch1(self):
        packages = [
            # here we only have default branch
            (Package(repo='1', family='1', name='a', version='2.2.20990101', flags=PackageFlags.IGNORE), PackageStatus.IGNORED),
            (Package(repo='1', family='1', name='a', version='2.1'), PackageStatus.NEWEST),
            (Package(repo='1', family='1', name='a', version='2.0.20990101', flags=PackageFlags.IGNORE), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='2.0'), PackageStatus.LEGACY),

            (Package(repo='2', family='2', name='a', version='2.1'), PackageStatus.NEWEST),
            (Package(repo='2', family='2', name='a', version='2.0'), PackageStatus.LEGACY),

            (Package(repo='3', family='3', name='a', version='2.0'), PackageStatus.OUTDATED),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_versionclass_single_branch2(self):
        packages = [
            # here we only have devel branch
            (Package(repo='1', family='1', name='a', version='2.2rc1.20990101', flags=PackageFlags.IGNORE | PackageFlags.DEVEL), PackageStatus.IGNORED),
            (Package(repo='1', family='1', name='a', version='2.2beta1', flags=PackageFlags.DEVEL), PackageStatus.DEVEL),
            (Package(repo='1', family='1', name='a', version='2.2alpha1.20990101', flags=PackageFlags.IGNORE | PackageFlags.DEVEL), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='2.2alpha1', flags=PackageFlags.DEVEL), PackageStatus.LEGACY),

            (Package(repo='2', family='2', name='a', version='2.2beta1', flags=PackageFlags.DEVEL), PackageStatus.DEVEL),
            (Package(repo='2', family='2', name='a', version='2.2alpha1', flags=PackageFlags.DEVEL), PackageStatus.LEGACY),

            (Package(repo='3', family='3', name='a', version='2.2alpha1', flags=PackageFlags.DEVEL), PackageStatus.OUTDATED),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_versionclass_branch_confusion(self):
        packages = [
            # same version is both devel and default in different packages
            # this should be consistently aggregated
            (Package(repo='1', family='1', name='a', version='2.1', flags=PackageFlags.DEVEL), PackageStatus.DEVEL),
            (Package(repo='1', family='1', name='a', version='2.0', flags=PackageFlags.DEVEL), PackageStatus.LEGACY),

            (Package(repo='2', family='2', name='a', version='2.1'), PackageStatus.DEVEL),
            (Package(repo='2', family='2', name='a', version='2.0'), PackageStatus.LEGACY),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_versionclass_devel_lower_than_default(self):
        packages = [
            # devel package < normal package
            (Package(repo='1', family='1', name='a', version='2.1'), PackageStatus.NEWEST),
            (Package(repo='1', family='1', name='a', version='2.0', flags=PackageFlags.DEVEL), PackageStatus.LEGACY),

            (Package(repo='2', family='2', name='a', version='2.1'), PackageStatus.NEWEST),
            (Package(repo='2', family='2', name='a', version='2.0', flags=PackageFlags.DEVEL), PackageStatus.LEGACY),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_versionclass_unignored_really_unignored(self):
        packages = [
            # ignored package should be fully unignored with the same non-ignored version in another repo
            (Package(repo='1', family='1', name='a', version='2.1', flags=PackageFlags.IGNORE), PackageStatus.NEWEST),
            (Package(repo='1', family='1', name='a', version='2.0'), PackageStatus.LEGACY),

            (Package(repo='2', family='2', name='a', version='2.1'), PackageStatus.NEWEST),
            (Package(repo='2', family='2', name='a', version='2.0'), PackageStatus.LEGACY),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_versionclass_unique(self):
        packages = [
            (Package(repo='1', family='1', name='a', version='2.0alpha1', flags=PackageFlags.DEVEL), PackageStatus.UNIQUE),
            (Package(repo='2', family='1', name='a', version='1.2'), PackageStatus.UNIQUE),
            (Package(repo='3', family='1', name='a', version='1.1'), PackageStatus.OUTDATED),
            (Package(repo='3', family='1', name='a', version='1.0'), PackageStatus.LEGACY),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_versionclass_branch_bounds(self):
        packages = [
            (Package(repo='1', family='1', name='a', version='2.2beta1', flags=PackageFlags.DEVEL), PackageStatus.DEVEL),
            (Package(repo='1', family='1', name='a', version='2.2alpha1.9999', flags=PackageFlags.IGNORE | PackageFlags.DEVEL), PackageStatus.LEGACY),
            # see #338. There are multiple possible ways to ignored version between branches,
            # we go with ignored for now
            (Package(repo='1', family='1', name='a', version='2.1.9999', flags=PackageFlags.IGNORE), PackageStatus.IGNORED),
            (Package(repo='1', family='1', name='a', version='2.1'), PackageStatus.NEWEST),
            (Package(repo='1', family='1', name='a', version='2.0'), PackageStatus.LEGACY),

            (Package(repo='2', family='2', name='a', version='2.1'), PackageStatus.NEWEST),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_versionclass_ignoredignored(self):
        packages = [
            (Package(repo='1', family='1', name='a', version='2.2.99999999', flags=PackageFlags.IGNORE), PackageStatus.IGNORED),
            (Package(repo='1', family='1', name='a', version='2.2.9999', flags=PackageFlags.IGNORE), PackageStatus.IGNORED),
            # this one should be outdated, not legacy, e.g. ignored's should not be counted
            # as first packages in the branch
            (Package(repo='1', family='1', name='a', version='2.1'), PackageStatus.OUTDATED),
            (Package(repo='1', family='1', name='a', version='2.0'), PackageStatus.LEGACY),

            (Package(repo='2', family='2', name='a', version='2.2'), PackageStatus.NEWEST),

        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_versionclass_sameversionsamestatus(self):
        packages = [
            (Package(repo='2', family='2', name='a', version='2.2'), PackageStatus.NEWEST),
            # one of these packages should not make the other one legacy instead of outdated
            (Package(repo='1', family='1', name='a', version='2.1'), PackageStatus.OUTDATED),
            (Package(repo='1', family='1', name='a', version='2.1'), PackageStatus.OUTDATED),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_versionclass_manylegacy(self):
        packages = [
            (Package(repo='2', family='2', name='a', version='2.2'), PackageStatus.NEWEST),
            # one of these packages should not make the other one legacy instead of outdated
            (Package(repo='1', family='1', name='a', version='2.1'), PackageStatus.OUTDATED),
            (Package(repo='1', family='1', name='a', version='2.0'), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='2.0'), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='1.9'), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='1.9'), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='1.8'), PackageStatus.LEGACY),
            (Package(repo='1', family='1', name='a', version='1.8'), PackageStatus.LEGACY),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_versionclass_flavors(self):
        packages = [
            (Package(repo='1', family='1', name='a', version='2.2'), PackageStatus.NEWEST),

            (Package(repo='2', family='2', name='a', version='2.1'), PackageStatus.OUTDATED),
            (Package(repo='2', family='2', name='a', version='2.0'), PackageStatus.LEGACY),

            (Package(repo='3', family='3', name='a', version='2.1'), PackageStatus.OUTDATED),
            (Package(repo='3', family='3', name='a', version='2.0', flavors=['foo']), PackageStatus.OUTDATED),

            (Package(repo='4', family='4', name='a', version='2.1', flavors=['foo']), PackageStatus.OUTDATED),
            (Package(repo='4', family='4', name='a', version='2.0'), PackageStatus.OUTDATED),

            (Package(repo='5', family='5', name='a', version='2.1', flavors=['foo']), PackageStatus.OUTDATED),
            (Package(repo='5', family='5', name='a', version='2.0', flavors=['foo']), PackageStatus.LEGACY),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_versionclass_outdated(self):
        packages = [
            (Package(repo='1', family='1', name='a', version='1.0'), PackageStatus.NEWEST),

            (Package(repo='2', family='2', name='a', version='1.0', flags=PackageFlags.OUTDATED), PackageStatus.OUTDATED),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_versionclass_legacy(self):
        packages = [
            (Package(repo='1', family='1', name='a', version='2.0'), PackageStatus.NEWEST),

            (Package(repo='2', family='2', name='a', version='1.0'), PackageStatus.OUTDATED),

            (Package(repo='3', family='3', name='a', version='1.0', flags=PackageFlags.LEGACY), PackageStatus.LEGACY),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_suppress_ignored(self):
        packages = [
            (Package(repo='1', family='1', name='a', version='2.0', flags=PackageFlags.IGNORE), PackageStatus.UNIQUE),
            (Package(repo='2', family='1', name='a', version='1.0', flags=PackageFlags.IGNORE), PackageStatus.OUTDATED),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))

    def test_suppress_ignored_rolling(self):
        packages = [
            (Package(repo='0', family='0', name='a', version='3.0', flags=PackageFlags.ROLLING), PackageStatus.ROLLING),
            (Package(repo='1', family='1', name='a', version='2.0', flags=PackageFlags.IGNORE), PackageStatus.NEWEST),
            (Package(repo='2', family='1', name='a', version='1.0', flags=PackageFlags.IGNORE), PackageStatus.OUTDATED),
        ]

        fill_packageset_versions([package for package, _ in packages])

        for package, expectedclass in packages:
            self.assertEqual(package.versionclass, expectedclass, msg='repo {}, pkg {}, ver {}'.format(package.repo, package.name, package.version))


if __name__ == '__main__':
    unittest.main()
