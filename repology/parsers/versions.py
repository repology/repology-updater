# Copyright (C) 2018-2019,2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Any, Callable, List, Tuple

from repology.package import PackageFlags


__all__ = ['VersionStripper', 'parse_rpm_version']


class VersionStripper:
    _strips: List[Callable[[str], str]]

    def __init__(self) -> None:
        self._strips = []

    def strip_left(self, separator: str) -> 'VersionStripper':
        self._strips.append(lambda s: s.split(separator, 1)[-1])
        return self

    def strip_left_greedy(self, separator: str) -> 'VersionStripper':
        self._strips.append(lambda s: s.rsplit(separator, 1)[-1])
        return self

    def strip_right(self, separator: str) -> 'VersionStripper':
        self._strips.append(lambda s: s.rsplit(separator, 1)[0])
        return self

    def strip_right_greedy(self, separator: str) -> 'VersionStripper':
        self._strips.append(lambda s: s.split(separator, 1)[0])
        return self

    def __call__(self, version: str) -> str:
        for strip in self._strips:
            version = strip(version)
        return version


_RPM_PRERELEASE_RE = re.compile('(.*)((?:alpha|beta|rc|dev|pre)[0-9]+)(.*)', re.IGNORECASE)
_RPM_POSTRELEASE_RE = re.compile('(.*)((?:post)[0-9]+)(.*)', re.IGNORECASE)
_RPM_SNAPSHOT = re.compile('[a-z]|20[0-9]{6}', re.IGNORECASE)


def parse_rpm_vertags(vertags: Any) -> List[str]:
    if isinstance(vertags, list):
        return vertags
    elif isinstance(vertags, str):
        return [vertags]
    elif vertags is None:
        return []
    else:
        raise RuntimeError('bad vertags format: {vertags}')


def parse_rpm_version(vertags: List[str], version: str, release: str) -> Tuple[str, int]:
    flags = 0
    cleaned_up_release = ''

    for part in re.split('|'.join(vertags), release) if vertags else [release]:
        if (match := _RPM_PRERELEASE_RE.fullmatch(part)) is not None:
            flags = PackageFlags.DEVEL
        else:
            match = _RPM_POSTRELEASE_RE.fullmatch(part)

        # legal prerelease or postrelease match
        if match is not None:
            version += '-' + match[2]

            if match[1] and match[3]:
                part = f'{match[1]}.{match[3]}'
            else:
                part = f'{match[1]}{match[3]}'

        cleaned_up_release += part

    if (cleaned_up_release == '0' or cleaned_up_release.startswith('0.')) and not flags & PackageFlags.DEVEL:
        flags |= PackageFlags.IGNORE

    if match := _RPM_SNAPSHOT.search(cleaned_up_release):
        flags |= PackageFlags.IGNORE

    return version, flags
