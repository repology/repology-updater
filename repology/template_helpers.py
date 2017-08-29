# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import datetime

import flask

from repology.package import PackageVersionClass, RepositoryVersionClass
from repology.packageformatter import PackageFormatter


def maintainer_to_links(maintainer):
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


def is_fallback_maintainer(maintainer):
    return maintainer.startswith('fallback-mnt-') and maintainer.endswith('@repology')


def maintainers_to_group_mailto(maintainers, subject=None):
    emails = []

    for maintainer in maintainers:
        if '@' in maintainer and '.' in maintainer.split('@', 1)[1]:
            emails.append(maintainer)

    if not emails:
        return None

    return 'mailto:' + ','.join(sorted(emails)) + ('?subject=' + subject if subject else '')


def for_page(value, letter=None):
    if letter is None or letter == '0':
        return not value or value < 'a'
    elif letter >= 'z':
        return value and value >= 'z'
    else:
        return value and value >= letter and value < chr(ord(letter) + 1)


def pkg_format(value, pkg):
    return PackageFormatter().format(value, pkg)


def css_for_package_versionclass(value):
    if value == PackageVersionClass.newest:
        return 'newest'
    elif value == PackageVersionClass.outdated:
        return 'outdated'
    elif value == PackageVersionClass.ignored:
        return 'ignored'


def css_for_summary_versionclass(value):
    if value == RepositoryVersionClass.newest:
        return 'newest'
    elif value == RepositoryVersionClass.outdated:
        return 'outdated'
    elif value == RepositoryVersionClass.mixed:
        return 'mixed'
    elif value == RepositoryVersionClass.ignored:
        return 'ignored'
    elif value == RepositoryVersionClass.lonely:
        return 'unique'


def url_for_self(**args):
    return flask.url_for(flask.request.endpoint, **dict(flask.request.view_args, **args))


class AFKChecker:
    def __init__(self, intervals=[]):
        self.intervals = []
        for interval in intervals:
            start, *rest = [
                datetime.date(*map(int, date.split('-', 2)))
                for date in interval.split(' ', 1)
            ]

            self.intervals.append((start, rest[0] if rest else start))

    def GetAFKEnd(self, today=None):
        if today is None:
            today = datetime.date.today()

        for interval in self.intervals:
            if today >= interval[0] and today <= interval[1]:
                return interval[1]

        return None
