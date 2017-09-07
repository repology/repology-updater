# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
    def __init__(self, url, branch='master', sparse_checkout=None):
        self.url = url
        self.branch = branch
        self.sparse_checkout = sparse_checkout

    def __SetupSparseCheckout(self, statepath, logger):
        sparse_checkout_path = os.path.join(statepath, '.git', 'info', 'sparse-checkout')

        # We always enable sparse checkout, as it's harder to
        # properly disable sparse checkout and restore all files
        # than to leave it enabled with all files whitelisted
        #
        # See https://stackoverflow.com/questions/36190800/how-to-disable-sparse-checkout-after-enabled/36195275
        RunSubprocess(['git', 'config', 'core.sparsecheckout', 'true'], cwd=statepath, logger=logger)
        with open(sparse_checkout_path, 'w') as sparse_checkout_file:
            if self.sparse_checkout:
                for item in self.sparse_checkout:
                    print(item, file=sparse_checkout_file)
            else:
                print('/*', file=sparse_checkout_file)

    def Fetch(self, statepath, update=True, logger=NoopLogger()):
        if not os.path.isdir(statepath):
            RunSubprocess(['git', 'clone', '--progress', '--no-checkout', '--depth=1', '--branch', self.branch, self.url, statepath], logger=logger)
            self.__SetupSparseCheckout(statepath, logger)
            RunSubprocess(['git', 'checkout'], cwd=statepath, logger=logger)
        elif update:
            RunSubprocess(['timeout', '10m', 'git', 'fetch', '--progress', '--depth=1'], cwd=statepath, logger=logger)
            RunSubprocess(['git', 'checkout'], cwd=statepath, logger=logger)  # needed for reset to not fail on changed sparse checkout
            self.__SetupSparseCheckout(statepath, logger)
            RunSubprocess(['git', 'reset', '--hard', 'origin/' + self.branch], cwd=statepath, logger=logger)
            RunSubprocess(['git', 'reflog', 'expire', '--expire=0', '--all'], cwd=statepath, logger=logger)
            RunSubprocess(['git', 'prune'], cwd=statepath, logger=logger)
        else:
            logger.Log('no update requested, skipping')
