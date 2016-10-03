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

class GitFetcher():
    def __init__(self, repository):
        self.repository = repository

    def Fetch(self, statepath, update = True, logger = NoopLogger()):
        if not os.path.isdir(statepath):
            RunSubprocess(["git", "clone", "--progress", "--depth=1", self.repository, statepath], logger = logger)
        elif update:
            RunSubprocess(["git", "fetch", "--progress"], cwd = statepath, logger = logger)
            RunSubprocess(["git", "reset", "--hard", "origin/master"], cwd = statepath, logger = logger)
