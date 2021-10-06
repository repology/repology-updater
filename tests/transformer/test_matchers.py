# Copyright (C) 2016-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.package import LinkType as Lt

from . import check_transformer
from ..package import PackageSample


def test_name() -> None:
    check_transformer(
        '[ { name: p1, setname: bar }, { name: [p3], setname: baz } ]',
        PackageSample(name='p1', version='1.0').expect(effname='bar'),
        PackageSample(name='p2', version='2.0').expect(effname='p2'),
        PackageSample(name='p3', version='2.0').expect(effname='baz'),
    )


def test_name_multi() -> None:
    # XXX: may not in fact cover multi-name branch of `name' matcher
    # bacause rules with multiple names are split to single-name rules
    # in Ruleset as an optimization
    check_transformer(
        '[ { name: [p1,p2], setname: bar } ]',
        PackageSample(name='p1', version='1.0').expect(effname='bar'),
        PackageSample(name='p2', version='2.0').expect(effname='bar'),
        PackageSample(name='p3', version='2.0').expect(effname='p3'),
    )


def test_namepat() -> None:
    check_transformer(
        '[ { namepat: ".*1", setname: bar } ]',
        PackageSample(name='p1', version='1.0').expect(effname='bar'),
        PackageSample(name='p2', version='2.0').expect(effname='p2'),
    )

    check_transformer(
        '[ { namepat: "p.*", setname: bar } ]',
        PackageSample(name='p1', version='1.0').expect(effname='bar'),
        PackageSample(name='p2', version='2.0').expect(effname='bar'),
    )

    check_transformer(
        '[ { namepat: "p", setname: bar }, { namepat: "1", setname: bar }, { namepat: ".", setname: bar } ] ',
        PackageSample(name='p1', version='1.0').expect(effname='p1'),
        PackageSample(name='p2', version='2.0').expect(effname='p2'),
    )

    check_transformer(
        '[ { namepat: "p2", setname: bar } ]',
        PackageSample(name='p1', version='1.0').expect(effname='p1'),
        PackageSample(name='p2', version='2.0').expect(effname='bar'),
    )


def test_ver() -> None:
    check_transformer(
        '[ { ver: "1.0", setname: bar }, { ver: ["3.0"], setname: baz } ]',
        PackageSample(name='p1', version='1.0').expect(effname='bar'),
        PackageSample(name='p2', version='2.0').expect(effname='p2'),
        PackageSample(name='p3', version='3.0').expect(effname='baz'),
    )


def test_notver() -> None:
    check_transformer(
        '[ { notver: "1.0", setname: bar }, { notver: ["1.0", "3.0"], setname: baz } ]',
        PackageSample(name='p1', version='1.0').expect(effname='p1'),
        PackageSample(name='p2', version='2.0').expect(effname='baz'),
        PackageSample(name='p3', version='3.0').expect(effname='bar'),
    )


def test_verpat() -> None:
    check_transformer(
        '[ { verpat: "1.*", setname: bar } ]',
        PackageSample(name='p1', version='1.0').expect(effname='bar'),
        PackageSample(name='p2', version='2.0').expect(effname='p2'),
        PackageSample(name='p3', version='2.1').expect(effname='p3'),
    )


def test_verpat_case_ignored() -> None:
    check_transformer(
        '[ { verpat: ".*beta.*", setname: bar } ]',
        PackageSample(name='p1', version='1beta1').expect(effname='bar'),
        PackageSample(name='p2', version='1BETA2').expect(effname='bar'),
    )


def test_verlonger() -> None:
    check_transformer(
        '[ { verlonger: 2, setname: bar } ]',
        PackageSample(name='p1', version='1.0.0').expect(effname='bar'),
        PackageSample(name='p2', version='1.0').expect(effname='p2'),
        PackageSample(name='p3', version='1-0-0').expect(effname='bar'),
    )


def test_vergt() -> None:
    check_transformer(
        '[ { vergt: "1.0", setname: bar } ]',
        PackageSample(name='p1', version='0.9').expect(effname='p1'),
        PackageSample(name='p2', version='1.0').expect(effname='p2'),
        PackageSample(name='p3', version='1.1').expect(effname='bar'),
    )


def test_verge() -> None:
    check_transformer(
        '[ { verge: "1.0", setname: bar } ]',
        PackageSample(name='p1', version='0.9').expect(effname='p1'),
        PackageSample(name='p2', version='1.0').expect(effname='bar'),
        PackageSample(name='p3', version='1.1').expect(effname='bar'),
    )


def test_verlt() -> None:
    check_transformer(
        '[ { verlt: "1.0", setname: bar } ]',
        PackageSample(name='p1', version='0.9').expect(effname='bar'),
        PackageSample(name='p2', version='1.0').expect(effname='p2'),
        PackageSample(name='p3', version='1.1').expect(effname='p3'),
    )


def test_verle() -> None:
    check_transformer(
        '[ { verle: "1.0", setname: bar } ]',
        PackageSample(name='p1', version='0.9').expect(effname='bar'),
        PackageSample(name='p2', version='1.0').expect(effname='bar'),
        PackageSample(name='p3', version='1.1').expect(effname='p3'),
    )


def test_vereq() -> None:
    check_transformer(
        '[ { vereq: "1.0", setname: bar } ]',
        PackageSample(name='p1', version='0.9').expect(effname='p1'),
        PackageSample(name='p2', version='1.0').expect(effname='bar'),
        PackageSample(name='p3', version='01.00.00').expect(effname='bar'),
        PackageSample(name='p4', version='1.1').expect(effname='p4'),
    )


def test_verne() -> None:
    check_transformer(
        '[ { verne: "1.0", setname: bar } ]',
        PackageSample(name='p1', version='0.9').expect(effname='bar'),
        PackageSample(name='p2', version='1.0').expect(effname='p2'),
        PackageSample(name='p3', version='01.00.00').expect(effname='p3'),
        PackageSample(name='p4', version='1.1').expect(effname='bar'),
    )


def test_wwwpat() -> None:
    check_transformer(
        '[ { wwwpat: "https?://foo\\\\.com/.*", setname: bar } ]',
        PackageSample(name='p1', version='1.0', links=[(Lt.UPSTREAM_HOMEPAGE, 'https://foo.com/xxx')]).expect(effname='bar'),
        PackageSample(name='p2', version='1.0', links=[(Lt.UPSTREAM_HOMEPAGE, 'http://foo.com/')]).expect(effname='bar'),
        PackageSample(name='p3', version='1.0', links=[(Lt.UPSTREAM_HOMEPAGE, 'http://foo_com/xxx')]).expect(effname='p3'),
        PackageSample(name='p1', version='1.0', links=[(Lt.UPSTREAM_DOWNLOAD, 'https://foo.com/xxx')]).expect(effname='bar'),
        PackageSample(name='p2', version='1.0', links=[(Lt.UPSTREAM_DOWNLOAD, 'http://foo.com/')]).expect(effname='bar'),
        PackageSample(name='p3', version='1.0', links=[(Lt.UPSTREAM_DOWNLOAD, 'http://foo_com/xxx')]).expect(effname='p3'),
        PackageSample(name='p4', version='2.0').expect(effname='p4'),
    )


def test_wwwpart() -> None:
    check_transformer(
        '[ { wwwpart: "foo", setname: bar } ]',
        PackageSample(name='p1', version='1.0', links=[(Lt.UPSTREAM_HOMEPAGE, 'http://foo/xxx')]).expect(effname='bar'),
        PackageSample(name='p2', version='1.0', links=[(Lt.UPSTREAM_HOMEPAGE, 'http://bar.com/yyy')]).expect(effname='p2'),
        PackageSample(name='p1', version='1.0', links=[(Lt.UPSTREAM_DOWNLOAD, 'http://foo/xxx')]).expect(effname='bar'),
        PackageSample(name='p2', version='1.0', links=[(Lt.UPSTREAM_DOWNLOAD, 'http://bar.com/yyy')]).expect(effname='p2'),
        PackageSample(name='p3', version='2.0').expect(effname='p3'),
    )


def test_wwwpart_case() -> None:
    check_transformer(
        '[ { wwwpart: homepage1, setname: ok1 }, { wwwpart: HOMEPAGE2, setname: ok2 }, { wwwpart: homepage3, setname: ok3 }, { wwwpart: HOMEPAGE4, setname: ok4 } ]',
        PackageSample(name='p1', version='1.0', links=[(Lt.UPSTREAM_HOMEPAGE, 'http://homepage1')]).expect(effname='ok1'),
        PackageSample(name='p2', version='1.0', links=[(Lt.UPSTREAM_HOMEPAGE, 'http://HOMEPAGE1')]).expect(effname='ok1'),
        PackageSample(name='p3', version='1.0', links=[(Lt.UPSTREAM_HOMEPAGE, 'http://homepage2')]).expect(effname='ok2'),
        PackageSample(name='p4', version='1.0', links=[(Lt.UPSTREAM_HOMEPAGE, 'http://HOMEPAGE2')]).expect(effname='ok2'),
        PackageSample(name='p5', version='1.0', links=[(Lt.UPSTREAM_HOMEPAGE, 'http://homepage3')]).expect(effname='ok3'),
        PackageSample(name='p6', version='1.0', links=[(Lt.UPSTREAM_HOMEPAGE, 'http://HOMEPAGE3')]).expect(effname='ok3'),
        PackageSample(name='p7', version='1.0', links=[(Lt.UPSTREAM_HOMEPAGE, 'http://homepage4')]).expect(effname='ok4'),
        PackageSample(name='p8', version='1.0', links=[(Lt.UPSTREAM_HOMEPAGE, 'http://HOMEPAGE4')]).expect(effname='ok4'),
    )


def test_summpart() -> None:
    check_transformer(
        '[ { summpart: Browser, setname: match }, { wwwpart: shouldnotmatch, setname: false } ]',
        PackageSample(name='p1', version='1.0', comment='Web browseR').expect(effname='match'),
        PackageSample(name='p2', version='1.0', comment='Another').expect(effname='p2'),
        PackageSample(name='p3', version='1.0').expect(effname='p3'),
    )


def test_ruleset() -> None:
    check_transformer(
        '[ { ruleset: foo, setname: quux }, { ruleset: [ baz ], setname: bat } ]',
        PackageSample(name='p1', version='1.0', repo='foo').expect(effname='quux'),
        PackageSample(name='p2', version='2.0', repo='bar').expect(effname='p2'),
        PackageSample(name='p3', version='3.0', repo='baz').expect(effname='bat'),
    )


def test_noruleset() -> None:
    check_transformer(
        '[ { noruleset: baz, setname: bat } ]',
        PackageSample(name='p1', version='1.0', repo='foo').expect(effname='bat'),
        PackageSample(name='p2', version='2.0', repo='bar').expect(effname='bat'),
        PackageSample(name='p3', version='3.0', repo='baz').expect(effname='p3'),
    )


def test_category() -> None:
    check_transformer(
        '[ { category: foo, setname: quux }, { category: [ baz ], setname: bat } ]',
        PackageSample(name='p1', version='1.0', category='foo').expect(effname='quux'),
        PackageSample(name='p2', version='2.0', category='bar').expect(effname='p2'),
        PackageSample(name='p3', version='3.0', category='baz').expect(effname='bat'),
    )


def test_category_case() -> None:
    check_transformer(
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


def test_maintainer() -> None:
    check_transformer(
        '[ { maintainer: "Foo@bAz.com", setname: quux }, { maintainer: [ "Bar@baZ.com" ], setname: bat } ]',
        PackageSample(name='p1', version='1.0', maintainers=['foo@baz.COM', 'bbb']).expect(effname='quux'),
        PackageSample(name='p2', version='2.0', maintainers=['aaa', 'baR@baz.Com']).expect(effname='bat'),
        PackageSample(name='p3', version='3.0', maintainers=['other@foo.com']).expect(effname='p3'),
        PackageSample(name='p4', version='3.0').expect(effname='p4'),
    )


def test_hasbranch() -> None:
    check_transformer(
        '[ { hasbranch: true, setname: "hasbranch" }, { hasbranch: false, setname: "nobranch" } ]',
        PackageSample().expect(effname='nobranch'),
        PackageSample(branch='foo').expect(effname='hasbranch'),
    )
