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

from repology.package import PackageFlags as Pf
from repology.repomgr import RepositoryManager
from repology.transformer import PackageTransformer

from .package import PackageSample


repomgr = RepositoryManager(repostext="""
[
    { name: dummyrepo, desc: dummyrepo, family: dummyrepo, sources: [] },
    { name: foo, desc: foo, family: foo, sources: [] },
    { name: bar, desc: bar, family: bar, sources: [] },
    { name: baz, desc: baz, family: baz, sources: [] }
]
""")


class TestPackageTransformer(unittest.TestCase):
    def _check_transformer(self, rulestext: str, *samples: PackageSample) -> None:
        transformer = PackageTransformer(repomgr, rulestext=rulestext)

        for sample in samples:
            transformer.process(sample.package)
            sample.check(self)

    def test_remove(self) -> None:
        self._check_transformer(
            '[ { name: p1, remove: true } ]',
            PackageSample(name='p1', version='1.0').expect(flags=Pf.REMOVE),
            PackageSample(name='p2', version='1.0').expect(flags=0),
        )

    def test_unremove(self) -> None:
        self._check_transformer(
            '[ { name: p1, remove: false } ]',
            PackageSample(name='p1', version='1.0', flags=Pf.REMOVE).expect(flags=0),
            PackageSample(name='p2', version='1.0', flags=Pf.REMOVE).expect(flags=Pf.REMOVE),
        )

    def test_ignore(self) -> None:
        self._check_transformer(
            '[ { name: p1, ignore: true } ]',
            PackageSample(name='p1', version='1.0').expect(flags=Pf.IGNORE),
            PackageSample(name='p2', version='1.0').expect(flags=0),
        )

    def test_unignore(self) -> None:
        self._check_transformer(
            '[ { name: p1, ignore: false } ]',
            PackageSample(name='p1', version='1.0', flags=Pf.IGNORE).expect(flags=0),
            PackageSample(name='p2', version='1.0', flags=Pf.IGNORE).expect(flags=Pf.IGNORE),
        )

    def test_devel(self) -> None:
        self._check_transformer(
            '[ { name: p1, devel: true } ]',
            PackageSample(name='p1', version='1.0').expect(flags=Pf.DEVEL),
            PackageSample(name='p2', version='1.0').expect(flags=0),
        )

    def test_undevel(self) -> None:
        self._check_transformer(
            '[ { name: p1, devel: false } ]',
            PackageSample(name='p1', version='1.0', flags=Pf.DEVEL).expect(flags=0),
            PackageSample(name='p2', version='1.0', flags=Pf.DEVEL).expect(flags=Pf.DEVEL),
        )

    def test_stable(self) -> None:
        self._check_transformer(
            '[ { name: p1, stable: true } ]',
            PackageSample(name='p1', version='1.0').expect(flags=Pf.STABLE),
            PackageSample(name='p2', version='1.0').expect(flags=0),
        )

    def test_un_stable(self) -> None:
        self._check_transformer(
            '[ { name: p1, stable: false } ]',
            PackageSample(name='p1', version='1.0', flags=Pf.STABLE).expect(flags=0),
            PackageSample(name='p2', version='1.0', flags=Pf.STABLE).expect(flags=Pf.STABLE),
        )

    def test_altver(self) -> None:
        self._check_transformer(
            '[ { name: p1, altver: true } ]',
            PackageSample(name='p1', version='1.0').expect(flags=Pf.ALTVER),
            PackageSample(name='p2', version='1.0').expect(flags=0),
        )

    def test_un_altver(self) -> None:
        self._check_transformer(
            '[ { name: p1, altver: false } ]',
            PackageSample(name='p1', version='1.0', flags=Pf.ALTVER).expect(flags=0),
            PackageSample(name='p2', version='1.0', flags=Pf.ALTVER).expect(flags=Pf.ALTVER),
        )

    def test_setbranch(self) -> None:
        self._check_transformer(
            '[ { setbranch: "9.x" } ]',
            PackageSample().expect(branch='9.x'),
        )

    def test_setbranchcomps(self) -> None:
        self._check_transformer(
            '[ { setbranchcomps: 1 } ]',
            PackageSample(version='1.2.3.4').expect(branch='1'),
        )

        self._check_transformer(
            '[ { setbranchcomps: 2 } ]',
            PackageSample(version='1.2.3.4').expect(branch='1.2'),
        )

        self._check_transformer(
            '[ { setbranchcomps: 3 } ]',
            PackageSample(version='1.2.3.4').expect(branch='1.2.3'),
        )

        self._check_transformer(
            '[ { setbranchcomps: 5 } ]',
            PackageSample(version='1.2.3.4').expect(branch='1.2.3.4'),
        )

    def test_multiflags(self) -> None:
        self._check_transformer(
            '[ { devel: true, ignore: false, noscheme: true }, { ignore: true, noscheme: false } ]',
            PackageSample(name='aaa', version='1.0').expect(flags=Pf.DEVEL | Pf.IGNORE),
        )

    def test_setname(self) -> None:
        self._check_transformer(
            '[ { setname: "bar" } ]',
            PackageSample(name='foo', version='1.0').expect(name='foo', effname='bar'),
        )

    def test_setname_subst(self) -> None:
        self._check_transformer(
            '[ { setname: "bar_$0" } ]',
            PackageSample(name='foo', version='1.0').expect(name='foo', effname='bar_foo'),
        )

    def test_setname_reverse_subst(self) -> None:
        self._check_transformer(
            '[ { setname: foo, name: [ $0-client, $0-server ] } ]',
            PackageSample(name='foo-client', version='1.0').expect(effname='foo'),
            PackageSample(name='foo-server', version='1.0').expect(effname='foo'),
            PackageSample(name='foo-other', version='1.0').expect(effname='foo-other'),
        )

        self._check_transformer(
            '[ { setname: foo, namepat: "$0-(client|server)" } ]',
            PackageSample(name='foo-client', version='1.0').expect(effname='foo'),
            PackageSample(name='foo-server', version='1.0').expect(effname='foo'),
            PackageSample(name='foo-other', version='1.0').expect(effname='foo-other'),
        )

    def test_setver(self) -> None:
        self._check_transformer(
            '[ { setver: "2.0" } ]',
            PackageSample(name='foo', version='1.0').expect(version='2.0'),
        )

    def test_setver_subst(self) -> None:
        self._check_transformer(
            '[ { setver: "2.$0" } ]',
            PackageSample(name='foo', version='1.0').expect(version='2.1.0'),
        )
        self._check_transformer(
            '[ { verpat: "([0-9]+)\\\\.([0-9]+)", setver: "$2.$1" } ]',
            PackageSample(name='foo', version='1.0').expect(version='0.1'),
        )

    def test_setver_setname_subst(self) -> None:
        self._check_transformer(
            '[ { namepat: "f(.*)", verpat: "1(.*)", setname: "$1/$0", setver: "$1/$0" } ]',
            PackageSample(name='foo', version='1.0').expect(effname='oo/foo', version='.0/1.0'),
        )

    def test_tolowername(self) -> None:
        self._check_transformer(
            '[ { tolowername: true } ]',
            PackageSample(name='fOoBaR', version='1.0').expect(name='fOoBaR', effname='foobar'),
        )

    def test_last(self) -> None:
        self._check_transformer(
            '[ { last: true }, { setname: "bar" } ]',
            PackageSample(name='foo', version='1.0').expect(effname='foo'),
        )

    def test_match_name(self) -> None:
        self._check_transformer(
            '[ { name: p1, setname: bar }, { name: [p3], setname: baz } ]',
            PackageSample(name='p1', version='1.0').expect(effname='bar'),
            PackageSample(name='p2', version='2.0').expect(effname='p2'),
            PackageSample(name='p3', version='2.0').expect(effname='baz'),
        )

    def test_match_name_multi(self) -> None:
        self._check_transformer(
            '[ { name: [p1,p2], setname: bar } ]',
            PackageSample(name='p1', version='1.0').expect(effname='bar'),
            PackageSample(name='p2', version='2.0').expect(effname='bar'),
            PackageSample(name='p3', version='2.0').expect(effname='p3'),
        )

    def test_match_namepat(self) -> None:
        self._check_transformer(
            '[ { namepat: ".*1", setname: bar } ]',
            PackageSample(name='p1', version='1.0').expect(effname='bar'),
            PackageSample(name='p2', version='2.0').expect(effname='p2'),
        )

        self._check_transformer(
            '[ { namepat: "p.*", setname: bar } ]',
            PackageSample(name='p1', version='1.0').expect(effname='bar'),
            PackageSample(name='p2', version='2.0').expect(effname='bar'),
        )

        self._check_transformer(
            '[ { namepat: "p", setname: bar }, { namepat: "1", setname: bar }, { namepat: ".", setname: bar } ] ',
            PackageSample(name='p1', version='1.0').expect(effname='p1'),
            PackageSample(name='p2', version='2.0').expect(effname='p2'),
        )

        self._check_transformer(
            '[ { namepat: "p2", setname: bar } ]',
            PackageSample(name='p1', version='1.0').expect(effname='p1'),
            PackageSample(name='p2', version='2.0').expect(effname='bar'),
        )

    def test_match_ver(self) -> None:
        self._check_transformer(
            '[ { ver: "1.0", setname: bar }, { ver: ["3.0"], setname: baz } ]',
            PackageSample(name='p1', version='1.0').expect(effname='bar'),
            PackageSample(name='p2', version='2.0').expect(effname='p2'),
            PackageSample(name='p3', version='3.0').expect(effname='baz'),
        )

    def test_match_vernot(self) -> None:
        self._check_transformer(
            '[ { notver: "1.0", setname: bar }, { notver: ["1.0", "3.0"], setname: baz } ]',
            PackageSample(name='p1', version='1.0').expect(effname='p1'),
            PackageSample(name='p2', version='2.0').expect(effname='baz'),
            PackageSample(name='p3', version='3.0').expect(effname='bar'),
        )

    def test_match_verpat(self) -> None:
        self._check_transformer(
            '[ { verpat: "1.*", setname: bar } ]',
            PackageSample(name='p1', version='1.0').expect(effname='bar'),
            PackageSample(name='p2', version='2.0').expect(effname='p2'),
        )

    def test_match_verpat_case_ignored(self) -> None:
        self._check_transformer(
            '[ { verpat: ".*beta.*", setname: bar } ]',
            PackageSample(name='p1', version='1beta1').expect(effname='bar'),
            PackageSample(name='p2', version='1BETA2').expect(effname='bar'),
        )

    def test_match_verlonger(self) -> None:
        self._check_transformer(
            '[ { verlonger: 2, setname: bar } ]',
            PackageSample(name='p1', version='1.0.0').expect(effname='bar'),
            PackageSample(name='p2', version='1.0').expect(effname='p2'),
            PackageSample(name='p3', version='1-0-0').expect(effname='bar'),
        )

    def test_match_vergt(self) -> None:
        self._check_transformer(
            '[ { vergt: "1.0", setname: bar } ]',
            PackageSample(name='p1', version='0.9').expect(effname='p1'),
            PackageSample(name='p2', version='1.0').expect(effname='p2'),
            PackageSample(name='p3', version='1.1').expect(effname='bar'),
        )

    def test_match_verge(self) -> None:
        self._check_transformer(
            '[ { verge: "1.0", setname: bar } ]',
            PackageSample(name='p1', version='0.9').expect(effname='p1'),
            PackageSample(name='p2', version='1.0').expect(effname='bar'),
            PackageSample(name='p3', version='1.1').expect(effname='bar'),
        )

    def test_match_verlt(self) -> None:
        self._check_transformer(
            '[ { verlt: "1.0", setname: bar } ]',
            PackageSample(name='p1', version='0.9').expect(effname='bar'),
            PackageSample(name='p2', version='1.0').expect(effname='p2'),
            PackageSample(name='p3', version='1.1').expect(effname='p3'),
        )

    def test_match_verle(self) -> None:
        self._check_transformer(
            '[ { verle: "1.0", setname: bar } ]',
            PackageSample(name='p1', version='0.9').expect(effname='bar'),
            PackageSample(name='p2', version='1.0').expect(effname='bar'),
            PackageSample(name='p3', version='1.1').expect(effname='p3'),
        )

    def test_match_vereq(self) -> None:
        self._check_transformer(
            '[ { vereq: "1.0", setname: bar } ]',
            PackageSample(name='p1', version='0.9').expect(effname='p1'),
            PackageSample(name='p2', version='1.0').expect(effname='bar'),
            PackageSample(name='p3', version='1.1').expect(effname='p3'),
        )

    def test_match_verne(self) -> None:
        self._check_transformer(
            '[ { verne: "1.0", setname: bar } ]',
            PackageSample(name='p1', version='0.9').expect(effname='bar'),
            PackageSample(name='p2', version='1.0').expect(effname='p2'),
            PackageSample(name='p3', version='1.1').expect(effname='bar'),
        )

    def test_match_wwwpat(self) -> None:
        self._check_transformer(
            '[ { wwwpat: "https?://foo\\\\.com/.*", setname: bar } ]',
            PackageSample(name='p1', version='1.0', homepage='https://foo.com/xxx').expect(effname='bar'),
            PackageSample(name='p2', version='1.0', homepage='http://foo.com/').expect(effname='bar'),
            PackageSample(name='p3', version='1.0', homepage='http://foo_com/xxx').expect(effname='p3'),
            PackageSample(name='p4', version='2.0').expect(effname='p4'),
        )

    def test_match_wwwpart(self) -> None:
        self._check_transformer(
            '[ { wwwpart: "foo", setname: bar } ]',
            PackageSample(name='p1', version='1.0', homepage='http://foo/xxx').expect(effname='bar'),
            PackageSample(name='p2', version='1.0', homepage='http://bar.com/yyy').expect(effname='p2'),
            PackageSample(name='p3', version='2.0').expect(effname='p3'),
        )

    def test_match_wwwpart_case(self) -> None:
        self._check_transformer(
            '[ { wwwpart: homepage1, setname: ok1 }, { wwwpart: HOMEPAGE2, setname: ok2 }, { wwwpart: homepage3, setname: ok3 }, { wwwpart: HOMEPAGE4, setname: ok4 } ]',
            PackageSample(name='p1', version='1.0', homepage='http://homepage1').expect(effname='ok1'),
            PackageSample(name='p2', version='1.0', homepage='http://HOMEPAGE1').expect(effname='ok1'),
            PackageSample(name='p3', version='1.0', homepage='http://homepage2').expect(effname='ok2'),
            PackageSample(name='p4', version='1.0', homepage='http://HOMEPAGE2').expect(effname='ok2'),
            PackageSample(name='p5', version='1.0', homepage='http://homepage3').expect(effname='ok3'),
            PackageSample(name='p6', version='1.0', homepage='http://HOMEPAGE3').expect(effname='ok3'),
            PackageSample(name='p7', version='1.0', homepage='http://homepage4').expect(effname='ok4'),
            PackageSample(name='p8', version='1.0', homepage='http://HOMEPAGE4').expect(effname='ok4'),
        )

    def test_match_summpart(self) -> None:
        self._check_transformer(
            '[ { summpart: Browser, setname: match }, { wwwpart: shouldnotmatch, setname: false } ]',
            PackageSample(name='p1', version='1.0', comment='Web browseR').expect(effname='match'),
            PackageSample(name='p2', version='1.0', comment='Another').expect(effname='p2'),
            PackageSample(name='p3', version='1.0').expect(effname='p3'),
        )

    def test_match_ruleset(self) -> None:
        self._check_transformer(
            '[ { ruleset: foo, setname: quux }, { ruleset: [ baz ], setname: bat } ]',
            PackageSample(name='p1', version='1.0', repo='foo').expect(effname='quux'),
            PackageSample(name='p2', version='2.0', repo='bar').expect(effname='p2'),
            PackageSample(name='p3', version='3.0', repo='baz').expect(effname='bat'),
        )

    def test_match_noruleset(self) -> None:
        self._check_transformer(
            '[ { noruleset: baz, setname: bat } ]',
            PackageSample(name='p1', version='1.0', repo='foo').expect(effname='bat'),
            PackageSample(name='p2', version='2.0', repo='bar').expect(effname='bat'),
            PackageSample(name='p3', version='3.0', repo='baz').expect(effname='p3'),
        )

    def test_match_category(self) -> None:
        self._check_transformer(
            '[ { category: foo, setname: quux }, { category: [ baz ], setname: bat } ]',
            PackageSample(name='p1', version='1.0', category='foo').expect(effname='quux'),
            PackageSample(name='p2', version='2.0', category='bar').expect(effname='p2'),
            PackageSample(name='p3', version='3.0', category='baz').expect(effname='bat'),
        )

    def test_match_category_case(self) -> None:
        self._check_transformer(
            '[ { category: categ1, setname: ok1 }, { category: CATEG2, setname: ok2 }, { category: categ3, setname: ok3 }, { category: CATEG4, setname: ok4 } ]',
            PackageSample(name='p1', version='1.0', category='categ1').expect(effname='ok1'),
            PackageSample(name='p2', version='1.0', category='CATEG1').expect(effname='ok1'),
            PackageSample(name='p3', version='1.0', category='categ2').expect(effname='ok2'),
            PackageSample(name='p4', version='1.0', category='CATEG2').expect(effname='ok2'),
            PackageSample(name='p5', version='1.0', category='categ3').expect(effname='ok3'),
            PackageSample(name='p6', version='1.0', category='CATEG3').expect(effname='ok3'),
            PackageSample(name='p7', version='1.0', category='categ4').expect(effname='ok4'),
            PackageSample(name='p8', version='1.0', category='CATEG4').expect(effname='ok4'),
        )

    def test_match_maintainer(self) -> None:
        self._check_transformer(
            '[ { maintainer: "Foo@bAz.com", setname: quux }, { maintainer: [ "Bar@baZ.com" ], setname: bat } ]',
            PackageSample(name='p1', version='1.0', maintainers=['foo@baz.COM', 'bbb']).expect(effname='quux'),
            PackageSample(name='p2', version='2.0', maintainers=['aaa', 'baR@baz.Com']).expect(effname='bat'),
            PackageSample(name='p3', version='3.0', maintainers=['other@foo.com']).expect(effname='p3'),
            PackageSample(name='p4', version='3.0').expect(effname='p4'),
        )

    def test_addflavor(self) -> None:
        self._check_transformer(
            '[ { name: foo, addflavor: fff } ]',
            PackageSample(name='foo', version='1.0').expect(flavors=['fff']),
            PackageSample(name='bar', version='1.0').expect(flavors=[]),
        )

        self._check_transformer(
            '[ { name: foo, addflavor: "$0" } ]',
            PackageSample(name='foo', version='1.0').expect(flavors=['foo']),
            PackageSample(name='bar', version='1.0').expect(flavors=[]),
        )

        self._check_transformer(
            '[ { namepat: "(fo).*", addflavor: "$1" } ]',
            PackageSample(name='foo', version='1.0').expect(flavors=['fo']),
            PackageSample(name='bar', version='1.0').expect(flavors=[]),
        )

        self._check_transformer(
            '[ { name: foo, addflavor: [a,b,c] } ]',
            PackageSample(name='foo', version='1.0').expect(flavors=['a', 'b', 'c']),
            PackageSample(name='bar', version='1.0').expect(flavors=[]),
        )

        self._check_transformer(
            '[ { namepat: "(prefix-)?foo(-suffix)?", addflavor: ["$1", "$2"] } ]',
            PackageSample(name='prefix-foo-suffix', version='1.0').expect(flavors=['prefix', 'suffix']),
            PackageSample(name='prefix-foo', version='1.0').expect(flavors=['prefix']),
            PackageSample(name='foo-suffix', version='1.0').expect(flavors=['suffix']),
            PackageSample(name='foo', version='1.0').expect(flavors=[]),
        )

    def test_flags(self) -> None:
        self._check_transformer(
            '[ { name: p1, addflag: xyz }, { flag: xyz, setname: bar }, { noflag: xyz, setname: baz } ]',
            PackageSample(name='p1', version='1.0').expect(effname='bar'),
            PackageSample(name='p2', version='1.0').expect(effname='baz'),
        )

    def test_rule_chain(self) -> None:
        self._check_transformer(
            '[ { name: aaa, setname: bbb }, { name: bbb, setname: ccc }, { name: eee, setname: fff }, { name: ddd, setname: eee } ]',
            PackageSample(name='aaa', version='1.0').expect(effname='ccc'),
            PackageSample(name='bbb', version='1.0').expect(effname='ccc'),
            PackageSample(name='ddd', version='1.0').expect(effname='eee'),
            PackageSample(name='eee', version='1.0').expect(effname='fff'),
        )


if __name__ == '__main__':
    unittest.main()
