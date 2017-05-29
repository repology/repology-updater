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

from repology.logger import NoopLogger
from repology.version import VersionCompare
from repology.www import Get


class FreshcodeFetcher():
    def __init__(self, url):
        self.url = url

    def Fetch(self, statepath, update=True, logger=NoopLogger()):
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

        newdata = json.loads(Get(self.url).text)

        # add new entries in reversed order, oldest first so newest
        # have higher priority; may also compare versions here
        for entry in newdata['releases']:
            if 'name' not in entry:
                logger.Log('skipping entry with no name')
                continue

            if entry['name'] in state:
                oldentry = state[entry['name']]

                if VersionCompare(entry['version'], oldentry['version']) > 0:
                    logger.Log('replacing entry "{}", version changed {} -> {}'.format(entry['name'], oldentry['version'], entry['version']))
                    state[entry['name']] = entry
            else:
                logger.Log('adding entry "{}", version {}'.format(entry['name'], entry['version']))
                state[entry['name']] = entry

        temppath = statepath + '.tmp'
        with open(temppath, 'w', encoding='utf-8') as newstatefile:
            json.dump(state, newstatefile)

        os.replace(temppath, statepath)

        logger.Log('saved new state, {} entries'.format(len(state)))
