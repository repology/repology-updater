# Copyright (C) 2018-2019,2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.parsers.versions import VersionStripper


def test_identity() -> None:
    assert VersionStripper()('1.2.3') == '1.2.3'


def test_basic() -> None:
    assert VersionStripper().strip_left('.')('1.2.3') == '2.3'
    assert VersionStripper().strip_left_greedy('.')('1.2.3') == '3'
    assert VersionStripper().strip_right('.')('1.2.3') == '1.2'
    assert VersionStripper().strip_right_greedy('.')('1.2.3') == '1'


def test_order() -> None:
    assert VersionStripper().strip_right('_').strip_right(',')('1_2,3_4') == '1_2'
    assert VersionStripper().strip_right(',').strip_right('_')('1_2,3_4') == '1'
