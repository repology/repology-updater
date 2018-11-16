# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import time
import functools

from json import dumps

import requests

from repology.config import config

USER_AGENT = 'repology-fetcher/0 (+{}/bots)'.format(config['REPOLOGY_HOME'])


class PoliteHTTP:
    def __init__(self, timeout=5, delay=None):
        self.do_http = functools.partial(do_http, timeout=timeout)
        self.delay = delay
        self.had_requests = False

    def __call__(self, *args, **kwargs):
        if self.had_requests and self.delay:
            time.sleep(self.delay)

        self.had_requests = True
        return self.do_http(*args, **kwargs)


# XXX: post argument is a compatibility shim
def do_http(url, method=None, check_status=True, timeout=5, data=None, json=None, post=None, headers=None):
    headers = headers.copy() if headers else {}
    headers['User-Agent'] = USER_AGENT

    if post and not data:
        data = post
    if json and not data:
        data = dumps(json)

    request = requests.get

    if method == 'POST' or (method is None and data):
        request = requests.post
    elif method == 'DELETE':
        request = requests.delete
    elif method == 'PUT':
        request = requests.put

    response = request(url, headers=headers, timeout=timeout, data=data)

    if check_status:
        response.raise_for_status()

    return response
