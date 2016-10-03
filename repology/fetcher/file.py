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

import os

from repology.logger import NoopLogger
from repology.subprocess import RunSubprocess

class FileFetcher():
    def __init__(self, *sources, gunzip = False, bunzip = False):
        self.sources = sources
        self.gunzip = gunzip
        self.bunzip = bunzip

    def Fetch(self, statepath, update = True, logger = NoopLogger()):
        if os.path.isfile(statepath) and not update:
            return

        if os.path.isfile(statepath):
            os.remove(statepath)

        for source in self.sources:
            command = None
            if self.gunzip:
                command = "wget -O- \"%s\" | gunzip >> \"%s\"" % (source, statepath)
            elif self.bunzip:
                command = "wget -O- \"%s\" | bunzip2 >> \"%s\"" % (source, statepath)
            else:
                command = "wget -O- \"%s\" >> \"%s\"" % (source, statepath)

            RunSubprocess(command, logger, shell = True)
