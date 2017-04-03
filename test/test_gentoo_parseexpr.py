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

from repology.parser.gentoo import ParseConditionalExpr


class TestGentooParseExpr(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(ParseConditionalExpr('http://foo'), ['http://foo'])

    def test_multiple(self):
        self.assertEqual(ParseConditionalExpr('http://foo http://bar'), ['http://foo', 'http://bar'])

    def test_rename(self):
        self.assertEqual(ParseConditionalExpr('http://foo/file.tgz -> file.tar.gz'), ['http://foo/file.tgz'])

    def test_condition(self):
        self.assertEqual(ParseConditionalExpr('!http? ( http://foo )'), ['http://foo'])
        self.assertEqual(ParseConditionalExpr('!http? ( http://foo ) !ftp? ( http://bar )'), ['http://foo', 'http://bar'])

    def test_nested_condition(self):
        self.assertEqual(ParseConditionalExpr('!http? ( !ftp? ( http://foo ) )'), ['http://foo'])

    def test_realworld(self):
        self.assertEqual(
            ParseConditionalExpr(
                'mirror://sourceforge/free-doko/FreeDoko_0.7.14.src.zip backgrounds? '
                '( mirror://sourceforge/free-doko/backgrounds.zip -> freedoko-backgrounds.zip ) '
                'kdecards? ( mirror://sourceforge/free-doko/kdecarddecks.zip ) xskatcards? '
                '( mirror://sourceforge/free-doko/xskat.zip ) pysolcards? ( mirror://sourceforge/free-doko/pysol.zip '
                ') gnomecards? ( mirror://sourceforge/free-doko/gnome-games.zip ) '
                'openclipartcards? ( mirror://sourceforge/free-doko/openclipart.zip ) '
                '!xskatcards? ( !kdecards? ( !gnomecards? ( !openclipartcards? ( !pysolcards? '
                '( mirror://sourceforge/free-doko/xskat.zip ) ) ) ) )',
            ), [
                'mirror://sourceforge/free-doko/FreeDoko_0.7.14.src.zip',
                'mirror://sourceforge/free-doko/backgrounds.zip',
                'mirror://sourceforge/free-doko/kdecarddecks.zip',
                'mirror://sourceforge/free-doko/xskat.zip',
                'mirror://sourceforge/free-doko/pysol.zip',
                'mirror://sourceforge/free-doko/gnome-games.zip',
                'mirror://sourceforge/free-doko/openclipart.zip',
                'mirror://sourceforge/free-doko/xskat.zip'
            ]
        )


if __name__ == '__main__':
    unittest.main()
