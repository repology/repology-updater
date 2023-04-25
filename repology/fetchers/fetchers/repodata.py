# Copyright (C) 2016-2019, 2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import xml.etree.ElementTree

from repology.atomic_fs import AtomicFile
from repology.fetchers import PersistentData, ScratchFileFetcher
from repology.fetchers.http import do_http, save_http_stream
from repology.logger import Logger


class RepodataFetcher(ScratchFileFetcher):
    primary_key = 'primary'

    def __init__(self, url: str, fetch_timeout: int = 60):
        super(RepodataFetcher, self).__init__(binary=True)

        self.url = url
        self.fetch_timeout = fetch_timeout

    def _do_fetch(self, statefile: AtomicFile, persdata: PersistentData, logger: Logger) -> bool:

        # if given url is a mirror.list, fetch the first baseurl
        if self.url.endswith('mirror.list'):
            baseurl = do_http(self.url, check_status=True, timeout=self.fetch_timeout).text.split()[0]
        else:
            baseurl = self.url

        if not baseurl.endswith('/'):
            baseurl = baseurl + '/'

        # fetch and parse repomd.xml
        repomd_url = baseurl + 'repodata/repomd.xml'
        logger.log('fetching metadata from ' + repomd_url)
        repomd_content = do_http(repomd_url, check_status=True, timeout=self.fetch_timeout).text
        repomd = xml.etree.ElementTree.fromstring(repomd_content)
        repomd_elt_primary = repomd.find('{{http://linux.duke.edu/metadata/repo}}data[@type="{}"]'.format(self.primary_key))
        if repomd_elt_primary is None:
            raise RuntimeError('Cannot find <{}> element in repomd.xml'.format(self.primary_key))

        repomd_elt_primary_location = repomd_elt_primary.find('./{http://linux.duke.edu/metadata/repo}location')

        checksum = None
        for checksum_type in ['sha256', 'sha512']:
            if (elt := repomd_elt_primary.find(f'./{{http://linux.duke.edu/metadata/repo}}open-checksum[@type="{checksum_type}"]')) is not None:
                checksum = elt.text
                break
        else:
            logger.log('no supported checksum', Logger.WARNING)

        if checksum == persdata.get('open-checksum'):
            logger.log('checksum not changed: {}'.format(checksum))
            return False

        if repomd_elt_primary_location is None:
            raise RuntimeError('Cannot find <location> element in repomd.xml')

        repodata_url = baseurl + repomd_elt_primary_location.attrib['href']

        # fetch actual repo data
        compression = None
        if repodata_url.endswith('gz'):
            compression = 'gz'
        elif repodata_url.endswith('xz'):
            compression = 'xz'
        elif repodata_url.endswith('bz2'):
            compression = 'bz2'

        logger.log('fetching {}'.format(repodata_url))

        save_http_stream(repodata_url, statefile.get_file(), compression=compression, timeout=self.fetch_timeout)

        if checksum:
            persdata['open-checksum'] = checksum
            logger.log('saving checksum: {}'.format(persdata['open-checksum']))

        logger.log('size is {} byte(s)'.format(os.path.getsize(statefile.get_path())))

        return True


class RepodataSqliteFetcher(RepodataFetcher):
    primary_key = 'primary_db'
