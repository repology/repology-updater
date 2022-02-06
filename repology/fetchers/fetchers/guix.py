# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from string import ascii_uppercase

import lxml.html

from repology.atomic_fs import AtomicDir
from repology.fetchers import PersistentData, ScratchDirFetcher
from repology.fetchers.http import PoliteHTTP
from repology.logger import Logger


class GuixFetcher(ScratchDirFetcher):
    def __init__(self, url: str, fetch_timeout: int = 5, fetch_delay: int | None = None) -> None:
        self.url = url
        self.do_http = PoliteHTTP(timeout=fetch_timeout, delay=fetch_delay)

    def _do_fetch(self, statedir: AtomicDir, persdata: PersistentData, logger: Logger) -> bool:
        for letter in ['0-9'] + list(ascii_uppercase):
            page = 1
            numpages = 1
            while True:
                logger.log('fetching {} page {}'.format(letter, page))

                pageurl = '{}/{}/page/{}/'.format(self.url, letter, page)

                # fetch HTML
                response = self.do_http(pageurl)
                response.encoding = 'utf-8'  # is not detected properly
                text = response.text

                # get number of pages, if there are more than 1 of them
                if numpages == 1:
                    for pagebutton in lxml.html.document_fromstring(text).xpath('.//nav[@class="page-selector"]/a'):  # type: ignore
                        numpages = max(numpages, int(pagebutton.text))  # type: ignore

                # save HTML
                with open(os.path.join(statedir.get_path(), '{}-{}.html'.format(letter, page)), 'w', encoding='utf-8') as pagefile:
                    pagefile.write(text)
                    pagefile.flush()
                    os.fsync(pagefile.fileno())

                # end if that was last (or only) page
                if page >= numpages:
                    break

                # proceed with the next page
                page += 1

        return True
