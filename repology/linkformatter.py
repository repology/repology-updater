# Copyright (C) 2016-2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import urllib.parse
from itertools import product
from typing import Any, Callable, Iterator

from repology.package import Package

__all__ = ['format_package_links']


_FILTERS: dict[str, Callable[[str], str]] = {
    'lowercase': lambda x: x.lower(),
    'firstletter': lambda x: x.lower()[0],
    'libfirstletter': lambda x: x.lower()[:4] if x.lower().startswith('lib') else x.lower()[0],
    'stripdmo': lambda x: x[:-4] if x.endswith('-dmo') else x,
    'basename': lambda x: x.rsplit('/', 1)[-1],
    'dirname': lambda x: x.rsplit('/', 1)[0],
    'dec': lambda x: str(_safe_int(x) - 1),
    'inc': lambda x: str(_safe_int(x) + 1),
    'quote': lambda x: urllib.parse.quote(x),
    'strip_nevra_epoch': lambda x: x.split(':', 1)[-1],
}


def _safe_int(arg: str) -> int:
    try:
        return int(arg)
    except ValueError:
        return 0


class FieldGatheringMapping:
    _package: Package
    _fields: dict[str, Any]
    _skip: bool

    def __init__(self, package: Package) -> None:
        self._package = package
        self._fields = {}
        self._skip = False

    def __getitem__(self, key: str) -> str:
        field, *filters = key.split('|', 1)

        is_optional = field.startswith('?')
        field = field.removeprefix('?')

        if key in self._fields or self._skip:
            return ''

        value: Any = None

        if field == 'name':
            value = self._package.name
        elif field == 'srcname':
            value = self._package.srcname
        elif field == 'binname':
            value = self._package.binname
        elif field == 'binorsrcname':
            value = self._package.binname or self._package.srcname
        elif field == 'subrepo':
            value = self._package.subrepo
        elif field == 'rawversion':
            value = self._package.rawversion
        elif field == 'category':
            value = self._package.category or ''
        elif field == 'arch':
            value = self._package.arch
        elif field == 'centossuffix':
            value = '-extras' if self._package.subrepo == 'extras' else ''
            is_optional = True
        elif field == 'rpmversion':
            # XXX: convert these to generic NEVRA parsiong code from repology.parsers.nevra
            version, release = self._package.rawversion.rsplit('-', 1)
            if ':' in version:
                epoch, version = version.rsplit(':', 1)
            value = version
        elif field == 'rpmrelease':
            version, release = self._package.rawversion.rsplit('-', 1)
            value = release
        elif self._package.extrafields is not None and field in self._package.extrafields:
            value = self._package.extrafields[field]

        if value is None or value == []:
            if is_optional:
                self._skip = True
            else:
                raise RuntimeError(f'missing key "{field}"')
        elif value == '':
            if not is_optional:
                raise RuntimeError(f'empty key "{field}"')
            self._fields[key] = [value]
        elif isinstance(value, list):
            if filters:
                raise RuntimeError(f'cannot apply filter to list of values in "{field}"')
            self._fields[key] = value
        elif isinstance(value, str):
            for filtername in filters:
                if filtername not in _FILTERS:
                    raise RuntimeError(f'unknown filter "filtername" in "{field}"')
                value = _FILTERS[filtername](value)

            self._fields[key] = [value]
        else:
            if filters:
                raise RuntimeError(f'cannot apply filter to non-string value in "{field}"')
            self._fields[key] = [value]

        return ''

    def generate_mappings(self) -> Iterator[dict[str, Any]]:
        if self._skip:
            return

        keys = list(self._fields.keys())

        for values in product(*self._fields.values()):
            yield dict(zip(keys, values))


def format_package_links(package: Package, link_template: str) -> Iterator[str]:
    field_gatherer = FieldGatheringMapping(package)

    link_template.format_map(field_gatherer)

    for mapping in field_gatherer.generate_mappings():
        yield link_template.format_map(mapping)
