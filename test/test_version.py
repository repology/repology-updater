#!/usr/bin/env python3
#
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

import unittest

from repology.version import VersionCompare


class TestVersionComparison(unittest.TestCase):
    def test_equality(self):
        self.assertEqual(VersionCompare('0', '0'), 0)
        self.assertEqual(VersionCompare('0a', '0a'), 0)
        self.assertEqual(VersionCompare('0.a', '0.a'), 0)
        self.assertEqual(VersionCompare('1a1', '1a1'), 0)
        self.assertEqual(VersionCompare('1alpha1', '1alpha1'), 0)
        self.assertEqual(VersionCompare('a', 'a'), 0)
        self.assertEqual(VersionCompare('foo', 'foo'), 0)
        self.assertEqual(VersionCompare('1.2.3', '1.2.3'), 0)
        self.assertEqual(VersionCompare('hello.world', 'hello.world'), 0)

    def test_different_number_of_components(self):
        self.assertEqual(VersionCompare('1', '1.0'), 0)
        self.assertEqual(VersionCompare('1.0', '1'), 0)

        self.assertEqual(VersionCompare('1', '1.0.0'), 0)
        self.assertEqual(VersionCompare('1.0.0', '1'), 0)

    def test_leading_zeroes(self):
        self.assertEqual(VersionCompare('00100.00100', '100.100'), 0)
        self.assertEqual(VersionCompare('100.100', '00100.00100'), 0)
        self.assertEqual(VersionCompare('0', '00000000'), 0)
        self.assertEqual(VersionCompare('00000000', '0'), 0)

    def test_simple_comparisons(self):
        self.assertEqual(VersionCompare('0.0.0', '0.0.1'), -1)
        self.assertEqual(VersionCompare('0.0.1', '0.0.0'), 1)

        self.assertEqual(VersionCompare('0.0.1', '0.0.2'), -1)
        self.assertEqual(VersionCompare('0.0.2', '0.0.1'), 1)

        self.assertEqual(VersionCompare('0.0.2', '0.1.0'), -1)
        self.assertEqual(VersionCompare('0.1.0', '0.0.2'), 1)

        self.assertEqual(VersionCompare('0.0.2', '0.0.10'), -1)
        self.assertEqual(VersionCompare('0.0.10', '0.0.2'), 1)

        self.assertEqual(VersionCompare('0.0.10', '0.1.0'), -1)
        self.assertEqual(VersionCompare('0.1.0', '0.0.10'), 1)

        self.assertEqual(VersionCompare('0.1.0', '0.1.1'), -1)
        self.assertEqual(VersionCompare('0.1.1', '0.1.0'), 1)

        self.assertEqual(VersionCompare('0.1.1', '1.0.0'), -1)
        self.assertEqual(VersionCompare('1.0.0', '0.1.1'), 1)

        self.assertEqual(VersionCompare('1.0.0', '10.0.0'), -1)
        self.assertEqual(VersionCompare('10.0.0', '1.0.0'), 1)

        self.assertEqual(VersionCompare('10.0.0', '100.0.0'), -1)
        self.assertEqual(VersionCompare('100.0.0', '10.0.0'), 1)

        self.assertEqual(VersionCompare('10.10000.10000', '11.0.0'), -1)
        self.assertEqual(VersionCompare('11.0.0', '10.10000.10000'), 1)

    def test_long_number(self):
        self.assertEqual(VersionCompare('20160101', '20160102'), -1)
        self.assertEqual(VersionCompare('20160102', '20160101'), 1)

    def test_even_longer_numver(self):
        self.assertEqual(VersionCompare('9999999999999999', '10000000000000000'), -1)
        self.assertEqual(VersionCompare('10000000000000000', '9999999999999999'), 1)

    def test_letter_addendum(self):
        self.assertEqual(VersionCompare('1.0', '1.0a'), -1)
        self.assertEqual(VersionCompare('1.0a', '1.0'), 1)

        self.assertEqual(VersionCompare('1.0a', '1.0b'), -1)
        self.assertEqual(VersionCompare('1.0b', '1.0a'), 1)

    def test_letter_component(self):
        self.assertEqual(VersionCompare('1.0.a', '1.0'), -1)
        self.assertEqual(VersionCompare('1.0', '1.0.a'), 1)

        self.assertEqual(VersionCompare('1.0.a', '1.0.b'), -1)
        self.assertEqual(VersionCompare('1.0.b', '1.0.a'), 1)

        self.assertEqual(VersionCompare('1.0.a', '1.0.0'), -1)
        self.assertEqual(VersionCompare('1.0.0', '1.0.a'), 1)

    def test_letter_vs_number(self):
        self.assertEqual(VersionCompare('a', '0'), -1)
        self.assertEqual(VersionCompare('0', 'a'), 1)

    def test_case_is_ignored(self):
        self.assertEqual(VersionCompare('1a1', '1ALPHA1'), 0)
        self.assertEqual(VersionCompare('1A1', '1alpha1'), 0)

    def test_miscomparation1(self):  # github issue #16
        self.assertEqual(VersionCompare('1.4c', '1.4e'), -1)
        self.assertEqual(VersionCompare('1.4e', '1.4c'), 1)

    def test_miscomparation2(self):  # github issue #16
        self.assertEqual(VersionCompare('4.89', '4.90.f'), -1)
        self.assertEqual(VersionCompare('4.90.f', '4.49'), 1)

    def test_miscomparation3(self):  # github issue #138
        self.assertEqual(VersionCompare('1.7.5~a1', '1.7.5a1'), 0)
        self.assertEqual(VersionCompare('1.7.5a1', '1.7.5~a1'), 0)
        self.assertEqual(VersionCompare('1.7.5~a1', '1.7.5-a1'), 0)
        self.assertEqual(VersionCompare('1.7.5-a1', '1.7.5~a1'), 0)
        self.assertEqual(VersionCompare('1.7.5a1', '1.7.5-a1'), 0)
        self.assertEqual(VersionCompare('1.7.5-a1', '1.7.5a1'), 0)

    def test_specific1(self):
        self.assertEqual(VersionCompare('1.0r1', '1.0_RC1'), 0)

    def test_doc_brag(self):
        # ensure that capabilities we brag about in
        # docs/VERSION_COMPARISON.md are actually there
        self.assertEqual(VersionCompare('1.2.3alpha4', '1.2.3~a4'), 0)
        self.assertEqual(VersionCompare('1.2.3alpha4', '1.2.3.a4'), 0)

        self.assertEqual(VersionCompare('1.2.3alpha4', '1.2.3'), -1)
        self.assertEqual(VersionCompare('1.2.3~a4', '1.2.3'), -1)
        self.assertEqual(VersionCompare('1.2.3.a4', '1.2.3'), -1)

    def test_non_dot_separator(self):
        self.assertEqual(VersionCompare('1.0.beta1', '1.0_beta1'), 0)

    def test_prerelease_sequence(self):
        self.assertEqual(VersionCompare('1.0.alpha1', '1.0.alpha2'), -1)
        self.assertEqual(VersionCompare('1.0.alpha2', '1.0.beta1'), -1)
        self.assertEqual(VersionCompare('1.0.beta1', '1.0.beta2'), -1)
        self.assertEqual(VersionCompare('1.0.beta2', '1.0.rc1'), -1)
        self.assertEqual(VersionCompare('1.0.beta2', '1.0.pre1'), -1)
        self.assertEqual(VersionCompare('1.0.rc2', '1.0'), -1)
        self.assertEqual(VersionCompare('1.0.pre2', '1.0'), -1)
        # XXX: is rc/pre order defined?

        self.assertEqual(VersionCompare('1.0alpha1', '1.0alpha2'), -1)
        self.assertEqual(VersionCompare('1.0alpha2', '1.0beta1'), -1)
        self.assertEqual(VersionCompare('1.0beta1', '1.0beta2'), -1)
        self.assertEqual(VersionCompare('1.0beta2', '1.0rc1'), -1)
        self.assertEqual(VersionCompare('1.0beta2', '1.0pre1'), -1)
        self.assertEqual(VersionCompare('1.0rc2', '1.0'), -1)
        self.assertEqual(VersionCompare('1.0pre2', '1.0'), -1)

    # while above tests are rock solid, following may be tuned
    def test_complex_cases(self):
        self.assertEqual(VersionCompare('1.0beta1', '1.0.beta1'), 0)
        self.assertEqual(VersionCompare('1.0beta1', '1.0.b1'), 0)
        self.assertEqual(VersionCompare('1.0.beta1', '1.0.b1'), 0)
        self.assertEqual(VersionCompare('1.0.beta1', '1.0.b1'), 0)

        self.assertEqual(VersionCompare('1.0alpha1', '1.0'), -1)
        self.assertEqual(VersionCompare('1.0', '1.0alpha1'), 1)

        self.assertEqual(VersionCompare('1.0beta1', '1.0'), -1)
        self.assertEqual(VersionCompare('1.0', '1.0beta1'), 1)

        self.assertEqual(VersionCompare('1.0pre1', '1.0'), -1)
        self.assertEqual(VersionCompare('1.0', '1.0pre1'), 1)

        self.assertEqual(VersionCompare('1.0rc1', '1.0'), -1)
        self.assertEqual(VersionCompare('1.0', '1.0rc1'), 1)

    def test_empty(self):
        self.assertEqual(VersionCompare('', '0'), 0)
        self.assertEqual(VersionCompare('', '1'), -1)

    def test_garbage(self):
        self.assertEqual(VersionCompare('......-----~~~~~!!!', '0.0.0.0'), 0)
        self.assertEqual(VersionCompare('.-~1~-.-~2~-.', '1.2'), 0)

    def test_case_insensitivity(self):
        self.assertEqual(VersionCompare('1.0A', '1.0a'), 0)
        self.assertEqual(VersionCompare('1.0ALPHA', '1.0alpha'), 0)


if __name__ == '__main__':
    unittest.main()
