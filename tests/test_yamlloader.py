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

import shutil

from repology.yamlloader import ParsedConfigCache, YamlConfig

from .fixtures import *  # noqa


def test_text():
    config = YamlConfig.from_text(
        """
        - { foo: 1 }
        - { bar: 2 }
        """
    )

    assert config.get_items() == [
        {'foo': 1},
        {'bar': 2},
    ]

    assert config.get_hash() == 'da87f61f7796c806802a20b96d40406533fb91e07945c747ed84124b6277151d'


def test_files(testdata_dir):
    config = YamlConfig.from_path(testdata_dir / 'yaml_configs')

    assert config.get_items() == [
        {'foo': 1},
        {'bar': 2},
        {'baz': 3},
    ]

    assert config.get_hash() == 'd6080e544cb4490aa1381f4cd3892c2f858f01fd6f0897e1d2829b20187b70e9'


def test_cache(testdata_dir, datadir):
    cache = ParsedConfigCache(datadir)

    for _ in ('populate cache', 'use cache'):
        config = YamlConfig.from_path(testdata_dir / 'yaml_configs', cache)

        assert config.get_items() == [
            {'foo': 1},
            {'bar': 2},
            {'baz': 3},
        ]

        assert config.get_hash() == 'd6080e544cb4490aa1381f4cd3892c2f858f01fd6f0897e1d2829b20187b70e9'


def test_cache_update(testdata_dir, datadir):
    cache = ParsedConfigCache(datadir)

    shutil.copytree(testdata_dir / 'yaml_configs', datadir / 'configs')

    # populate cache
    config = YamlConfig.from_path(datadir / 'configs', cache)

    # modify config
    with open(datadir / 'configs' / '1.yaml', 'a') as fd:
        print('- { "foo": 11 }', file=fd)

    config = YamlConfig.from_path(datadir / 'configs', cache)

    assert config.get_items() == [
        {'foo': 1},
        {'foo': 11},
        {'bar': 2},
        {'baz': 3},
    ]

    assert config.get_hash() == '0c86170147f75217684bc52ed5f87085460a7fe4b2af901d7a9569772139594c'
