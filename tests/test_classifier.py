#!/usr/bin/env python3
#
# Copyright (C) 2017-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.classifier import classify_packages
from repology.package import PackageFlags as Pf
from repology.package import PackageStatus as Ps

from .package import PackageSample


class TestPackageProc(unittest.TestCase):
    def _check_fill_versions(self, *samples: PackageSample) -> None:
        classify_packages([sample.package for sample in samples])

        for sample in samples:
            sample.check(self)

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

    def test_versionclass_branch_bounds1(self) -> None:
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
            # In the past, the following package was assigned to devel section in absence of stable
            # section. I don't see a point in that - it looks more like ignored status should be honored
            # Real world cases to check out:
            # - goldendict
            # - libadwaita
            PackageSample(repo='2', version='0.9999', flags=Pf.IGNORE).expect(versionclass=Ps.IGNORED),
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

            PackageSample(repo='2', version='1.0', flags=Pf.SINK).expect(versionclass=Ps.OUTDATED),
        )

    def test_versionclass_legacy(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='2.0').expect(versionclass=Ps.NEWEST),

            PackageSample(repo='2', version='1.0').expect(versionclass=Ps.OUTDATED),

            PackageSample(repo='3', version='1.0', flags=Pf.LEGACY).expect(versionclass=Ps.LEGACY),
        )

    def test_versionclass_nolegacy(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='2.0').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='1.0', flags=Pf.NOLEGACY).expect(versionclass=Ps.OUTDATED),

            PackageSample(repo='2', version='2.0').expect(versionclass=Ps.NEWEST),
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

    def test_suppress_ignored_noscheme(self) -> None:
        # should not suppress noscheme
        self._check_fill_versions(
            PackageSample(repo='0', family='1', version='1.0', flags=Pf.NOSCHEME).expect(versionclass=Ps.NOSCHEME),
            PackageSample(repo='1', family='1', version='2.0', flags=Pf.NOSCHEME).expect(versionclass=Ps.NOSCHEME),
        )

        # even with other ignored flags
        self._check_fill_versions(
            PackageSample(repo='0', family='1', version='1.0', flags=Pf.NOSCHEME | Pf.IGNORE).expect(versionclass=Ps.NOSCHEME),
            PackageSample(repo='1', family='1', version='2.0', flags=Pf.NOSCHEME | Pf.IGNORE).expect(versionclass=Ps.NOSCHEME),
        )

    def test_altver(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='1.1.1234', flags=Pf.ALTVER).expect(versionclass=Ps.NEWEST),
            PackageSample(repo='0', version='1.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='1.0.1234', flags=Pf.ALTVER).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='0', version='1.0').expect(versionclass=Ps.LEGACY),
        )

    def test_altscheme(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='1', version='1235', flags=Pf.ALTSCHEME).expect(versionclass=Ps.NEWEST),
            PackageSample(repo='0', version='1.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='1234', flags=Pf.ALTSCHEME).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='0', version='1.0').expect(versionclass=Ps.LEGACY),
        )

    def test_branch_off(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='0', version='11.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='0', version='10.1').expect(versionclass=Ps.LEGACY),
            PackageSample(repo='0', version='10.0').expect(versionclass=Ps.LEGACY),

            PackageSample(repo='1', version='11.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='10.0').expect(versionclass=Ps.LEGACY),
        )

    def test_branch_on(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='0', version='11.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='0', version='10.1', branch='10.x').expect(versionclass=Ps.LEGACY),
            PackageSample(repo='0', version='10.0', branch='10.x').expect(versionclass=Ps.LEGACY),

            PackageSample(repo='1', version='11.1').expect(versionclass=Ps.NEWEST),
            # outdated, because there's no latest 10.1 for 10.x in this repo
            PackageSample(repo='1', version='10.0', branch='10.x').expect(versionclass=Ps.OUTDATED),
        )

    def test_branch_wget(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='msys', version='2.0.0', branch='2').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='msys', version='1.20.3').expect(versionclass=Ps.OUTDATED),

            PackageSample(repo='gentoo', version='2.0.0', branch='2').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='gentoo', version='1.21.1').expect(versionclass=Ps.LEGACY),
        )

    def test_branch_ignored(self) -> None:
        # legacy branch not created because older versions are ignored
        # should fallback to generic behavior as if branch wasn't specified
        self._check_fill_versions(
            PackageSample(repo='0', version='11.1').expect(versionclass=Ps.NEWEST),

            PackageSample(repo='1', version='11.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='10.1', branch='10.x', flags=Pf.UNTRUSTED).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='10.0', branch='10.x', flags=Pf.UNTRUSTED).expect(versionclass=Ps.LEGACY),
        )

    def test_branch_devel(self) -> None:
        # devel versions should be ignored when considering newest package in branch
        self._check_fill_versions(
            PackageSample(repo='0', version='11.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='0', version='10.1', branch='10.x').expect(versionclass=Ps.LEGACY),

            PackageSample(repo='1', version='11.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='10.2alpha1', branch='10.x', flags=Pf.DEVEL).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='10.0', branch='10.x').expect(versionclass=Ps.LEGACY),
        )

    def test_branch_multi(self) -> None:
        # multiple similar versions should have the same status
        self._check_fill_versions(
            PackageSample(repo='0', version='11.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='0', version='10.1', branch='10.x').expect(versionclass=Ps.LEGACY),

            PackageSample(repo='1', version='11.1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='10.0', branch='10.x').expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='1', version='10.0', branch='10.x').expect(versionclass=Ps.OUTDATED),
        )

    def test_branch_flavors(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='0', version='11.1', flavors=['a']).expect(versionclass=Ps.NEWEST),
            PackageSample(repo='0', version='11.1', flavors=['b']).expect(versionclass=Ps.NEWEST),

            PackageSample(repo='1', version='11.1', flavors=['a']).expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='11.1', flavors=['b']).expect(versionclass=Ps.NEWEST),

            PackageSample(repo='1', version='11.0', flavors=['a']).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='11.0', flavors=['b']).expect(versionclass=Ps.LEGACY),

            PackageSample(repo='1', version='10.2', flavors=['b'], branch='10.x').expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='10.1', flavors=['a'], branch='10.x').expect(versionclass=Ps.OUTDATED),
        )

    def test_sublimetext_case(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='0', version='101', flags=Pf.ALTSCHEME).expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='100', flags=Pf.ALTSCHEME).expect(versionclass=Ps.OUTDATED),

            PackageSample(repo='2', version='99', flags=Pf.DEVEL | Pf.INCORRECT).expect(versionclass=Ps.INCORRECT),

            PackageSample(repo='3', version='10.101', flags=Pf.INCORRECT).expect(versionclass=Ps.INCORRECT),
            PackageSample(repo='4', version='10').expect(versionclass=Ps.NEWEST),
        )

    def test_force_outdated(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='0', version='2', flags=Pf.OUTDATED).expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='1', version='1').expect(versionclass=Ps.OUTDATED),
        )

        self._check_fill_versions(
            PackageSample(repo='0', version='2', flags=Pf.DEVEL | Pf.OUTDATED).expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='1', version='1').expect(versionclass=Ps.NEWEST),
        )

        self._check_fill_versions(
            PackageSample(repo='0', version='1', flags=Pf.OUTDATED).expect(versionclass=Ps.OUTDATED),
        )

    def test_recalled(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='0', version='2', flags=Pf.RECALLED).expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='0', version='1').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='2').expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='1', version='1').expect(versionclass=Ps.NEWEST),
        )

        self._check_fill_versions(
            PackageSample(repo='0', version='3').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='0', version='2', flags=Pf.RECALLED).expect(versionclass=Ps.LEGACY),
            PackageSample(repo='0', version='1').expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='3').expect(versionclass=Ps.NEWEST),
            PackageSample(repo='1', version='2').expect(versionclass=Ps.LEGACY),
            PackageSample(repo='1', version='1').expect(versionclass=Ps.LEGACY),
        )

        self._check_fill_versions(
            PackageSample(repo='0', version='1', flags=Pf.RECALLED).expect(versionclass=Ps.OUTDATED),
            PackageSample(repo='1', version='1').expect(versionclass=Ps.OUTDATED),
        )

    def test_kdeconnect(self) -> None:
        self._check_fill_versions(
            PackageSample(repo='winget', version='21.08.1.726', flags=Pf.ALTVER).expect(versionclass=Ps.NEWEST),
            PackageSample(repo='kde_neon', version='21.08.1+p20.04+tunstable+git20210927.0021', flags=Pf.IGNORE | Pf.INCORRECT | Pf.ANY_IS_PATCH).expect(versionclass=Ps.INCORRECT),
            PackageSample(repo='alpine', version='21.08.1', flags=0).expect(versionclass=Ps.NEWEST),
        )


if __name__ == '__main__':
    unittest.main()
