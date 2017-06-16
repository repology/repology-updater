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

from repology.package import Package
from repology.transformer import PackageTransformer


class TestPackageTransformer(unittest.TestCase):
    def check_transformer(self, rulestext, *packages):
        transformer = PackageTransformer(rulestext=rulestext)

        for packagedict in packages:
            create_params = {}
            expected_params = {}
            for field, value in packagedict.items():
                if field.startswith('expect_'):
                    expected_params[field[7:]] = value
                else:
                    create_params[field] = value

            package = Package(**create_params)
            transformer.Process(package)

            for field, value in expected_params.items():
                self.assertEqual(package.__dict__[field], value)

    def test_ignore(self):
        self.check_transformer(
            '[ { name: p1, ignore: true } ]',
            {'name': 'p1', 'version': '1.0', 'expect_ignore': True},
            {'name': 'p2', 'version': '1.0', 'expect_ignore': False}
        )

    def test_unignore(self):
        self.check_transformer(
            '[ { name: p1, unignore: true } ]',
            {'name': 'p1', 'version': '1.0', 'ignore': True, 'expect_ignore': False},
            {'name': 'p2', 'version': '1.0', 'ignore': True, 'expect_ignore': True}
        )

    def test_ignorever(self):
        self.check_transformer(
            '[ { name: p1, ignorever: true } ]',
            {'name': 'p1', 'version': '1.0', 'expect_ignoreversion': True},
            {'name': 'p2', 'version': '1.0', 'expect_ignoreversion': False}
        )

    def test_unignorever(self):
        self.check_transformer(
            '[ { name: p1, unignorever: true } ]',
            {'name': 'p1', 'version': '1.0', 'ignoreversion': True, 'expect_ignoreversion': False},
            {'name': 'p2', 'version': '1.0', 'ignoreversion': True, 'expect_ignoreversion': True}
        )

    def test_setname(self):
        self.check_transformer(
            '[ { setname: "bar" } ]',
            {'name': 'foo', 'version': '1.0', 'expect_name': 'foo', 'expect_effname': 'bar'}
        )

    def test_setname_subst(self):
        self.check_transformer(
            '[ { setname: "bar_$0" } ]',
            {'name': 'foo', 'version': '1.0', 'expect_name': 'foo', 'expect_effname': 'bar_foo'}
        )

    def test_tolowername(self):
        self.check_transformer(
            '[ { tolowername: true } ]',
            {'name': 'fOoBaR', 'version': '1.0', 'expect_name': 'fOoBaR', 'expect_effname': 'foobar'}
        )

    def test_last(self):
        self.check_transformer(
            '[ { last: true }, { setname: "bar" } ]',
            {'name': 'foo', 'version': '1.0', 'expect_effname': 'foo'}
        )

    def test_match_name(self):
        self.check_transformer(
            '[ { name: p1, setname: bar }, { name: [p3], setname: baz } ]',
            {'name': 'p1', 'version': '1.0', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '2.0', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '2.0', 'expect_effname': 'baz'}
        )

    def test_match_name_multi(self):
        self.check_transformer(
            '[ { name: [p1,p2], setname: bar } ]',
            {'name': 'p1', 'version': '1.0', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '2.0', 'expect_effname': 'bar'},
            {'name': 'p3', 'version': '2.0', 'expect_effname': 'p3'}
        )

    def test_match_namepat(self):
        self.check_transformer(
            '[ { namepat: ".*1", setname: bar } ]',
            {'name': 'p1', 'version': '1.0', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '2.0', 'expect_effname': 'p2'}
        )

        self.check_transformer(
            '[ { namepat: "p.*", setname: bar } ]',
            {'name': 'p1', 'version': '1.0', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '2.0', 'expect_effname': 'bar'}
        )

        self.check_transformer(
            '[ { namepat: "p", setname: bar }, { namepat: "1", setname: bar }, { namepat: ".", setname: bar } ] ',
            {'name': 'p1', 'version': '1.0', 'expect_effname': 'p1'},
            {'name': 'p2', 'version': '2.0', 'expect_effname': 'p2'}
        )

        self.check_transformer(
            '[ { namepat: "p2", setname: bar } ]',
            {'name': 'p1', 'version': '1.0', 'expect_effname': 'p1'},
            {'name': 'p2', 'version': '2.0', 'expect_effname': 'bar'}
        )

    def test_match_ver(self):
        self.check_transformer(
            '[ { ver: "1.0", setname: bar }, { ver: ["3.0"], setname: baz } ]',
            {'name': 'p1', 'version': '1.0', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '2.0', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '3.0', 'expect_effname': 'baz'}
        )

    def test_match_verpat(self):
        self.check_transformer(
            '[ { verpat: "1.*", setname: bar } ]',
            {'name': 'p1', 'version': '1.0', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '2.0', 'expect_effname': 'p2'}
        )

    def test_match_verlonger(self):
        self.check_transformer(
            '[ { verlonger: 2, setname: bar } ]',
            {'name': 'p1', 'version': '1.0.0', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '1.0', 'expect_effname': 'p2'}
        )

    def test_match_wwwpat(self):
        self.check_transformer(
            '[ { wwwpat: "https?://foo\\\\.com/.*", setname: bar } ]',
            {'name': 'p1', 'version': '1.0', 'homepage': 'https://foo.com/xxx', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '1.0', 'homepage': 'http://foo.com/', 'expect_effname': 'bar'},
            {'name': 'p3', 'version': '1.0', 'homepage': 'http://foo_com/xxx', 'expect_effname': 'p3'},
            {'name': 'p4', 'version': '2.0', 'expect_effname': 'p4'}
        )

    def test_match_wwwpart(self):
        self.check_transformer(
            '[ { wwwpart: "foo", setname: bar } ]',
            {'name': 'p1', 'version': '1.0', 'homepage': 'http://foo/xxx', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '1.0', 'homepage': 'http://bar.com/yyy', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '2.0', 'expect_effname': 'p3'}
        )

    def test_match_family(self):
        self.check_transformer(
            '[ { family: foo, setname: quux }, { family: [ baz ], setname: bat } ]',
            {'name': 'p1', 'version': '1.0', 'family': 'foo', 'expect_effname': 'quux'},
            {'name': 'p2', 'version': '2.0', 'family': 'bar', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '3.0', 'family': 'baz', 'expect_effname': 'bat'}
        )

    def test_match_category(self):
        self.check_transformer(
            '[ { category: foo, setname: quux }, { category: [ baz ], setname: bat } ]',
            {'name': 'p1', 'version': '1.0', 'category': 'foo', 'expect_effname': 'quux'},
            {'name': 'p2', 'version': '2.0', 'category': 'bar', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '3.0', 'category': 'baz', 'expect_effname': 'bat'}
        )


if __name__ == '__main__':
    unittest.main()
