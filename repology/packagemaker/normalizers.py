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


def require_url(value):
    if not re.match('(ftp|https?|mirror|git|svn|hg|bzr|cvs)://', value):
        return None, 'does not look like an URL'
    return value, None


def strip(value):
    return value.strip(), None


def warn_whitespace(value):
    if ' ' in value or '\t' in value:
        return value, 'contains whitespace'
    return value, None


def forbid_newlines(value):
    if '\n' in value:
        return None, 'contains newlines'
    else:
        return value, None
