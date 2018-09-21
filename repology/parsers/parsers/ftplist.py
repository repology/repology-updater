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

from repology.parsers import Parser
from repology.parsers.nevra import filename2nevra


class RPMFTPListParser(Parser):
    def iter_parse(self, path, factory):
        with open(path) as listfile:
            for line in listfile:
                filename = line.strip().split()[-1]

                nevra = filename2nevra(filename)

                pkg = factory.begin()

                pkg.set_name(nevra[0])
                pkg.set_version(nevra[2])

                pkg.set_extra_field('nevr', filename.rsplit('.', 2)[0])

                yield pkg
