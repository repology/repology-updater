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

from repology.package import PackageFlags as Pf

from . import check_transformer
from ..package import PackageSample


def test_flag_chain() -> None:
    check_transformer(
        '[ { name: p1, addflag: xyz }, { flag: xyz, setname: bar }, { noflag: xyz, setname: baz } ]',
        PackageSample(name='p1', version='1.0').expect(effname='bar'),
        PackageSample(name='p2', version='1.0').expect(effname='baz'),
    )


def test_setname_chain() -> None:
    check_transformer(
        '[ { name: aaa, setname: bbb }, { name: bbb, setname: ccc }, { name: eee, setname: fff }, { name: ddd, setname: eee } ]',
        PackageSample(name='aaa', version='1.0').expect(effname='ccc'),
        PackageSample(name='bbb', version='1.0').expect(effname='ccc'),
        PackageSample(name='ddd', version='1.0').expect(effname='eee'),
        PackageSample(name='eee', version='1.0').expect(effname='fff'),
    )


def test_multiflags() -> None:
    check_transformer(
        '[ { devel: true, ignore: false, noscheme: true }, { ignore: true, noscheme: false } ]',
        PackageSample(name='aaa', version='1.0').expect(flags=Pf.DEVEL | Pf.IGNORE),
    )
