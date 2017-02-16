# Copyright (C) 2017 Steve Wills <steve@mouf.net>
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

import rubymarshal.reader

from repology.package import Package


class RubyGemParser():
    def __init__(self):
        pass

    def force_decode(self, var):
        if type(var) is not str:
            return str(var, 'UTF-8')
        else:
            return var

    def Parse(self, path):
        packages = {}

        with open(path, 'rb') as fd:
            content = rubymarshal.reader.load(fd)
            for gem in content:
                pkg = Package()
                gemplat = self.force_decode(gem[2])
                if gemplat == 'ruby':
                    pkg.name = self.force_decode(gem[0])
                    pkg.version = self.force_decode(gem[1].values[0])
                    pkg.homepage = 'https://rubygems.org/gems/' + pkg.name
                    packages[pkg.name] = pkg

        return [package for package in packages.values()]
