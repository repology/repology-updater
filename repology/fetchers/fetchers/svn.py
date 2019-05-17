# Copyright (C) 2018-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from repology.logger import Logger
from repology.subprocess import get_subprocess_output, run_subprocess


class SVNFetcher(PersistentDirFetcher):
    def __init__(self, url: str, fetch_timeout: int = 600) -> None:
        self.url = url
        self.fetch_timeout = fetch_timeout

    def _do_fetch(self, statepath: str, logger: Logger) -> bool:
        run_subprocess(['timeout', str(self.fetch_timeout), 'svn', 'checkout', self.url, statepath], logger=logger)

        return True

    def _do_update(self, statepath: str, logger: Logger) -> bool:
        old_rev = get_subprocess_output(['svn', 'info', '--show-item', 'revision', statepath], logger=logger).strip()

        run_subprocess(['timeout', str(self.fetch_timeout), 'svn', 'up', statepath], logger=logger)

        new_rev = get_subprocess_output(['svn', 'info', '--show-item', 'revision', statepath], logger=logger).strip()

        if new_rev == old_rev:
            logger.log('Revision has not changed: {}'.format(new_rev))
            return False

        logger.log('Revision was updated from {} to {}'.format(old_rev, new_rev))
        return True
