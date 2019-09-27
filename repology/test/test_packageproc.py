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

# mypy: no-disallow-untyped-calls

import unittest
from typing import List

from repology.package import Package
from repology.package import PackageFlags as Pf
from repology.package import PackageStatus as Ps
from repology.packageproc import fill_packageset_versions, packageset_is_unique

from .package import PackageSample, spawn_package


class TestPackageProc(unittest.TestCase):
    def _check_fill_versions(self, *samples: PackageSample) -> None:
        fill_packageset_versions([sample.package for sample in samples])

        for sample in samples:
            sample.check(self)

    def test_packageset_is_unique(self) -> None:
        packages: List[Package] = []
        self.assertEqual(packageset_is_unique(packages), True)

        packages = [spawn_package(family='foo')]
        self.assertEqual(packageset_is_unique(packages), True)

        packages = [spawn_package(family='foo'), spawn_package(family='foo')]
        self.assertEqual(packageset_is_unique(packages), True)

        packages = [spawn_package(family='foo'), spawn_package(family='bar')]
        self.assertEqual(packageset_is_unique(packages), False)

    def test_versionclasses_big(self) -> None:
        self._check_fill_versions(
            # Reference repo
            PackageSample(repo='1', version='2.2.20990101', flags=Pf.IGNORE).expect(versionclass=Ps.IGNORED),
            PackageSample(repo='1', version='2.2beta1', flags=Pf.DEVEL).expect(versionclass=Ps.DEVEL),
            PackageSample(repo='1', version='2.2alpha1.20990101', flags=Pf.DEVEL | Pf.IGNORE).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='2.2alpha1', flags=Pf.DEVEL).expect(versionclass=Ps.LEGACY),
            # see #338. There are multiple possible ways to ignored version between branches,
            # we go with ignored for now
            PackageSample(repo='1', version='2.1.20990101', flags=Pf.IGNORE).expect(versionclass=Ps.IGNORED),
            PackageSample(repo='1', version='2.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='2.0.20990101', flags=Pf.IGNORE).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='2.0').expect(versionclass=Ps.LEGACY),

            PackageSample(repo='1', version='1.2.20990101', flags=Pf.IGNORE).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='1.2beta1', flags=Pf.DEVEL).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='1.2alpha1.20990101', flags=Pf.DEVEL | Pf.IGNORE).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='1.2alpha1', flags=Pf.DEVEL).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='1.1.20990101', flags=Pf.IGNORE).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='1.1').expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='1.0.20990101', flags=Pf.IGNORE).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='1.0').expect(versionclass=Ps.LEGACY),

            # devel + legacy
            PackageSample(repo='2', version='2.2beta1', flags=Pf.DEVEL).expect(versionclass=Ps.DEVEL),
            PackageSample(repo='2', version='2.0').expect(versionclass=Ps.OUTDATED),

            # devel + newest + legacy
            PackageSample(repo='3', version='2.2beta1', flags=Pf.DEVEL).expect(versionclass=Ps.DEVEL),
            PackageSample(repo='3', version='2.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='3', version='2.0').expect(versionclass=Ps.LEGACY),

            # newest + legacy
            PackageSample(repo='4', version='2.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='4', version='2.0').expect(versionclass=Ps.LEGACY),

            # outdated + legacy
            PackageSample(repo='5', version='1.1').expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='5', version='1.0').expect(versionclass=Ps.LEGACY),

            # outdated outdated/ignored + legacy
            PackageSample(repo='6', version='1.1.20990101', flags=Pf.IGNORE).expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='6', version='1.1').expect(versionclass=Ps.LEGACY),
            PackageSample(repo='6', version='1.0').expect(versionclass=Ps.LEGACY),

            # ignored classes are unignored when they are backed with real classes
            PackageSample(repo='8', version='2.2beta1', flags=Pf.DEVEL | Pf.IGNORE).expect(versionclass=Ps.DEVEL),

            PackageSample(repo='9', version='2.1', flags=Pf.IGNORE).expect(versionclass=Ps.NEWEST),

            PackageSample(repo='10', version='2.0', flags=Pf.IGNORE).expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='10', version='1.9', flags=Pf.IGNORE).expect(versionclass=Ps.LEGACY),

            # version between newest and devel should be outdated when there's no devel
            PackageSample(repo='11', version='2.2alpha1', flags=Pf.DEVEL).expect(versionclass=Ps.OUTDATED),

            # outdated in devel and normal at the same time
            PackageSample(repo='12', version='2.2alpha1', flags=Pf.DEVEL).expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='12', version='2.0').expect(versionclass=Ps.OUTDATED),
        )

    def test_versionclass_single_branch1(self) -> None:
        self._check_fill_versions(
            # here we only have default branch
            PackageSample(repo='1', version='2.2.20990101', flags=Pf.IGNORE).expect(versionclass=Ps.IGNORED),
            PackageSample(repo='1', version='2.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='2.0.20990101', flags=Pf.IGNORE).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='2.0').expect(versionclass=Ps.LEGACY),

            PackageSample(repo='2', version='2.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='2', version='2.0').expect(versionclass=Ps.LEGACY),

            PackageSample(repo='3', version='2.0').expect(versionclass=Ps.OUTDATED),
        )

    def test_versionclass_single_branch2(self) -> None:
        self._check_fill_versions(
            # here we only have devel branch
            PackageSample(repo='1', version='2.2rc1.20990101', flags=Pf.IGNORE | Pf.DEVEL).expect(versionclass=Ps.IGNORED),
            PackageSample(repo='1', version='2.2beta1', flags=Pf.DEVEL).expect(versionclass=Ps.DEVEL),
            PackageSample(repo='1', version='2.2alpha1.20990101', flags=Pf.IGNORE | Pf.DEVEL).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='2.2alpha1', flags=Pf.DEVEL).expect(versionclass=Ps.LEGACY),

            PackageSample(repo='2', version='2.2beta1', flags=Pf.DEVEL).expect(versionclass=Ps.DEVEL),
            PackageSample(repo='2', version='2.2alpha1', flags=Pf.DEVEL).expect(versionclass=Ps.LEGACY),

            PackageSample(repo='3', version='2.2alpha1', flags=Pf.DEVEL).expect(versionclass=Ps.OUTDATED),
        )

    def test_hard_devel(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='2.1', flags=Pf.DEVEL).expect(versionclass=Ps.DEVEL),
            PackageSample(repo='1', version='2.0', flags=Pf.DEVEL).expect(versionclass=Ps.LEGACY),

            PackageSample(repo='2', version='2.1').expect(versionclass=Ps.DEVEL),
            PackageSample(repo='2', version='2.0').expect(versionclass=Ps.LEGACY),
        )

    def test_stable(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='2.1', flags=Pf.DEVEL).expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='2.0', flags=Pf.DEVEL).expect(versionclass=Ps.LEGACY),

            PackageSample(repo='2', version='2.1', flags=Pf.STABLE).expect(versionclass=Ps.NEWEST),
            PackageSample(repo='2', version='2.0').expect(versionclass=Ps.LEGACY),
        )

    def test_weak_devel1(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='2.1', flags=Pf.WEAK_DEVEL).expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='2.0', flags=Pf.WEAK_DEVEL).expect(versionclass=Ps.LEGACY),

            PackageSample(repo='2', version='2.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='2', version='2.0').expect(versionclass=Ps.LEGACY),
        )

    def test_weak_devel2(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='2.1', flags=Pf.WEAK_DEVEL).expect(versionclass=Ps.DEVEL),
            PackageSample(repo='1', version='2.0', flags=Pf.WEAK_DEVEL).expect(versionclass=Ps.NEWEST),
            PackageSample(repo='2', version='2.0').expect(versionclass=Ps.NEWEST),
        )

    def test_versionclass_devel_lower_than_default(self) -> None:
        self._check_fill_versions(
            # devel package < normal package
            PackageSample(repo='1', version='2.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='2.0', flags=Pf.DEVEL).expect(versionclass=Ps.LEGACY),

            PackageSample(repo='2', version='2.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='2', version='2.0', flags=Pf.DEVEL).expect(versionclass=Ps.LEGACY),
        )

    def test_versionclass_unignored_really_unignored(self) -> None:
        self._check_fill_versions(
            # ignored package should be fully unignored with the same non-ignored version in another repo
            PackageSample(repo='1', version='2.1', flags=Pf.IGNORE).expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='2.0').expect(versionclass=Ps.LEGACY),

            PackageSample(repo='2', version='2.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='2', version='2.0').expect(versionclass=Ps.LEGACY),
        )

    def test_versionclass_unique(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', family='1', version='2.0alpha1', flags=Pf.DEVEL).expect(versionclass=Ps.UNIQUE),
            PackageSample(repo='2', family='1', version='1.2').expect(versionclass=Ps.UNIQUE),
            PackageSample(repo='3', family='1', version='1.1').expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='3', family='1', version='1.0').expect(versionclass=Ps.LEGACY),
        )

    def test_versionclass_branch_bounds(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='2.2beta1', flags=Pf.DEVEL).expect(versionclass=Ps.DEVEL),
            PackageSample(repo='1', version='2.2alpha1.9999', flags=Pf.IGNORE | Pf.DEVEL).expect(versionclass=Ps.LEGACY),
            # see #338. There are multiple possible ways to ignored version between branches,
            # we go with ignored for now
            PackageSample(repo='1', version='2.1.9999', flags=Pf.IGNORE).expect(versionclass=Ps.IGNORED),
            PackageSample(repo='1', version='2.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='2.0').expect(versionclass=Ps.LEGACY),

            PackageSample(repo='2', version='2.1').expect(versionclass=Ps.NEWEST),
        )

    def test_versionclass_branch_bounds2(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='2.2beta1', flags=Pf.DEVEL).expect(versionclass=Ps.DEVEL),
            # despite the following package is not devel, it should not end devel branch because it's ignored
            PackageSample(repo='1', version='2.1.9999', flags=Pf.IGNORE).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='2.1.pre1', flags=Pf.DEVEL).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='2.0').expect(versionclass=Ps.NEWEST),

            PackageSample(repo='2', version='2.0').expect(versionclass=Ps.NEWEST),
        )

    def test_versionclass_branch_bounds3(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='2.0beta1', flags=Pf.DEVEL).expect(versionclass=Ps.DEVEL),
            # in absense of main branch, trailing ingnored versions should be assigned to devel
            PackageSample(repo='2', version='0.9999', flags=Pf.IGNORE).expect(versionclass=Ps.OUTDATED),
        )

    def test_versionclass_ignoredignored(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='2.2.99999999', flags=Pf.IGNORE).expect(versionclass=Ps.IGNORED),
            PackageSample(repo='1', version='2.2.9999', flags=Pf.IGNORE).expect(versionclass=Ps.IGNORED),
            # this one should be outdated, not legacy, e.g. ignored's should not be counted
            # as first packages in the branch
            PackageSample(repo='1', version='2.1').expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='1', version='2.0').expect(versionclass=Ps.LEGACY),

            PackageSample(repo='2', version='2.2').expect(versionclass=Ps.NEWEST),

        )

    def test_versionclass_sameversionsamestatus(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='2', version='2.2').expect(versionclass=Ps.NEWEST),
            # one of these packages should not make the other one legacy instead of outdated
            PackageSample(repo='1', version='2.1').expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='1', version='2.1').expect(versionclass=Ps.OUTDATED),
        )

    def test_versionclass_manylegacy(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='2', version='2.2').expect(versionclass=Ps.NEWEST),
            # one of these packages should not make the other one legacy instead of outdated
            PackageSample(repo='1', version='2.1').expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='1', version='2.0').expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='2.0').expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='1.9').expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='1.9').expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='1.8').expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='1.8').expect(versionclass=Ps.LEGACY),
        )

    def test_versionclass_flavors(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='2.2').expect(versionclass=Ps.NEWEST),

            PackageSample(repo='2', version='2.1').expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='2', version='2.0').expect(versionclass=Ps.LEGACY),

            PackageSample(repo='3', version='2.1').expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='3', version='2.0', flavors=['foo']).expect(versionclass=Ps.OUTDATED),

            PackageSample(repo='4', version='2.1', flavors=['foo']).expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='4', version='2.0').expect(versionclass=Ps.OUTDATED),

            PackageSample(repo='5', version='2.1', flavors=['foo']).expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='5', version='2.0', flavors=['foo']).expect(versionclass=Ps.LEGACY),
        )

    def test_versionclass_outdated(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='1.0').expect(versionclass=Ps.NEWEST),

            PackageSample(repo='2', version='1.0', flags=Pf.OUTDATED).expect(versionclass=Ps.OUTDATED),
        )

    def test_versionclass_legacy(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='2.0').expect(versionclass=Ps.NEWEST),

            PackageSample(repo='2', version='1.0').expect(versionclass=Ps.OUTDATED),

            PackageSample(repo='3', version='1.0', flags=Pf.LEGACY).expect(versionclass=Ps.LEGACY),
        )

    def test_suppress_ignored(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', family='1', version='2.0', flags=Pf.IGNORE).expect(versionclass=Ps.UNIQUE),
            PackageSample(repo='2', family='1', version='1.0', flags=Pf.IGNORE).expect(versionclass=Ps.OUTDATED),
        )

    def test_suppress_ignored_rolling(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='0', family='0', version='3.0', flags=Pf.ROLLING).expect(versionclass=Ps.ROLLING),
            PackageSample(repo='1', family='1', version='2.0', flags=Pf.IGNORE).expect(versionclass=Ps.NEWEST),
            PackageSample(repo='2', family='1', version='1.0', flags=Pf.IGNORE).expect(versionclass=Ps.OUTDATED),
        )


if __name__ == '__main__':
    unittest.main()
