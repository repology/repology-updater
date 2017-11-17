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


__all__ = ['PackageFormatter']


class PackageFormatter(string.Formatter):
    filters = {
        'lowercase': lambda x: x.lower(),
        'firstletter': lambda x: x.lower()[0],
        'libfirstletter': lambda x: x.lower()[:4] if x.lower().startswith('lib') else x.lower()[0]
    }

    def get_value(self, key, args, kwargs):
        pkg = args[0]

        key, *requested_filters = key.split('|')

        value = ''

        if key == 'name':
            value = pkg.name
        elif key == 'subrepo':
            value = pkg.subrepo
        elif key == 'version':
            value = pkg.version
        elif key == 'origversion':
            value = pkg.origversion if pkg.origversion is not None else pkg.version
        elif key == 'category':
            value = pkg.category if pkg.category is not None else ''
        elif key == 'archrepo':
            value = 'community' if pkg.subrepo.startswith('community') else 'packages'
        elif key == 'archbase':
            value = pkg.extrafields['base'] if 'base' in pkg.extrafields else pkg.name
        elif key in pkg.extrafields:
            value = pkg.extrafields[key]

        for filtername in requested_filters:
            if filtername in self.filters:
                value = self.filters[filtername](value)

        # XXX: we should handle errors here, e.g. unknown fields and unknown filters
        # but that way bebsite users will get errors first. Need some kind of log facility
        # instead

        return value
