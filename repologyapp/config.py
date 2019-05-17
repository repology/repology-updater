# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import os
from typing import Any, Dict

__all__ = ['config']

config: Dict[str, Any] = {}


def _load_config(path: str) -> None:
    with open(path) as f:
        exec(compile(f.read(), path, 'exec'), globals(), config)


def _load_configs() -> None:
    default_config_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'repology.conf.default'))
    custom_config_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'repology.conf'))
    runtime_config_path = os.environ['REPOLOGY_CONFIG'] if 'REPOLOGY_CONFIG' in os.environ else None

    _load_config(default_config_path)
    if os.path.isfile(custom_config_path):
        _load_config(custom_config_path)
    if runtime_config_path and os.path.isfile(runtime_config_path):
        _load_config(runtime_config_path)


_load_configs()
