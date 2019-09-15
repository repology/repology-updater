# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Iterable, List, Optional

from repologyapp.package import PackageDataDetailed, PackageStatus
from repologyapp.packageformatter import PackageFormatter


__all__ = ['maintainer_to_links', 'maintainers_to_group_mailto', 'pkg_format', 'css_for_versionclass']


def maintainer_to_links(maintainer: str) -> List[str]:
    links = []

    if '@' in maintainer:
        name, domain = maintainer.split('@', 1)

        if domain == 'cpan':
            links.append('http://search.cpan.org/~' + name)
        elif domain == 'aur':
            links.append('https://aur.archlinux.org/account/' + name)
        elif domain in ('altlinux.org', 'altlinux.ru'):
            links.append('http://sisyphus.ru/en/packager/' + name + '/')
        elif domain == 'github':
            links.append('https://github.com/' + name)
        elif domain == 'freshcode':
            links.append('http://freshcode.club/search?user=' + name)

        if '.' in domain:
            links.append('mailto:' + maintainer)

    return links


def maintainers_to_group_mailto(maintainers: Iterable[str], subject: Optional[str] = None) -> Optional[str]:
    emails = []

    for maintainer in maintainers:
        if '@' in maintainer and '.' in maintainer.split('@', 1)[1]:
            emails.append(maintainer)

    if not emails:
        return None

    return 'mailto:' + ','.join(sorted(emails)) + ('?subject=' + subject if subject else '')


def pkg_format(value: str, pkg: PackageDataDetailed, escape_mode: Optional[str] = None) -> str:
    return PackageFormatter(escape_mode=escape_mode).format(value, pkg, escape_mode=escape_mode)


def css_for_versionclass(value: int) -> str:
    if value == PackageStatus.IGNORED:
        return 'ignored'
    elif value == PackageStatus.UNIQUE:
        return 'unique'
    elif value == PackageStatus.DEVEL:
        return 'devel'
    elif value == PackageStatus.NEWEST:
        return 'newest'
    elif value == PackageStatus.LEGACY:
        return 'legacy'
    elif value == PackageStatus.OUTDATED:
        return 'outdated'
    elif value == PackageStatus.INCORRECT:
        return 'incorrect'
    elif value == PackageStatus.UNTRUSTED:
        return 'untrusted'
    elif value == PackageStatus.NOSCHEME:
        return 'noscheme'
    elif value == PackageStatus.ROLLING:
        return 'rolling'
    else:
        raise RuntimeError('unknown versionclass {}'.format(value))
