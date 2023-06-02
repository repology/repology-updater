# Copyright (C) 2022 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.maintainermgr import MaintainerManager
from repology.yamlloader import YamlConfig


def test_hide():
    config = YamlConfig.from_text(
        """
        - { maintainer: foo@example.com, hide: true }
        - { maintainer: bar@example.com, hide: false }
        - { maintainer: baz@example.com }
        """
    )

    m = MaintainerManager(config)

    assert m.is_hidden('foo@example.com')
    assert not m.is_hidden('bar@example.com')
    assert not m.is_hidden('baz@example.com')
    assert not m.is_hidden('quux@example.com')

    assert m.convert_maintainer('foo@example.com') is None
    assert m.convert_maintainer('bar@example.com') is not None
    assert m.convert_maintainer('baz@example.com') is not None
    assert m.convert_maintainer('quux@example.com') is not None


def test_replace():
    config = YamlConfig.from_text(
        """
        - { maintainer: foo@example.com, replace: baz@example.com }
        - { maintainer: bar@example.com }
        """
    )

    m = MaintainerManager(config)

    assert m.convert_maintainer('foo@example.com') == 'baz@example.com'
    assert m.convert_maintainer('bar@example.com') == 'bar@example.com'
    assert m.convert_maintainer('other@example.com') == 'other@example.com'
