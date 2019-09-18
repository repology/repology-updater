#!/usr/bin/env python3
#
# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Any, Dict

from repology.package import PackageFlags
from repology.repomgr import RepositoryManager
from repology.transformer import PackageTransformer

from .package import spawn_package


repomgr = RepositoryManager(repostext="""
[
    { name: dummyrepo, desc: dummyrepo, family: dummyrepo, sources: [] },
    { name: foo, desc: foo, family: foo, sources: [] },
    { name: bar, desc: bar, family: bar, sources: [] },
    { name: baz, desc: baz, family: baz, sources: [] }
]
""")


class TestPackageTransformer(unittest.TestCase):
    def check_transformer(self, rulestext: str, *packages: Dict[str, Any]) -> None:
        transformer = PackageTransformer(repomgr, rulestext=rulestext)
        for packagedict in packages:
            create_params = {}
            expected_params = {}
            for field, value in packagedict.items():
                if field.startswith('expect_'):
                    expected_params[field[7:]] = value
                else:
                    create_params[field] = value

            package = spawn_package(**create_params)
            transformer.process(package)

            for field, value in expected_params.items():
                self.assertEqual(package.__dict__[field], value)

    def test_remove(self) -> None:
        self.check_transformer(
            '[ { name: p1, remove: true } ]',
            {'name': 'p1', 'version': '1.0', 'expect_flags': PackageFlags.REMOVE},
            {'name': 'p2', 'version': '1.0', 'expect_flags': 0}
        )

    def test_unremove(self) -> None:
        self.check_transformer(
            '[ { name: p1, remove: false } ]',
            {'name': 'p1', 'version': '1.0', 'flags': PackageFlags.REMOVE, 'expect_flags': 0},
            {'name': 'p2', 'version': '1.0', 'flags': PackageFlags.REMOVE, 'expect_flags': PackageFlags.REMOVE}
        )

    def test_ignore(self) -> None:
        self.check_transformer(
            '[ { name: p1, ignore: true } ]',
            {'name': 'p1', 'version': '1.0', 'expect_flags': PackageFlags.IGNORE},
            {'name': 'p2', 'version': '1.0', 'expect_flags': 0}
        )

    def test_unignore(self) -> None:
        self.check_transformer(
            '[ { name: p1, ignore: false } ]',
            {'name': 'p1', 'version': '1.0', 'flags': PackageFlags.IGNORE, 'expect_flags': 0},
            {'name': 'p2', 'version': '1.0', 'flags': PackageFlags.IGNORE, 'expect_flags': PackageFlags.IGNORE}
        )

    def test_devel(self) -> None:
        self.check_transformer(
            '[ { name: p1, devel: true } ]',
            {'name': 'p1', 'version': '1.0', 'expect_flags': PackageFlags.DEVEL},
            {'name': 'p2', 'version': '1.0', 'expect_flags': 0}
        )

    def test_undevel(self) -> None:
        self.check_transformer(
            '[ { name: p1, devel: false } ]',
            {'name': 'p1', 'version': '1.0', 'flags': PackageFlags.DEVEL, 'expect_flags': 0},
            {'name': 'p2', 'version': '1.0', 'flags': PackageFlags.DEVEL, 'expect_flags': PackageFlags.DEVEL}
        )

    def test_multiflags(self) -> None:
        self.check_transformer(
            '[ { devel: true, ignore: false, noscheme: true }, { ignore: true, noscheme: false } ]',
            {'name': 'aaa', 'version': '1.0', 'expect_flags': PackageFlags.DEVEL | PackageFlags.IGNORE}
        )

    def test_setname(self) -> None:
        self.check_transformer(
            '[ { setname: "bar" } ]',
            {'name': 'foo', 'version': '1.0', 'expect_name': 'foo', 'expect_effname': 'bar'}
        )

    def test_setname_subst(self) -> None:
        self.check_transformer(
            '[ { setname: "bar_$0" } ]',
            {'name': 'foo', 'version': '1.0', 'expect_name': 'foo', 'expect_effname': 'bar_foo'}
        )

    def test_setname_reverse_subst(self) -> None:
        self.check_transformer(
            '[ { setname: foo, name: [ $0-client, $0-server ] } ]',
            {'name': 'foo-client', 'version': '1.0', 'expect_effname': 'foo'},
            {'name': 'foo-server', 'version': '1.0', 'expect_effname': 'foo'},
            {'name': 'foo-other', 'version': '1.0', 'expect_effname': 'foo-other'},
        )

        self.check_transformer(
            '[ { setname: foo, namepat: "$0-(client|server)" } ]',
            {'name': 'foo-client', 'version': '1.0', 'expect_effname': 'foo'},
            {'name': 'foo-server', 'version': '1.0', 'expect_effname': 'foo'},
            {'name': 'foo-other', 'version': '1.0', 'expect_effname': 'foo-other'},
        )

    def test_setver(self) -> None:
        self.check_transformer(
            '[ { setver: "2.0" } ]',
            {'name': 'foo', 'version': '1.0', 'expect_version': '2.0'}
        )

    def test_setver_subst(self) -> None:
        self.check_transformer(
            '[ { setver: "2.$0" } ]',
            {'name': 'foo', 'version': '1.0', 'expect_version': '2.1.0'}
        )
        self.check_transformer(
            '[ { verpat: "([0-9]+)\\\\.([0-9]+)", setver: "$2.$1" } ]',
            {'name': 'foo', 'version': '1.0', 'expect_version': '0.1'}
        )

    def test_setver_setname_subst(self) -> None:
        self.check_transformer(
            '[ { namepat: "f(.*)", verpat: "1(.*)", setname: "$1/$0", setver: "$1/$0" } ]',
            {'name': 'foo', 'version': '1.0', 'expect_effname': 'oo/foo', 'expect_version': '.0/1.0'}
        )

    def test_tolowername(self) -> None:
        self.check_transformer(
            '[ { tolowername: true } ]',
            {'name': 'fOoBaR', 'version': '1.0', 'expect_name': 'fOoBaR', 'expect_effname': 'foobar'}
        )

    def test_last(self) -> None:
        self.check_transformer(
            '[ { last: true }, { setname: "bar" } ]',
            {'name': 'foo', 'version': '1.0', 'expect_effname': 'foo'}
        )

    def test_match_name(self) -> None:
        self.check_transformer(
            '[ { name: p1, setname: bar }, { name: [p3], setname: baz } ]',
            {'name': 'p1', 'version': '1.0', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '2.0', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '2.0', 'expect_effname': 'baz'}
        )

    def test_match_name_multi(self) -> None:
        self.check_transformer(
            '[ { name: [p1,p2], setname: bar } ]',
            {'name': 'p1', 'version': '1.0', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '2.0', 'expect_effname': 'bar'},
            {'name': 'p3', 'version': '2.0', 'expect_effname': 'p3'}
        )

    def test_match_namepat(self) -> None:
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

    def test_match_ver(self) -> None:
        self.check_transformer(
            '[ { ver: "1.0", setname: bar }, { ver: ["3.0"], setname: baz } ]',
            {'name': 'p1', 'version': '1.0', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '2.0', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '3.0', 'expect_effname': 'baz'}
        )

    def test_match_vernot(self) -> None:
        self.check_transformer(
            '[ { notver: "1.0", setname: bar }, { notver: ["1.0", "3.0"], setname: baz } ]',
            {'name': 'p1', 'version': '1.0', 'expect_effname': 'p1'},
            {'name': 'p2', 'version': '2.0', 'expect_effname': 'baz'},
            {'name': 'p3', 'version': '3.0', 'expect_effname': 'bar'}
        )

    def test_match_verpat(self) -> None:
        self.check_transformer(
            '[ { verpat: "1.*", setname: bar } ]',
            {'name': 'p1', 'version': '1.0', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '2.0', 'expect_effname': 'p2'}
        )

    def test_match_verpat_case_ignored(self) -> None:
        self.check_transformer(
            '[ { verpat: ".*beta.*", setname: bar } ]',
            {'name': 'p1', 'version': '1beta1', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '1BETA2', 'expect_effname': 'bar'}
        )

    def test_match_verlonger(self) -> None:
        self.check_transformer(
            '[ { verlonger: 2, setname: bar } ]',
            {'name': 'p1', 'version': '1.0.0', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '1.0', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '1-0-0', 'expect_effname': 'bar'}
        )

    def test_match_vergt(self) -> None:
        self.check_transformer(
            '[ { vergt: "1.0", setname: bar } ]',
            {'name': 'p1', 'version': '0.9', 'expect_effname': 'p1'},
            {'name': 'p2', 'version': '1.0', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '1.1', 'expect_effname': 'bar'}
        )

    def test_match_verge(self) -> None:
        self.check_transformer(
            '[ { verge: "1.0", setname: bar } ]',
            {'name': 'p1', 'version': '0.9', 'expect_effname': 'p1'},
            {'name': 'p2', 'version': '1.0', 'expect_effname': 'bar'},
            {'name': 'p3', 'version': '1.1', 'expect_effname': 'bar'}
        )

    def test_match_verlt(self) -> None:
        self.check_transformer(
            '[ { verlt: "1.0", setname: bar } ]',
            {'name': 'p1', 'version': '0.9', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '1.0', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '1.1', 'expect_effname': 'p3'}
        )

    def test_match_verle(self) -> None:
        self.check_transformer(
            '[ { verle: "1.0", setname: bar } ]',
            {'name': 'p1', 'version': '0.9', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '1.0', 'expect_effname': 'bar'},
            {'name': 'p3', 'version': '1.1', 'expect_effname': 'p3'}
        )

    def test_match_vereq(self) -> None:
        self.check_transformer(
            '[ { vereq: "1.0", setname: bar } ]',
            {'name': 'p1', 'version': '0.9', 'expect_effname': 'p1'},
            {'name': 'p2', 'version': '1.0', 'expect_effname': 'bar'},
            {'name': 'p3', 'version': '1.1', 'expect_effname': 'p3'}
        )

    def test_match_verne(self) -> None:
        self.check_transformer(
            '[ { verne: "1.0", setname: bar } ]',
            {'name': 'p1', 'version': '0.9', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '1.0', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '1.1', 'expect_effname': 'bar'}
        )

    def test_match_wwwpat(self) -> None:
        self.check_transformer(
            '[ { wwwpat: "https?://foo\\\\.com/.*", setname: bar } ]',
            {'name': 'p1', 'version': '1.0', 'homepage': 'https://foo.com/xxx', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '1.0', 'homepage': 'http://foo.com/', 'expect_effname': 'bar'},
            {'name': 'p3', 'version': '1.0', 'homepage': 'http://foo_com/xxx', 'expect_effname': 'p3'},
            {'name': 'p4', 'version': '2.0', 'expect_effname': 'p4'}
        )

    def test_match_wwwpart(self) -> None:
        self.check_transformer(
            '[ { wwwpart: "foo", setname: bar } ]',
            {'name': 'p1', 'version': '1.0', 'homepage': 'http://foo/xxx', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '1.0', 'homepage': 'http://bar.com/yyy', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '2.0', 'expect_effname': 'p3'}
        )

    def test_match_wwwpart_case(self) -> None:
        self.check_transformer(
            '[ { wwwpart: homepage1, setname: ok1 }, { wwwpart: HOMEPAGE2, setname: ok2 }, { wwwpart: homepage3, setname: ok3 }, { wwwpart: HOMEPAGE4, setname: ok4 } ]',
            {'name': 'p1', 'version': '1.0', 'homepage': 'http://homepage1', 'expect_effname': 'ok1'},
            {'name': 'p2', 'version': '1.0', 'homepage': 'http://HOMEPAGE1', 'expect_effname': 'ok1'},
            {'name': 'p3', 'version': '1.0', 'homepage': 'http://homepage2', 'expect_effname': 'ok2'},
            {'name': 'p4', 'version': '1.0', 'homepage': 'http://HOMEPAGE2', 'expect_effname': 'ok2'},
            {'name': 'p5', 'version': '1.0', 'homepage': 'http://homepage3', 'expect_effname': 'ok3'},
            {'name': 'p6', 'version': '1.0', 'homepage': 'http://HOMEPAGE3', 'expect_effname': 'ok3'},
            {'name': 'p7', 'version': '1.0', 'homepage': 'http://homepage4', 'expect_effname': 'ok4'},
            {'name': 'p8', 'version': '1.0', 'homepage': 'http://HOMEPAGE4', 'expect_effname': 'ok4'},
        )

    def test_match_summpart(self) -> None:
        self.check_transformer(
            '[ { summpart: Browser, setname: match }, { wwwpart: shouldnotmatch, setname: false } ]',
            {'name': 'p1', 'version': '1.0', 'comment': 'Web browseR', 'expect_effname': 'match'},
            {'name': 'p2', 'version': '1.0', 'comment': 'Another', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '1.0', 'expect_effname': 'p3'},
        )

    def test_match_ruleset(self) -> None:
        self.check_transformer(
            '[ { ruleset: foo, setname: quux }, { ruleset: [ baz ], setname: bat } ]',
            {'name': 'p1', 'version': '1.0', 'repo': 'foo', 'expect_effname': 'quux'},
            {'name': 'p2', 'version': '2.0', 'repo': 'bar', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '3.0', 'repo': 'baz', 'expect_effname': 'bat'}
        )

    def test_match_noruleset(self) -> None:
        self.check_transformer(
            '[ { noruleset: baz, setname: bat } ]',
            {'name': 'p1', 'version': '1.0', 'repo': 'foo', 'expect_effname': 'bat'},
            {'name': 'p2', 'version': '2.0', 'repo': 'bar', 'expect_effname': 'bat'},
            {'name': 'p3', 'version': '3.0', 'repo': 'baz', 'expect_effname': 'p3'}
        )

    def test_match_category(self) -> None:
        self.check_transformer(
            '[ { category: foo, setname: quux }, { category: [ baz ], setname: bat } ]',
            {'name': 'p1', 'version': '1.0', 'category': 'foo', 'expect_effname': 'quux'},
            {'name': 'p2', 'version': '2.0', 'category': 'bar', 'expect_effname': 'p2'},
            {'name': 'p3', 'version': '3.0', 'category': 'baz', 'expect_effname': 'bat'}
        )

    def test_match_category_case(self) -> None:
        self.check_transformer(
            '[ { category: categ1, setname: ok1 }, { category: CATEG2, setname: ok2 }, { category: categ3, setname: ok3 }, { category: CATEG4, setname: ok4 } ]',
            {'name': 'p1', 'version': '1.0', 'category': 'categ1', 'expect_effname': 'ok1'},
            {'name': 'p2', 'version': '1.0', 'category': 'CATEG1', 'expect_effname': 'ok1'},
            {'name': 'p3', 'version': '1.0', 'category': 'categ2', 'expect_effname': 'ok2'},
            {'name': 'p4', 'version': '1.0', 'category': 'CATEG2', 'expect_effname': 'ok2'},
            {'name': 'p5', 'version': '1.0', 'category': 'categ3', 'expect_effname': 'ok3'},
            {'name': 'p6', 'version': '1.0', 'category': 'CATEG3', 'expect_effname': 'ok3'},
            {'name': 'p7', 'version': '1.0', 'category': 'categ4', 'expect_effname': 'ok4'},
            {'name': 'p8', 'version': '1.0', 'category': 'CATEG4', 'expect_effname': 'ok4'},
        )

    def test_match_maintainer(self) -> None:
        self.check_transformer(
            '[ { maintainer: "Foo@bAz.com", setname: quux }, { maintainer: [ "Bar@baZ.com" ], setname: bat } ]',
            {'name': 'p1', 'version': '1.0', 'maintainers': ['foo@baz.COM', 'bbb'], 'expect_effname': 'quux'},
            {'name': 'p2', 'version': '2.0', 'maintainers': ['aaa', 'baR@baz.Com'], 'expect_effname': 'bat'},
            {'name': 'p3', 'version': '3.0', 'maintainers': ['other@foo.com'], 'expect_effname': 'p3'},
            {'name': 'p4', 'version': '3.0', 'expect_effname': 'p4'}
        )

    def test_addflavor(self) -> None:
        self.check_transformer(
            '[ { name: foo, addflavor: fff } ]',
            {'name': 'foo', 'version': '1.0', 'expect_flavors': ['fff']},
            {'name': 'bar', 'version': '1.0', 'expect_flavors': []}
        )

        self.check_transformer(
            '[ { name: foo, addflavor: "$0" } ]',
            {'name': 'foo', 'version': '1.0', 'expect_flavors': ['foo']},
            {'name': 'bar', 'version': '1.0', 'expect_flavors': []}
        )

        self.check_transformer(
            '[ { namepat: "(fo).*", addflavor: "$1" } ]',
            {'name': 'foo', 'version': '1.0', 'expect_flavors': ['fo']},
            {'name': 'bar', 'version': '1.0', 'expect_flavors': []}
        )

        self.check_transformer(
            '[ { name: foo, addflavor: [a,b,c] } ]',
            {'name': 'foo', 'version': '1.0', 'expect_flavors': ['a', 'b', 'c']},
            {'name': 'bar', 'version': '1.0', 'expect_flavors': []}
        )

        self.check_transformer(
            '[ { namepat: "(prefix-)?foo(-suffix)?", addflavor: ["$1", "$2"] } ]',
            {'name': 'prefix-foo-suffix', 'version': '1.0', 'expect_flavors': ['prefix', 'suffix']},
            {'name': 'prefix-foo', 'version': '1.0', 'expect_flavors': ['prefix']},
            {'name': 'foo-suffix', 'version': '1.0', 'expect_flavors': ['suffix']},
            {'name': 'foo', 'version': '1.0', 'expect_flavors': []}
        )

    def test_flags(self) -> None:
        self.check_transformer(
            '[ { name: p1, addflag: xyz }, { flag: xyz, setname: bar }, { noflag: xyz, setname: baz } ]',
            {'name': 'p1', 'version': '1.0', 'expect_effname': 'bar'},
            {'name': 'p2', 'version': '1.0', 'expect_effname': 'baz'},
        )

    def test_rule_chain(self) -> None:
        self.check_transformer(
            '[ { name: aaa, setname: bbb }, { name: bbb, setname: ccc }, { name: eee, setname: fff }, { name: ddd, setname: eee } ]',
            {'name': 'aaa', 'version': '1.0', 'expect_effname': 'ccc'},
            {'name': 'bbb', 'version': '1.0', 'expect_effname': 'ccc'},
            {'name': 'ddd', 'version': '1.0', 'expect_effname': 'eee'},
            {'name': 'eee', 'version': '1.0', 'expect_effname': 'fff'}
        )


if __name__ == '__main__':
    unittest.main()
