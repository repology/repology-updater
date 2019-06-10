# Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Any, Dict, Iterable, Tuple, Union

from jsonslicer import JsonSlicer


def iter_json_list(path: str, json_path: Tuple[Union[str, None], ...], **kwargs: Any) -> Iterable[Dict[str, Any]]:
    with open(path, 'rb') as jsonfile:
        yield from JsonSlicer(jsonfile, json_path, **kwargs)


def iter_json_dict(path: str, json_path: Tuple[Union[str, None], ...], **kwargs: Any) -> Iterable[Tuple[str, Dict[str, Any]]]:
    with open(path, 'rb') as jsonfile:
        yield from JsonSlicer(jsonfile, json_path, path_mode='map_keys', **kwargs)
