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

from dataclasses import dataclass
from typing import ClassVar, Dict, Optional, Tuple


__all__ = ['NameType', 'NameMapper']


class NameType:
    GENERIC_PKGNAME: ClassVar[int] = 10

    WIKIDATA_ENTITY: ClassVar[int] = 20
    WIKIDATA_LABEL: ClassVar[int] = 21
    WIKIDATA_REPOLOGY_PROJECT_NAME: ClassVar[int] = 22

    BSD_PKGNAME: ClassVar[int] = 30
    BSD_ORIGIN: ClassVar[int] = 31


@dataclass
class _NameMapping:
    visiblename: int
    projectname_seed: int

    name: Optional[int] = None
    basename: Optional[int] = None
    keyname: Optional[int] = None


@dataclass
class MappedNames:
    name: Optional[str] = None
    basename: Optional[str] = None
    keyname: Optional[str] = None
    visiblename: Optional[str] = None
    projectname_seed: Optional[str] = None


_MAPPINGS = [
    # Generic
    _NameMapping(
        name=NameType.GENERIC_PKGNAME,
        visiblename=NameType.GENERIC_PKGNAME,
        projectname_seed=NameType.GENERIC_PKGNAME,
    ),
    # Wikidata
    _NameMapping(
        keyname=NameType.WIKIDATA_ENTITY,
        visiblename=NameType.WIKIDATA_LABEL,
        projectname_seed=NameType.WIKIDATA_REPOLOGY_PROJECT_NAME,
    ),
    # *BSD
    _NameMapping(
        name=NameType.BSD_PKGNAME,
        keyname=NameType.BSD_ORIGIN,
        visiblename=NameType.BSD_ORIGIN,
        projectname_seed=NameType.BSD_PKGNAME,
    ),
]


class NameMapper:
    _names: Dict[int, str]
    _mappings: ClassVar[Dict[Tuple[int, ...], _NameMapping]] = {
        tuple(sorted(set(filter(None, mapping.__dict__.values())))): mapping
        for mapping in _MAPPINGS
    }

    def __init__(self) -> None:
        self._names = {}

    def add_name(self, name: str, name_type: int) -> None:
        self._names[name_type] = name

    def get_mapped_names(self) -> MappedNames:
        keys = tuple(sorted(self._names.keys()))

        mapping = NameMapper._mappings.get(keys)

        if mapping is None:
            raise RuntimeError('no mapping for names combination {}'.format(keys))

        mapped = MappedNames()

        for out_name, in_name in mapping.__dict__.items():
            if in_name is not None:
                setattr(mapped, out_name, self._names[in_name])

        return mapped

    def describe(self) -> Optional[str]:
        if not self._names:
            return None
        return '|'.join(v for _, v in sorted(self._names.items()))
