# Copyright (C) 2017-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.fetchers import Fetcher
from repology.logger import Logger, NoopLogger
from repology.subprocess import run_subprocess


class RsyncFetcher(Fetcher):
    def __init__(self, url: str, fetch_timeout: int = 60, rsync_include: str | None = None, rsync_exclude: str | None = None) -> None:
        self.url = url
        self.fetch_timeout = fetch_timeout
        self.rsync_include = rsync_include
        self.rsync_exclude = rsync_exclude

    def fetch(self, statepath: str, update: bool = True, logger: Logger = NoopLogger()) -> bool:
        if os.path.exists(statepath) and not update:
            logger.log('no update requested, skipping')
            return False

        args = [
            '--info=stats2',
            '--archive',
            '--compress',
            '--delete',
            '--delete-excluded',
            '--safe-links',
        ]

        if self.fetch_timeout is not None:
            args += ['--timeout', str(self.fetch_timeout)]

        if self.rsync_include is not None:
            args += ['--include', self.rsync_include]

        if self.rsync_exclude is not None:
            args += ['--exclude', self.rsync_exclude]

        run_subprocess(['rsync'] + args + [self.url, statepath], logger)

        return True
