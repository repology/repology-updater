#!/usr/bin/env python3
#
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

# mypy: no-disallow-untyped-calls

from typing import Any, Dict

from repologyapp.package import Package


def spawn_package(**custom_args: Any) -> Package:
    args: Dict[str, Any] = {
        'repo': 'dummyrepo',
        'family': 'dummyfamily',

        'name': 'dummyname',
        'effname': 'dummyname',

        'version': '0',
        'origversion': '0',
        'rawversion': '0',

        'versionclass': 0,
    }

    args.update(custom_args)

    return Package(**args)
