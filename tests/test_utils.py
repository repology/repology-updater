# Copyright (C) 2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.utils.itertools import chain_optionals, unicalize


def test_chain_optionals():
    assert list(chain_optionals()) == []
    assert list(chain_optionals([])) == []
    assert list(chain_optionals([], [])) == []

    assert list(chain_optionals([0, 1, 2])) == [0, 1, 2]
    assert list(chain_optionals([0, 1, 2], [3, 4, 5])) == [0, 1, 2, 3, 4, 5]
    assert list(chain_optionals(None, [0, 1, 2], None, [3, 4, 5], None)) == [0, 1, 2, 3, 4, 5]

    assert list(chain_optionals(None, range(3), None, range(3, 6), None)) == [0, 1, 2, 3, 4, 5]


def test_unicalize():
    assert list(unicalize([])) == []
    assert list(unicalize([0, 1, 2])) == [0, 1, 2]
    assert list(unicalize([0, 1, 2, 0, 1, 2])) == [0, 1, 2]
