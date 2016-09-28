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
import subprocess

class FileFetcher():
    def __init__(self, *sources, gunzip = False, bunzip = False):
        self.sources = sources
        self.gunzip = gunzip
        self.bunzip = bunzip

    def Fetch(self, statepath, update = True, verbose = False):
        if os.path.isfile(statepath) and not update:
            return

        if os.path.isfile(statepath):
            os.remove(statepath)

        quietflag = 'q' if not verbose else ''

        for source in self.sources:
            if self.gunzip:
                subprocess.check_call("wget -%sO- %s | gunzip >> %s" % (quietflag, source, statepath), shell = True)
            elif self.bunzip:
                subprocess.check_call("wget -%sO- %s | bunzip2 >> %s" % (quietflag, source, statepath), shell = True)
            else:
                subprocess.check_call("wget -%sO- %s >> %s" % (quietflag, source, statepath), shell = True)
