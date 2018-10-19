# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


_supported_schemas = [
    'bzr',
    'cvs',
    'ftp',
    'git',
    'hg',
    'http',
    'https',
    'mirror',
    'svn',
]


def url(value):
    match = re.fullmatch('([a-z][a-z0-9.+-]*)://([^/]+)(/.*)?', value, re.IGNORECASE)
    if not match and '://' not in value:
        return None, 'does not look like an URL (schema missing)'
    elif not match:
        return None, 'does not look like an URL'

    schema = match.group(1).lower()
    hostname = match.group(2).lower()
    path = match.group(3)

    if schema in ['http', 'https'] and not path:
        path = '/'

    if schema not in _supported_schemas:
        return None, 'unsupported URL schema'

    return '{}://{}{}'.format(schema, hostname, path), None


def strip(value):
    return value.strip(), None


def tolower(value):
    return value.lower(), None


def warn_whitespace(value):
    if ' ' in value or '\t' in value:
        return value, 'contains whitespace'
    return value, None


def forbid_newlines(value):
    if '\n' in value:
        return None, 'contains newlines'
    else:
        return value, None
