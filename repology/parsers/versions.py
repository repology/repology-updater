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
from typing import Any, Callable

from libversion import version_compare

from repology.package import PackageFlags


__all__ = ['VersionStripper', 'parse_rpm_version', 'parse_debian_version']


class VersionStripper:
    _strips: list[Callable[[str], str]]

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


# allows alpha1, alpha20210101, alpha.1, but not alpha.20210101 (which is parsed as alpha instead)
_RPM_PRERELEASE_RE = re.compile('(.*?)((?:alpha|beta|rc)(?:[0-9]+|\\.[0-9]{1,2}(?![0-9]))?)(.*)', re.IGNORECASE)
_RPM_PRERELEASE_FALLBACK_RE = re.compile('(.*?)((?:dev|pre)(?:[0-9]+|\\.[0-9]{1,2}(?![0-9]))?)(.*)', re.IGNORECASE)
_RPM_POSTRELEASE_RE = re.compile('(.*?)((?:post)[0-9]+)(.*)', re.IGNORECASE)
_RPM_SNAPSHOT = re.compile('[a-z]|20[0-9]{6}', re.IGNORECASE)


def parse_rpm_vertags(vertags: Any) -> list[str]:
    if isinstance(vertags, list):
        return vertags
    elif isinstance(vertags, str):
        return [vertags]
    elif vertags is None:
        return []
    else:
        raise RuntimeError('bad vertags format: {vertags}')


def parse_rpm_version(vertags: list[str], version: str, release: str) -> tuple[str, int]:
    flags = 0
    cleaned_up_release = ''

    for part in re.split('|'.join(vertags), release) if vertags else [release]:
        if (match := _RPM_PRERELEASE_RE.fullmatch(part)) is not None:
            flags = PackageFlags.DEVEL
        elif (match := _RPM_PRERELEASE_FALLBACK_RE.fullmatch(part)) is not None:
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


_DEBIAN_SPLIT_RE = re.compile('(?=[+~-]+)')
_DEBIAN_GARBAGE = 'dfsg|nmu|repack|ds|debian|mx|pristine|stable|ubuntu'
_DEBIAN_GARBAGE_PART_RE = re.compile('[+~-]+(?:' + _DEBIAN_GARBAGE + ')[.0-9]*', re.IGNORECASE)
_DEBIAN_EMBEDDED_GARBAGE_RE = re.compile('(?:' + _DEBIAN_GARBAGE + '|is|real)')
_DEBIAN_GOOD_PRERELEASE_LONG_PART_RE = re.compile('[+~-]+(?:alpha|beta|rc|dev|pre[a-z]*)[.0-9]*', re.IGNORECASE)
_DEBIAN_GOOD_PRERELEASE_SHORT_PART_RE = re.compile('~[ab][0-9]{0,2}', re.IGNORECASE)
_DEBIAN_GOOD_POSTRELEASE_PART_RE = re.compile('[+-]+(post[a-z]*)[.0-9]*', re.IGNORECASE)
_DEBIAN_ALPHA_RE = re.compile('[a-zA-Z]')
_DEBIAN_POST_ALPHA_RE = re.compile('[+][a-zA-Z]')


def parse_debian_version(version: str) -> tuple[str, int]:
    # Epoch and revision
    version = version.split(':', 1)[-1]
    version = version.rsplit('-', 1)[0]

    flags = 0

    # Process parts
    parts = _DEBIAN_SPLIT_RE.split(version)
    version = parts[0]
    alpha_parts_count = 0

    for part in parts[1:]:
        if _DEBIAN_GARBAGE_PART_RE.fullmatch(part) is not None:
            # Garbage parts which have nothing to do with upstream
            # version, such as `+dfsg1`. Drop these.
            continue

        # Count parts which contain letters
        this_alpha_part_pos = None
        if _DEBIAN_ALPHA_RE.search(part) is not None:
            this_alpha_part_pos = alpha_parts_count
            alpha_parts_count += 1

        # Allowed meaningful prerelease parts, such as `~beta2`
        if _DEBIAN_GOOD_PRERELEASE_LONG_PART_RE.fullmatch(part) is not None:
            flags |= PackageFlags.DEVEL
            version += part
            continue

        # Allowed meaningful prerelease short parts, such as `~b2`
        if _DEBIAN_GOOD_PRERELEASE_SHORT_PART_RE.fullmatch(part) is not None:
            flags |= PackageFlags.DEVEL
            version += part
            continue

        # Allowed meaningful postrelease parts, such as `-patch1`
        if _DEBIAN_GOOD_POSTRELEASE_PART_RE.fullmatch(part) is not None:
            version += part
            continue

        # Pre-snapshots. Marked incorrect as the "future" version they
        # are based on is made up, with the exception of when it's equal
        # to 0 which indicates that upstream has no official releases
        if part.startswith('~'):
            flags |= PackageFlags.IGNORE if version_compare(parts[0], '0') == 0 else PackageFlags.INCORRECT
            version += part
            continue

        #
        # The remaining cases are (assumed) post-snapshots
        #

        # Special handling for post- suffixes which start with letter,
        # such as `1.1+git20210203`. These are marked ANY_IS_PATCH to
        # compare greater than e.g. `1.1`, respecting intended `+`
        # behavior. Unfortunately, we can only handle first such suffix
        if this_alpha_part_pos == 0 and _DEBIAN_POST_ALPHA_RE.match(part) is not None:
            flags |= PackageFlags.ANY_IS_PATCH

        flags |= PackageFlags.IGNORE
        version += part

    if _DEBIAN_EMBEDDED_GARBAGE_RE.search(version) is not None:
        # Remaining garbage bits which cannot be separated from upstream
        # version. Always incorrect.
        flags |= PackageFlags.INCORRECT

    return version, flags
