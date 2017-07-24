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

import string


class PackageFormatter(string.Formatter):
    def get_value(self, key, args, kwargs):
        pkg = args[0]
        if key == 'name':
            return pkg.name
        elif key == 'subrepo':
            return pkg.subrepo
        elif key == 'version':
            return pkg.version
        elif key == 'origversion':
            return pkg.origversion if pkg.origversion is not None else pkg.version
        elif key == 'category':
            return pkg.category if pkg.category is not None else ''
        elif key in pkg.extrafields:
            return pkg.extrafields[key]
        return ''
