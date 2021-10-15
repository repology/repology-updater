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

import hashlib
import os
import pickle
from typing import Any, cast

import yaml


__all__ = ['ParsedConfigCache', 'YamlConfig']


ConfigItems = list[Any]


class ParsedConfigCache:
    _path: str

    def __init__(self, path: str) -> None:
        self._path = path
        if not os.path.exists(self._path):
            os.makedirs(self._path)

    def _get_cache_path(self, path: str) -> str:
        return os.path.join(self._path, path.replace('/', '_').replace('.', '_'))

    def get(self, path: str, hash_: str) -> ConfigItems | None:
        cache_path = self._get_cache_path(path)
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as fd:
                stored_hash, stored_items = pickle.load(fd)
                if stored_hash == hash_:
                    return cast(ConfigItems, stored_items)

        return None

    def store(self, path: str, hash_: str, items: ConfigItems) -> None:
        cache_path = self._get_cache_path(path)
        with open(cache_path, 'wb') as fd:
            pickle.dump((hash_, items), fd)
            fd.flush()
            os.fsync(fd.fileno())


class YamlConfig:
    _items: ConfigItems
    _hash: str

    def __init__(self, items: ConfigItems, hash_: str) -> None:
        self._items = items
        self._hash = hash_

    @staticmethod
    def from_text(text: str) -> 'YamlConfig':
        texthash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        return YamlConfig(yaml.safe_load(text), texthash)

    @staticmethod
    def from_path(path: str, cache: ParsedConfigCache | None = None) -> 'YamlConfig':
        items: list[Any] = []

        file_paths: list[str] = []

        overall_hash = hashlib.sha256()

        for root, dirs, files in os.walk(path):
            file_paths += [os.path.join(root, f) for f in files if f.endswith('.yaml')]
            dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file_path in sorted(file_paths):
            with open(file_path, 'rb') as fd:
                data = fd.read()
                file_hash = hashlib.sha256(data).hexdigest()

                if cache is not None and (cached := cache.get(file_path, file_hash)) is not None:
                    items.extend(cached)
                elif (parsed := yaml.safe_load(data.decode('utf-8'))):
                    if cache is not None:
                        cache.store(file_path, file_hash, parsed)
                    items.extend(parsed)

                overall_hash.update(file_hash.encode('utf-8'))

        return YamlConfig(items, overall_hash.hexdigest())

    def dump(self) -> str:
        return cast(str, yaml.safe_dump(self._items, default_flow_style=False, sort_keys=False))

    def get_items(self) -> list[Any]:
        return self._items

    def get_hash(self) -> str:
        return self._hash
