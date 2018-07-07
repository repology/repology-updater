# Copyright (C) 2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.fetchers import PersistentDirFetcher
from repology.subprocess import RunSubprocess


class RsyncFetcher(PersistentDirFetcher):
    def __init__(self, url, fetch_timeout=60):
        self.url = url
        self.fetch_timeout = fetch_timeout

    def do_fetch(self, statedir, logger):
        command = ['rsync', '--verbose', '--archive', '--compress', '--delete', '--delete-excluded', '--timeout', str(self.fetch_timeout), self.url, statedir]
        RunSubprocess(command, logger)

    def do_update(self, statedir, logger):
        self.do_fetch(statedir, logger)
