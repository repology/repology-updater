# Copyright (C) 2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import pytest

from repology.package import PackageFlags as Pf
from repology.parsers.versions import parse_debian_version


def test_basic() -> None:
    assert parse_debian_version('1.2.3-1') == ('1.2.3', 0)


def test_revision() -> None:
    assert parse_debian_version('1.2.3-1.2.3') == ('1.2.3', 0)


def test_revision_is_not_greedy() -> None:
    assert parse_debian_version('1-2-3-4')[0] == '1-2-3'


@pytest.mark.xfail(reason='cannot tell this case from snapshots like 1-20210101')
def test_minus_parts_do_not_produce_extra_flags() -> None:
    assert parse_debian_version('1-2-3-4')[1] == 0


def test_epoch() -> None:
    assert parse_debian_version('1:1.2.3-1') == ('1.2.3', 0)


@pytest.mark.parametrize('suffix', [
    '+dfsg',
    '+dfsg1',
    '+dfsg1.3',
    '+ds3',
])
def test_garbage_suffixes(suffix) -> None:
    assert parse_debian_version(f'1.1.2{suffix}-2') == ('1.1.2', 0)


def test_inseparable_garbage() -> None:
    assert parse_debian_version('1.1.2dfsg3') == ('1.1.2dfsg3', Pf.INCORRECT)


@pytest.mark.parametrize('version,expected_flags', [
    # known good prerelease suffixes
    ('1.1.2~alpha1', Pf.DEVEL),
    ('1.1.2-alpha1', Pf.DEVEL),
    ('1.1.2+alpha1', Pf.DEVEL),
    ('1.1.2~beta1', Pf.DEVEL),
    ('1.1.2-beta1', Pf.DEVEL),
    ('1.1.2+beta1', Pf.DEVEL),
    ('1.1.2~rc1', Pf.DEVEL),
    ('1.1.2-rc1', Pf.DEVEL),
    ('1.1.2+rc1', Pf.DEVEL),
    ('1.1.2~beta.1', Pf.DEVEL),
    ('1.1.2-beta.1', Pf.DEVEL),
    ('1.1.2+beta.1', Pf.DEVEL),
    ('1.1.2~beta', Pf.DEVEL),
    ('1.1.2-beta', Pf.DEVEL),
    ('1.1.2+beta', Pf.DEVEL),

    # known good postrelease suffixes
    ('1.1.2+post1', 0),
    ('1.1.2-post1', 0),

    # good short prerelease suffixes (we know it's prerelease by ~)
    ('1.1.2~a', Pf.DEVEL),
    ('1.1.2~b', Pf.DEVEL),
    ('1.1.2~a1', Pf.DEVEL),
    ('1.1.2~b1', Pf.DEVEL),
    pytest.param('1.1.2~a.1', Pf.DEVEL, marks=pytest.mark.xfail(reason='not supported, but may be depending on amount of false positives')),
    pytest.param('1.1.2~b.1', Pf.DEVEL, marks=pytest.mark.xfail(reason='not supported, but may be depending on amount of false positives')),

    # unknown pre suffixes
    ('1.1.2~c1', Pf.INCORRECT),
    ('1.1.2~git20210101', Pf.INCORRECT),
    ('1.1.2~20210101', Pf.INCORRECT),
    ('1.1.2~b20212121', Pf.INCORRECT),

    # unknown pre suffixes, but version is 0
    ('0~c1', Pf.IGNORE),
    ('0~git20210101', Pf.IGNORE),
    ('0~20210101', Pf.IGNORE),
    ('0~b20212121', Pf.IGNORE),

    # unknown post suffixes
    ('1.1.2+c1', Pf.IGNORE | Pf.ANY_IS_PATCH),
    ('1.1.2+git20210101', Pf.IGNORE | Pf.ANY_IS_PATCH),
    ('1.1.2+20210101+git20210101', Pf.IGNORE | Pf.ANY_IS_PATCH),
    ('1.1.2+20210101', Pf.IGNORE),

    # "really" crap instead of epochs
    ('2really1', Pf.INCORRECT),
    ('2is1', Pf.INCORRECT),
    ('2.is.really.1', Pf.INCORRECT),
])
def test_suffixes(version, expected_flags) -> None:
    assert parse_debian_version(f'{version}-1') == (version, expected_flags)


@pytest.mark.parametrize('version,expected_version,expected_flags', [
    pytest.param('1.0.0+git20170913.6.c70cbf6-4', '1.0.0+git20170913.6.c70cbf6', Pf.IGNORE | Pf.ANY_IS_PATCH),
    pytest.param('5.0.4+post1-1', '5.0.4+post1', 0, id='yubioath-desktop'),
    pytest.param('1.2.post4+dfsg-2', '1.2.post4', 0, id='pgzero'),
])
def test_real_world(version, expected_version, expected_flags):
    fixed_version, flags = parse_debian_version(version)
    assert fixed_version == expected_version
    assert flags == expected_flags


@pytest.mark.parametrize('version,expected_version,expected_flags', [
    pytest.param('0.F-2-1', '0.F-2', 0, id='cataclysm-dda'),
    pytest.param('1.4.6+really1.4.2-2', '1.4.6+really1.4.2', Pf.INCORRECT, id='nim'),
])
def test_real_world_weak(version, expected_version, expected_flags):
    fixed_version, flags = parse_debian_version(version)
    assert fixed_version == expected_version
    assert flags & expected_flags == expected_flags
