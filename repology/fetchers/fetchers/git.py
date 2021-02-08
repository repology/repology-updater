# Copyright (C) 2016-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import List, Optional

from repology.fetchers import PersistentDirFetcher
from repology.logger import Logger
from repology.subprocess import Runner


class GitFetcher(PersistentDirFetcher):
    _url: str
    _branch: str
    _sparse_checkout: Optional[List[str]]
    _timeout_arg: str
    _depth_arg: Optional[str]

    def __init__(self, url: str, branch: str = 'master', sparse_checkout: Optional[List[str]] = None, fetch_timeout: int = 600, depth: Optional[int] = 1) -> None:
        self._url = url
        self._branch = branch
        self._sparse_checkout = sparse_checkout
        self._timeout_arg = str(fetch_timeout)
        self._depth_arg = None if depth is None else f'--depth={depth}'

    def _setup_sparse_checkout(self, statepath: str) -> None:
        sparse_checkout_path = os.path.join(statepath, '.git', 'info', 'sparse-checkout')

        # We always enable sparse checkout, as it's harder to
        # properly disable sparse checkout and restore all files
        # than to leave it enabled with all files whitelisted
        #
        # See https://stackoverflow.com/questions/36190800/how-to-disable-sparse-checkout-after-enabled/36195275
        with open(sparse_checkout_path, 'w') as sparse_checkout_file:
            if self._sparse_checkout:
                for item in self._sparse_checkout:
                    print(item, file=sparse_checkout_file)
            else:
                print('/*', file=sparse_checkout_file)
            sparse_checkout_file.flush()
            os.fsync(sparse_checkout_file.fileno())

    def _do_fetch(self, statepath: str, logger: Logger) -> bool:
        Runner(logger=logger).run(
            'timeout', self._timeout_arg,
            'git', 'clone', '--progress', '--no-checkout',
            self._depth_arg,
            '--branch', self._branch,
            self._url,
            statepath
        )

        r = Runner(logger=logger, cwd=statepath)

        r.run('git', 'config', 'core.sparsecheckout', 'true')
        self._setup_sparse_checkout(statepath)
        r.run('git', 'checkout')

        return True

    def _do_update(self, statepath: str, logger: Logger) -> bool:
        r = Runner(logger=logger, cwd=statepath)

        old_head = r.get('git', 'rev-parse', 'HEAD').strip()

        r.run('timeout', self._timeout_arg, 'git', 'fetch', '--progress', self._depth_arg)
        r.run('git', 'checkout')  # needed for reset to not fail on changed sparse checkout
        self._setup_sparse_checkout(statepath)
        r.run('git', 'reset', '--hard', f'origin/{self._branch}')
        r.run('git', 'reflog', 'expire', '--expire=0', '--all')
        r.run('git', 'prune')

        new_head = r.get('git', 'rev-parse', 'HEAD').strip()

        if new_head == old_head:
            logger.log('HEAD has not changed: {}'.format(new_head))
            return False

        logger.log('HEAD was updated from {} to {}'.format(old_head, new_head))
        return True
