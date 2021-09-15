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
from repology.parsers.versions import parse_rpm_version


def test_basic() -> None:
    assert parse_rpm_version([], '1.2.3', '1') == ('1.2.3', 0)


def test_release_starts_with_zero() -> None:
    # Release starts with zero - potentially prerelease or a snapshot
    assert parse_rpm_version([], '1.2.3', '0') == ('1.2.3', Pf.IGNORE)


def test_release_contains_date() -> None:
    # Release suggests snapshot, even if it doesn't start with zero
    assert parse_rpm_version([], '1.2.3', '1.20200101') == ('1.2.3', Pf.IGNORE)


def test_release_contains_good_prerelease() -> None:
    assert parse_rpm_version([], '1.2.3', '1.alpha1') == ('1.2.3-alpha1', 0)
    assert parse_rpm_version([], '1.2.3', '1.beta1') == ('1.2.3-beta1', 0)
    assert parse_rpm_version([], '1.2.3', '1.pre1') == ('1.2.3-pre1', 0)

    assert parse_rpm_version([], '1.2.3', '1alpha1') == ('1.2.3-alpha1', 0)
    assert parse_rpm_version([], '1.2.3', '1beta1') == ('1.2.3-beta1', 0)
    assert parse_rpm_version([], '1.2.3', '1pre1') == ('1.2.3-pre1', 0)


@pytest.mark.xfail(reason='not implemented yet, prone to false positives')
def test_release_contains_good_prerelease_dot_separated() -> None:
    assert parse_rpm_version([], '1.2.3', '1.alpha.1') == ('1.2.3-alpha.1', 0)
    assert parse_rpm_version([], '1.2.3', '1.beta.1') == ('1.2.3-beta.1', 0)
    assert parse_rpm_version([], '1.2.3', '1.pre.1') == ('1.2.3-pre.1', 0)

    assert parse_rpm_version([], '1.2.3', '1alpha.1') == ('1.2.3-alpha.1', 0)
    assert parse_rpm_version([], '1.2.3', '1beta.1') == ('1.2.3-beta.1', 0)
    assert parse_rpm_version([], '1.2.3', '1pre.1') == ('1.2.3-pre.1', 0)


def test_release_contains_letters() -> None:
    # Release contains letters, likely garbage
    assert parse_rpm_version([], '1.2.3', '1.garbage') == ('1.2.3', Pf.IGNORE)


def test_release_tag() -> None:
    # Tags may be removed
    assert parse_rpm_version(['el'], '1.2.3', '1.el6') == ('1.2.3', 0)


@pytest.mark.xfail(reason='not fixed yet')
def test_release_tag_glued() -> None:
    # Removed tags should not corrupt prerelease versions
    assert parse_rpm_version(['el'], '1.2.3', '1beta3el6') == ('1.2.3-beta3', 0)


@pytest.mark.xfail(reason='not implemented')
def test_misc_asciidoctor() -> None:
    assert parse_rpm_version(['fc'], '1.5.0', '0.2.alpha.13.fc26') == ('1.5.0-alpha.13', 0)


@pytest.mark.xfail(reason='not implemented')
def test_misc_roundcube() -> None:
    assert parse_rpm_version(['mga'], '1.5', '0.beta.2.mga8') == ('1.5-beta.2', 0)
