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

from repology.util import GetMaintainers


class TestSplitMaintainers(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(GetMaintainers('amdmi3@FreeBSD.org'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3@FAKE'), ['amdmi3@fake'])

    def test_name(self):
        self.assertEqual(GetMaintainers('Dmitry Marakasov <amdmi3@FreeBSD.org>'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('"Dmitry Marakasov" <amdmi3@FreeBSD.org>'), ['amdmi3@freebsd.org'])

    def test_name_comma(self):
        self.assertEqual(GetMaintainers('Marakasov, Dmitry <amdmi3@FreeBSD.org>'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('"Marakasov, Dmitry" <amdmi3@FreeBSD.org>'), ['amdmi3@freebsd.org'])

    def test_list(self):
        self.assertEqual(GetMaintainers('amdmi3@FreeBSD.org,gnome@FreeBSD.org'), ['amdmi3@freebsd.org', 'gnome@freebsd.org'])

    def test_list_name(self):
        self.assertEqual(GetMaintainers('Dmitry Marakasov <amdmi3@FreeBSD.org>, Gnome Guys <gnome@FreeBSD.org>'), ['amdmi3@freebsd.org', 'gnome@freebsd.org'])

    def test_garbage(self):
        self.assertEqual(GetMaintainers(',amdmi3@FreeBSD.org, ,,   '), ['amdmi3@freebsd.org'])

    def test_obfuscation(self):
        self.assertEqual(GetMaintainers('amdmi3[at]FreeBSD[dot]org'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3 [ at ] FreeBSD [ dot ] org'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3 at FreeBSD dot org'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3_at_FreeBSD.org'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3{at}FreeBSD{dot}org'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3 <at> freebsd {dot} org'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3~at~freebsd~dot~org'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3 (at) freebsd (dot) org'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3 __at__ freebsd __dot__ org'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3-at-freebsd-dot-org'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3<at>freebsd.org'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3 <at> freebsd.org'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3 [underscore] ports [at] freebsd.org'), ['amdmi3_ports@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3 plus ports@freebsd.org'), ['amdmi3+ports@freebsd.org'])
        self.assertEqual(GetMaintainers('agent smith (amdmi3@freebsd.org)'), ['amdmi3@freebsd.org'])

        self.assertEqual(GetMaintainers('amdNOmi3@freeSPAMbsd.org (remove NO and SPAM)'), ['amdmi3@freebsd.org'])
        self.assertEqual(GetMaintainers('amdmi3 @ google mail'), ['amdmi3@gmail.com'])

    def test_empty(self):
        self.assertEqual(GetMaintainers('somecrap'), [])
        self.assertEqual(GetMaintainers(''), [])


if __name__ == '__main__':
    unittest.main()
