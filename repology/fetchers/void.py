# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
# Copyright (C) 2017 Felix Van der Jeugt <felix.vanderjeugt@gmail.com>
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
import urllib

from repology.fetchers.git import GitFetcher
from repology.fetchers.helpers.fetch import Fetch
from repology.fetchers.helpers.state import StateDir
from repology.logger import NoopLogger
from repology.subprocess import RunSubprocess


class VoidFetcher(GitFetcher):
    def __init__(self, url, giturl=None, arches=[]):
        super().__init__(giturl)
        self.dataurl = url
        self.arches = arches

    def Fetch(self, statepath, update=True, logger=NoopLogger()):
        if os.path.isdir(statepath) and not update:
            return

        with StateDir(statepath) as statedir:
            super().Fetch(os.path.join(statedir, 'repo'), update, logger)

            archdir = os.path.join(statedir, 'arches')
            os.mkdir(archdir)
            tarpath = os.path.join(statedir, '.temporary.tar')
            for arch in self.arches:
                with open(tarpath, 'wb') as tarfile:
                    tarfile.write(Fetch(self.dataurl + arch + '-repodata', timeout=5).content)
                RunSubprocess(['tar', 'xzfC', tarpath, statedir, 'index.plist'], logger)
                os.rename(os.path.join(statedir, 'index.plist'),
                          os.path.join(archdir, arch.replace('/', ' ')))
                os.remove(tarpath)
