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

from repology.package import Package

__all__ = ['PackageFormatter']


class PackageFormatter(string.Formatter):
    filters = {
        'lowercase': lambda x: x.lower(),
        'firstletter': lambda x: x.lower()[0],
        'libfirstletter': lambda x: x.lower()[:4] if x.lower().startswith('lib') else x.lower()[0]
    }

    def get_value(self, key, args, kwargs):
        pkgdata = args[0].__dict__ if isinstance(args[0], Package) else args[0]
        key, *requested_filters = key.split('|')

        value = ''

        if key == 'name':
            value = pkgdata['name']
        elif key == 'subrepo':
            value = pkgdata['subrepo']
        elif key == 'version':
            value = pkgdata['version']
        elif key == 'origversion':
            value = pkgdata['origversion'] if pkgdata['origversion'] is not None else pkgdata['version']
        elif key == 'category':
            value = pkgdata['category'] if pkgdata['category'] is not None else ''
        elif key == 'archrepo':
            value = 'community' if pkgdata['subrepo'].startswith('community') else 'packages'
        elif key == 'archbase':
            value = pkgdata['extrafields']['base'] if 'base' in pkgdata['extrafields'] else pkgdata['name']
        elif key in pkgdata['extrafields']:
            value = pkgdata['extrafields'][key]

        for filtername in requested_filters:
            if filtername in self.filters:
                value = self.filters[filtername](value)

        # XXX: we should handle errors here, e.g. unknown fields and unknown filters
        # but that way bebsite users will get errors first. Need some kind of log facility
        # instead

        return value
