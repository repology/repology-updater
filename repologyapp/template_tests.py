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


__all__ = ['is_fallback_maintainer', 'for_page']


def is_fallback_maintainer(maintainer):
    return maintainer.startswith('fallback-mnt-') and maintainer.endswith('@repology')


def for_page(value, letter=None):
    if letter is None or letter == '0':
        return not value or value < 'a'
    elif letter >= 'z':
        return value and value >= 'z'
    else:
        return value and value >= letter and value < chr(ord(letter) + 1)
