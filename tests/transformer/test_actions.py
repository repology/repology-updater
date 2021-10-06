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

# mypy: no-disallow-untyped-calls

from repology.package import PackageFlags as Pf

from . import check_transformer
from ..package import PackageSample


def test_remove_true() -> None:
    check_transformer(
        '[ { name: p1, remove: true } ]',
        PackageSample(name='p1', version='1.0').expect(flags=Pf.REMOVE),
        PackageSample(name='p2', version='1.0').expect(flags=0),
    )


def test_remove_false() -> None:
    check_transformer(
        '[ { name: p1, remove: false } ]',
        PackageSample(name='p1', version='1.0', flags=Pf.REMOVE).expect(flags=0),
        PackageSample(name='p2', version='1.0', flags=Pf.REMOVE).expect(flags=Pf.REMOVE),
    )


def test_ignore_true() -> None:
    check_transformer(
        '[ { name: p1, ignore: true } ]',
        PackageSample(name='p1', version='1.0').expect(flags=Pf.IGNORE),
        PackageSample(name='p2', version='1.0').expect(flags=0),
    )


def test_ignore_false() -> None:
    check_transformer(
        '[ { name: p1, ignore: false } ]',
        PackageSample(name='p1', version='1.0', flags=Pf.IGNORE).expect(flags=0),
        PackageSample(name='p2', version='1.0', flags=Pf.IGNORE).expect(flags=Pf.IGNORE),
    )


def test_devel_true() -> None:
    check_transformer(
        '[ { name: p1, devel: true } ]',
        PackageSample(name='p1', version='1.0').expect(flags=Pf.DEVEL),
        PackageSample(name='p2', version='1.0').expect(flags=0),
    )


def test_devel_false() -> None:
    check_transformer(
        '[ { name: p1, devel: false } ]',
        PackageSample(name='p1', version='1.0', flags=Pf.DEVEL).expect(flags=0),
        PackageSample(name='p2', version='1.0', flags=Pf.DEVEL).expect(flags=Pf.DEVEL),
    )


def test_stable_true() -> None:
    check_transformer(
        '[ { name: p1, stable: true } ]',
        PackageSample(name='p1', version='1.0').expect(flags=Pf.STABLE),
        PackageSample(name='p2', version='1.0').expect(flags=0),
    )


def test_stable_false() -> None:
    check_transformer(
        '[ { name: p1, stable: false } ]',
        PackageSample(name='p1', version='1.0', flags=Pf.STABLE).expect(flags=0),
        PackageSample(name='p2', version='1.0', flags=Pf.STABLE).expect(flags=Pf.STABLE),
    )


def test_altver_true() -> None:
    check_transformer(
        '[ { name: p1, altver: true } ]',
        PackageSample(name='p1', version='1.0').expect(flags=Pf.ALTVER),
        PackageSample(name='p2', version='1.0').expect(flags=0),
    )


def test_altver_false() -> None:
    check_transformer(
        '[ { name: p1, altver: false } ]',
        PackageSample(name='p1', version='1.0', flags=Pf.ALTVER).expect(flags=0),
        PackageSample(name='p2', version='1.0', flags=Pf.ALTVER).expect(flags=Pf.ALTVER),
    )


def test_vulnerable_true() -> None:
    check_transformer(
        '[ { name: p1, vulnerable: true } ]',
        PackageSample(name='p1', version='1.0').expect(flags=Pf.VULNERABLE),
        PackageSample(name='p2', version='1.0').expect(flags=0),
    )


def test_vulnerable_false() -> None:
    check_transformer(
        '[ { name: p1, vulnerable: false } ]',
        PackageSample(name='p1', version='1.0', flags=Pf.VULNERABLE).expect(flags=0),
        PackageSample(name='p2', version='1.0', flags=Pf.VULNERABLE).expect(flags=Pf.VULNERABLE),
    )


def test_setbranch() -> None:
    check_transformer(
        '[ { setbranch: "9.x" } ]',
        PackageSample().expect(branch='9.x'),
    )


def test_setbranchcomps() -> None:
    check_transformer(
        '[ { setbranchcomps: 1 } ]',
        PackageSample(version='1.2.3.4').expect(branch='1'),
    )

    check_transformer(
        '[ { setbranchcomps: 2 } ]',
        PackageSample(version='1.2.3.4').expect(branch='1.2'),
    )

    check_transformer(
        '[ { setbranchcomps: 3 } ]',
        PackageSample(version='1.2.3.4').expect(branch='1.2.3'),
    )

    check_transformer(
        '[ { setbranchcomps: 5 } ]',
        PackageSample(version='1.2.3.4').expect(branch='1.2.3.4'),
    )


def test_setname() -> None:
    check_transformer(
        '[ { setname: "bar" } ]',
        PackageSample(name='foo', version='1.0').expect(name='foo', effname='bar'),
    )


def test_setname_subst() -> None:
    check_transformer(
        '[ { setname: "bar_$0" } ]',
        PackageSample(name='foo', version='1.0').expect(name='foo', effname='bar_foo'),
    )


def test_setname_reverse_subst() -> None:
    check_transformer(
        '[ { setname: foo, name: [ $0-client, $0-server ] } ]',
        PackageSample(name='foo-client', version='1.0').expect(effname='foo'),
        PackageSample(name='foo-server', version='1.0').expect(effname='foo'),
        PackageSample(name='foo-other', version='1.0').expect(effname='foo-other'),
    )

    check_transformer(
        '[ { setname: foo, namepat: "$0-(client|server)" } ]',
        PackageSample(name='foo-client', version='1.0').expect(effname='foo'),
        PackageSample(name='foo-server', version='1.0').expect(effname='foo'),
        PackageSample(name='foo-other', version='1.0').expect(effname='foo-other'),
    )


def test_setver() -> None:
    check_transformer(
        '[ { setver: "2.0" } ]',
        PackageSample(name='foo', version='1.0').expect(version='2.0'),
    )


def test_setver_subst() -> None:
    check_transformer(
        '[ { setver: "2.$0" } ]',
        PackageSample(name='foo', version='1.0').expect(version='2.1.0'),
    )
    check_transformer(
        '[ { verpat: "([0-9]+)\\\\.([0-9]+)", setver: "$2.$1" } ]',
        PackageSample(name='foo', version='1.0').expect(version='0.1'),
    )


def test_setver_setname_subst() -> None:
    check_transformer(
        '[ { namepat: "f(.*)", verpat: "1(.*)", setname: "$1/$0", setver: "$1/$0" } ]',
        PackageSample(name='foo', version='1.0').expect(effname='oo/foo', version='.0/1.0'),
    )


def test_tolowername() -> None:
    check_transformer(
        '[ { tolowername: true } ]',
        PackageSample(name='fOoBaR', version='1.0').expect(name='fOoBaR', effname='foobar'),
    )


def test_last() -> None:
    check_transformer(
        '[ { last: true }, { setname: "bar" } ]',
        PackageSample(name='foo', version='1.0').expect(effname='foo'),
    )


def test_addflavor() -> None:
    check_transformer(
        '[ { name: foo, addflavor: fff } ]',
        PackageSample(name='foo', version='1.0').expect(flavors=['fff']),
        PackageSample(name='bar', version='1.0').expect(flavors=[]),
    )

    check_transformer(
        '[ { name: foo, addflavor: "$0" } ]',
        PackageSample(name='foo', version='1.0').expect(flavors=['foo']),
        PackageSample(name='bar', version='1.0').expect(flavors=[]),
    )

    check_transformer(
        '[ { namepat: "(fo).*", addflavor: "$1" } ]',
        PackageSample(name='foo', version='1.0').expect(flavors=['fo']),
        PackageSample(name='bar', version='1.0').expect(flavors=[]),
    )

    check_transformer(
        '[ { name: foo, addflavor: [a,b,c] } ]',
        PackageSample(name='foo', version='1.0').expect(flavors=['a', 'b', 'c']),
        PackageSample(name='bar', version='1.0').expect(flavors=[]),
    )

    check_transformer(
        '[ { namepat: "(prefix-)?foo(-suffix)?", addflavor: ["$1", "$2"] } ]',
        PackageSample(name='prefix-foo-suffix', version='1.0').expect(flavors=['prefix', 'suffix']),
        PackageSample(name='prefix-foo', version='1.0').expect(flavors=['prefix']),
        PackageSample(name='foo-suffix', version='1.0').expect(flavors=['suffix']),
        PackageSample(name='foo', version='1.0').expect(flavors=[]),
    )
