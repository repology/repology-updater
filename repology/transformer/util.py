# Copyright (C) 2018-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import re
from typing import Any


__all__ = ['DOLLAR0', 'DOLLARN', 'yaml_as_list', 'yaml_as_lowercase_list', 'yaml_as_set', 'yaml_as_lowercase_set']


DOLLAR0 = re.compile('\\$0', re.ASCII)
DOLLARN = re.compile('\\$([0-9])', re.ASCII)


def yaml_as_list(val: Any) -> list[str]:
    if isinstance(val, list):
        return val
    elif isinstance(val, set):
        return list(val)
    else:
        return [val]


def yaml_as_lowercase_list(val: Any) -> list[str]:
    return [v.lower() for v in yaml_as_list(val)]


def yaml_as_set(val: Any) -> set[str]:
    return set(yaml_as_list(val))


def yaml_as_lowercase_set(val: Any) -> set[str]:
    return set(yaml_as_lowercase_list(val))
