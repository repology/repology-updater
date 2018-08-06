# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import functools
import json
import os
import time

import requests

from repology.fetchers import ScratchDirFetcher
from repology.fetchers.fetch import do_http
from repology.logger import Logger


class ElasticSearchFetcher(ScratchDirFetcher):
    def __init__(self, url, scroll_url=None, es_query=None, es_filter=None, es_fields=None, es_size=5000, es_scroll='1m', fetch_timeout=5, fetch_delay=None):
        self.url = url
        self.scroll_url = scroll_url
        self.scroll = es_scroll

        self.request_data = {}
        if es_fields:
            self.request_data['fields'] = es_fields
        if es_query:
            self.request_data['query'] = es_query
        if es_filter:
            self.request_data['filter'] = es_filter
        if es_size:
            self.request_data['size'] = es_size

        self.do_http = functools.partial(do_http, timeout=fetch_timeout)
        self.do_delay = functools.partial(time.sleep, fetch_delay) if fetch_delay else lambda: None

    def do_fetch_scroll(self, statedir, logger):
        numpage = 0

        logger.log('getting page {}'.format(numpage))
        response = self.do_http('{}?scroll={}'.format(self.url, self.scroll), json=self.request_data).json()

        scroll_id = response['_scroll_id']

        while response['hits']['hits']:
            with open(os.path.join(statedir, '{}.json'.format(numpage)), 'w', encoding='utf-8') as pagefile:
                json.dump(response['hits']['hits'], pagefile)

            self.do_delay()

            numpage += 1

            logger.log('getting page {}'.format(numpage))
            response = self.do_http('{}?scroll={}&scroll_id={}'.format(self.scroll_url, self.scroll, scroll_id)).json()

        try:
            self.do_http(self.scroll_url, method='DELETE', json={'scroll_id': scroll_id}).json()
        except requests.exceptions.HTTPError as e:
            # we don't care too much if removing the scroll fails, it'll timeout anyway
            # XXX: but log this
            logger.log('failed to DELETE scroll, server reply follows:'.format(e.response.text), severity=Logger.ERROR)
            logger.log(e.response.text, severity=Logger.ERROR)
            pass

    def do_fetch(self, statedir, logger):
        try:
            self.do_fetch_scroll(statedir, logger)
        except requests.exceptions.HTTPError as e:
            # show server reply as it contains the failure cause
            logger.log('request failed, server reply follows:'.format(e.response.text), severity=Logger.ERROR)
            logger.log(e.response.text, serverity=Logger.ERROR)
            raise
