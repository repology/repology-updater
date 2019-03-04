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

import xml.etree.ElementTree

from repology.fetchers import ScratchFileFetcher
from repology.fetchers.http import do_http, save_http_stream


class RepodataFetcher(ScratchFileFetcher):
    def __init__(self, url, fetch_timeout=60):
        super(RepodataFetcher, self).__init__(binary=True)

        self.url = url
        self.fetch_timeout = fetch_timeout

    def _do_fetch(self, statefile, logger) -> bool:
        # fetch and parse repomd.xml
        repomd_url = self.url + 'repodata/repomd.xml'
        logger.Log('fetching metadata from ' + repomd_url)
        repomd_content = do_http(repomd_url, check_status=True, timeout=self.fetch_timeout).text
        repomd_xml = xml.etree.ElementTree.fromstring(repomd_content)
        repomd_xml_primary_location = repomd_xml.find('{http://linux.duke.edu/metadata/repo}data[@type="primary"]/{http://linux.duke.edu/metadata/repo}location')

        if repomd_xml_primary_location is None:
            raise RuntimeError('Cannot find primary data location in repomd.xml')

        repodata_url = self.url + repomd_xml_primary_location.attrib['href']

        # fetch actual repo data
        compression = None
        if repodata_url.endswith('gz'):
            compression = 'gz'
        elif repodata_url.endswith('xz'):
            compression = 'xz'

        logger.Log('fetching {}'.format(repodata_url))

        save_http_stream(repodata_url, statefile, compression=compression, timeout=self.fetch_timeout)

        logger.Log('size is {} byte(s)'.format(statefile.tell()))

        return True
