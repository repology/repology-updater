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

import json
import os
from typing import Any

import requests

from repology.atomic_fs import AtomicDir
from repology.fetchers import PersistentData, ScratchDirFetcher
from repology.fetchers.http import PoliteHTTP
from repology.logger import Logger


class ElasticSearchFetcher(ScratchDirFetcher):
    _url: str
    _scroll_url: str | None
    _scroll: str | None
    _request_data: dict[str, Any]
    _do_http: PoliteHTTP

    def __init__(self, url: str, scroll_url: str | None = None, es_query: str | None = None, es_filter: str | None = None, es_fields: str | None = None, es_size: int = 5000, es_scroll: str = '1m', fetch_timeout: int = 5, fetch_delay: int | None = None):
        self._url = url
        self._scroll_url = scroll_url
        self._scroll = es_scroll

        self._request_data = {}
        if es_fields:
            self._request_data['fields'] = es_fields
        if es_query:
            self._request_data['query'] = es_query
        if es_filter:
            self._request_data['filter'] = es_filter
        if es_size:
            self._request_data['size'] = es_size

        self._do_http = PoliteHTTP(timeout=fetch_timeout, delay=fetch_delay)

    def _do_fetch_scroll(self, statedir: AtomicDir, logger: Logger) -> None:
        numpage = 0

        logger.log('getting page {}'.format(numpage))
        response = self._do_http('{}?scroll={}'.format(self._url, self._scroll), json=self._request_data).json()

        scroll_id = response['_scroll_id']

        while response['hits']['hits']:
            with open(os.path.join(statedir.get_path(), '{}.json'.format(numpage)), 'w', encoding='utf-8') as pagefile:
                json.dump(response['hits']['hits'], pagefile)
                pagefile.flush()
                os.fsync(pagefile.fileno())

            numpage += 1

            logger.log('getting page {}'.format(numpage))
            response = self._do_http('{}?scroll={}&scroll_id={}'.format(self._scroll_url, self._scroll, scroll_id)).json()

        try:
            self._do_http(self._scroll_url, method='DELETE', json={'scroll_id': scroll_id}).json()
        except requests.exceptions.HTTPError as e:
            # we don't care too much if removing the scroll fails, it'll timeout anyway
            logger.log(f'failed to DELETE scroll{": " + e.response.text if e.response else ""}', severity=Logger.ERROR)

    def _do_fetch(self, statedir: AtomicDir, persdata: PersistentData, logger: Logger) -> bool:
        try:
            self._do_fetch_scroll(statedir, logger)
        except requests.exceptions.HTTPError as e:
            # show server reply as it contains the failure cause
            logger.log(f'request failed{": " + e.response.text if e.response else ""}', severity=Logger.ERROR)
            raise

        return True
