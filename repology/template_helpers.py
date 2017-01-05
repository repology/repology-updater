#!/usr/bin/env python3
#
# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import flask

from repology.packageformatter import PackageFormatter
from repology.package import *


def maintainer_to_link(maintainer):
    if re.match(".*@.*\..*", maintainer):
        return "mailto:" + maintainer
    elif maintainer.endswith("@cpan"):
        return "http://search.cpan.org/~" + maintainer[:-5]
    else:
        return None


def for_page(value, letter=None):
    if letter is None or letter == '0':
        return not value or value < 'a'
    elif letter >= 'z':
        return value and value >= 'z'
    else:
        return value and value >= letter and value < chr(ord(letter) + 1)


def SpanTrim(value, maxlength):
    # support lists as well
    if type(value) is list:
        return [SpanTrim(v, maxlength) for v in value]

    if len(value) <= maxlength:
        return value

    # no point in leaving dot just before ellipsis
    trimmed = value[0:maxlength-2]
    while trimmed.endswith('.'):
        trimmed = trimmed[0:-1]

    # we assume ellipsis take ~2 char width
    return "<span title=\"%s\">%s…</span>" % (value, trimmed)


def pkg_format(value, pkg):
    return PackageFormatter().format(value, pkg)


def PackageVersionClass2CSSClass(value):
    if value == PackageVersionClass.newest:
        return 'good'
    elif value == PackageVersionClass.outdated:
        return 'bad'
    elif value == PackageVersionClass.ignored:
        return 'ignore'


def RepositoryVersionClass2CSSClass(value):
    if value == RepositoryVersionClass.newest:
        return 'good'
    elif value == RepositoryVersionClass.outdated:
        return 'bad'
    elif value == RepositoryVersionClass.mixed:
        return 'multi'
    elif value == RepositoryVersionClass.ignored:
        return 'ignore'
    elif value == RepositoryVersionClass.lonely:
        return 'lonely'


def url_for_self(**args):
    return flask.url_for(flask.request.endpoint, **dict(flask.request.view_args, **args))
