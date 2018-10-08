#!/usr/bin/env python3
#
# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.parsers.maintainers import extract_maintainers
from repology.parsers.nevra import construct_evr, filename2nevra


class TestNevra(unittest.TestCase):
    def test_filename2nevra(self):
        self.assertEqual(filename2nevra('foo-1.2.3-1.i386.rpm'), ('foo', '', '1.2.3', '1', 'i386'))
        self.assertEqual(filename2nevra('foo-bar-baz-999:1.2.3-1.src.rpm'), ('foo-bar-baz', '999', '1.2.3', '1', 'src'))


class TestConstructEvr(unittest.TestCase):
    def test_filename2nevra(self):
        self.assertEqual(construct_evr('1', '1.2.3', 'fc.14'), '1:1.2.3-fc.14')
        self.assertEqual(construct_evr(1, '1.2.3', 'fc.14'), '1:1.2.3-fc.14')

        self.assertEqual(construct_evr(None, '1.2.3', 'fc.14'), '1.2.3-fc.14')
        self.assertEqual(construct_evr('', '1.2.3', 'fc.14'), '1.2.3-fc.14')
        self.assertEqual(construct_evr('0', '1.2.3', 'fc.14'), '1.2.3-fc.14')
        self.assertEqual(construct_evr(0, '1.2.3', 'fc.14'), '1.2.3-fc.14')

        self.assertEqual(construct_evr('1', '1.2.3', None), '1:1.2.3')
        self.assertEqual(construct_evr('1', '1.2.3', ''), '1:1.2.3')

        self.assertEqual(construct_evr(None, '1.2.3', None), '1.2.3')
        self.assertEqual(construct_evr(0, '1.2.3', ''), '1.2.3')


class TestSplitMaintainers(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(extract_maintainers('amdmi3@FreeBSD.org'), ['amdmi3@freebsd.org'])
        self.assertEqual(extract_maintainers('amdmi3@FAKE'), ['amdmi3@fake'])

    def test_name(self):
        self.assertEqual(extract_maintainers('Dmitry Marakasov <amdmi3@FreeBSD.org>'), ['amdmi3@freebsd.org'])
        self.assertEqual(extract_maintainers('"Dmitry Marakasov" <amdmi3@FreeBSD.org>'), ['amdmi3@freebsd.org'])

    def test_name_comma(self):
        self.assertEqual(extract_maintainers('Marakasov, Dmitry <amdmi3@FreeBSD.org>'), ['amdmi3@freebsd.org'])
        self.assertEqual(extract_maintainers('"Marakasov, Dmitry" <amdmi3@FreeBSD.org>'), ['amdmi3@freebsd.org'])

    def test_lists(self):
        self.assertEqual(extract_maintainers('amdmi3@FreeBSD.org,gnome@FreeBSD.org'), ['amdmi3@freebsd.org', 'gnome@freebsd.org'])
        self.assertEqual(extract_maintainers('amdmi3@FreeBSD.org, gnome@FreeBSD.org'), ['amdmi3@freebsd.org', 'gnome@freebsd.org'])
        self.assertEqual(extract_maintainers('amdmi3@FreeBSD.org gnome@FreeBSD.org'), ['amdmi3@freebsd.org', 'gnome@freebsd.org'])

    def test_list_name(self):
        self.assertEqual(extract_maintainers('Dmitry Marakasov <amdmi3@FreeBSD.org>, Gnome Guys <gnome@FreeBSD.org>'), ['amdmi3@freebsd.org', 'gnome@freebsd.org'])

    def test_list_name_complex(self):
        self.assertEqual(extract_maintainers('Marakasov, Dmitry <amdmi3@FreeBSD.org>, Guys, Gnome <gnome@FreeBSD.org>'), ['amdmi3@freebsd.org', 'gnome@freebsd.org'])

    def test_list_name_ambigous(self):
        # apart from samples form test_lists above, this is ambigous -
        # words may be a name, or may be an obfuscated email. These
        # should be skipped
        self.assertEqual(extract_maintainers('dmitry marakasov amdmi3@FreeBSD.org, foo dot bar@FreeBSD.org'), [])

    def test_garbage(self):
        self.assertEqual(extract_maintainers(',amdmi3@FreeBSD.org, ,,   '), ['amdmi3@freebsd.org'])

    def test_immune_to_obfuscation(self):
        self.assertEqual(extract_maintainers('amdmi3[at]FreeBSD[dot]org'), [])
        self.assertEqual(extract_maintainers('amdmi3 [ at ] FreeBSD [ dot ] org'), [])
        self.assertEqual(extract_maintainers('amdmi3 at FreeBSD dot org'), [])
        self.assertEqual(extract_maintainers('amdmi3_at_FreeBSD.org'), [])
        self.assertEqual(extract_maintainers('amdmi3{at}FreeBSD{dot}org'), [])
        self.assertEqual(extract_maintainers('amdmi3 <at> freebsd {dot} org'), [])
        self.assertEqual(extract_maintainers('amdmi3~at~freebsd~dot~org'), [])
        self.assertEqual(extract_maintainers('amdmi3 (at) freebsd (dot) org'), [])
        self.assertEqual(extract_maintainers('amdmi3 __at__ freebsd __dot__ org'), [])
        self.assertEqual(extract_maintainers('amdmi3-at-freebsd-dot-org'), [])
        self.assertEqual(extract_maintainers('amdmi3<at>freebsd.org'), [])
        self.assertEqual(extract_maintainers('amdmi3 <at> freebsd.org'), [])
        self.assertEqual(extract_maintainers('amdmi3 [underscore] ports [at] freebsd.org'), [])
        self.assertEqual(extract_maintainers('amdmi3 plus ports@freebsd.org'), [])
        self.assertEqual(extract_maintainers('agent smith (amdmi3@freebsd.org)'), [])

        self.assertEqual(extract_maintainers('amdNOmi3@freeSPAMbsd.org (remove NO and SPAM)'), [])
        self.assertEqual(extract_maintainers('amdmi3 @ google mail'), [])

    def test_empty(self):
        self.assertEqual(extract_maintainers('somecrap'), [])
        self.assertEqual(extract_maintainers(''), [])
        self.assertEqual(extract_maintainers('http://repology.org'), [])
        self.assertEqual(extract_maintainers('Repology <http://repology.org>'), [])
        self.assertEqual(extract_maintainers('nobody <really>'), [])


if __name__ == '__main__':
    unittest.main()
