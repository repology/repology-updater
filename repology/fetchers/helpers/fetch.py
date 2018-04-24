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

import requests

from repology.config import config

USER_AGENT = 'repology-fetcher/0 (+{}/bots)'.format(config['REPOLOGY_HOME'])


def Fetch(url, check_status=True, timeout=60, post=None, headers=None):
    headers = headers.copy() if headers else {}
    headers['User-Agent'] = USER_AGENT

    response = None
    if post:
        response = requests.post(url, headers=headers, timeout=timeout, data=post)
    else:
        response = requests.get(url, headers=headers, timeout=timeout)

    if check_status:
        response.raise_for_status()

    return response
