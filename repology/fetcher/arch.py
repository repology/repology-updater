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
import shutil

from repology.logger import NoopLogger
from repology.subprocess import RunSubprocess


class ArchDBFetcher():
    def __init__(self, *sources):
        self.sources = sources

    def DoFetch(self, statepath, update, logger):
        for source in self.sources:
            command = "wget -O- \"%s\" | tar -xz -f- -C \"%s\"" % (source, statepath)
            RunSubprocess(command, logger, shell=True)

    def Fetch(self, statepath, update=True, logger=NoopLogger()):
        if os.path.isdir(statepath) and not update:
            return

        if os.path.exists(statepath):
            shutil.rmtree(statepath)

        os.mkdir(statepath)

        try:
            self.DoFetch(statepath, update, logger)
        except:
            if os.path.exists(statepath):
                shutil.rmtree(statepath)
            raise
