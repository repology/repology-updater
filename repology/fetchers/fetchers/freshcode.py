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

import json
import os

from libversion import version_compare

from repology.fetchers import Fetcher
from repology.fetchers.fetch import fetch
from repology.fetchers.state import state_file
from repology.logger import NoopLogger


class FreshcodeFetcher(Fetcher):
    def __init__(self, url):
        self.url = url

    def fetch(self, statepath, update=True, logger=NoopLogger()):
        if os.path.isfile(statepath) and not update:
            logger.Log('no update requested, skipping')
            return

        state = {}

        if os.path.isfile(statepath):
            with open(statepath, 'r', encoding='utf-8') as oldstatefile:
                state = json.load(oldstatefile)
            logger.Log('loaded old state, {} entries'.format(len(state)))
        else:
            logger.Log('starting with empty state')

        newdata = json.loads(fetch(self.url).text)

        if not newdata['releases']:
            raise RuntimeError('Empty freshcode package list received, refusing to go on')

        # add new entries in reversed order, oldest first so newest
        # have higher priority; may also compare versions here
        for entry in newdata['releases']:
            if 'name' not in entry:
                logger.Log('skipping entry with no name')
                continue

            if entry['name'] in state:
                oldentry = state[entry['name']]

                if version_compare(entry['version'], oldentry['version']) > 0:
                    logger.Log('replacing entry "{}", version changed {} -> {}'.format(entry['name'], oldentry['version'], entry['version']))
                    state[entry['name']] = entry
            else:
                logger.Log('adding entry "{}", version {}'.format(entry['name'], entry['version']))
                state[entry['name']] = entry

        with state_file(statepath, 'w', encoding='utf-8') as statefile:
            json.dump(state, statefile)

        logger.Log('saved new state, {} entries'.format(len(state)))
