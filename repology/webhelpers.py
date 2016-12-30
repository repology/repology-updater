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
