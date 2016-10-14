# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import shutil

from repology.logger import NoopLogger
from repology.www import Get
from repology.fetcher.file import FileFetcher


class OpenSUSERepodataFetcher():
    def __init__(self, repourl):
        self.repourl = repourl
        pass

    def DoFetch(self, statepath, logger):
        root = xml.etree.ElementTree.fromstring(Get(self.url + "repodata/repomd.xml", check_status = True).text)
        location = root.find("{http://linux.duke.edu/metadata/repo}data[@type='primary']/{http://linux.duke.edu/metadata/repo}location")
        return FileFetcher(location)

    def Fetch(self, statepath, update=True, logger=NoopLogger()):
        if os.path.isfile(statepath) and not update:
            logger.Log("no update requested, skipping")
            return

        # Get and parse repomd.xml
        repomd_url = self.repourl + "repodata/repomd.xml"
        logger.Log("fetching metadata from " + repomd_url)
        repomd_content = Get(repomd_url, check_status = True).text
        repomd_xml = xml.etree.ElementTree.fromstring(repomd_content)

        repodata_url = self.repourl + repomd_xml.find("{http://linux.duke.edu/metadata/repo}data[@type='primary']/{http://linux.duke.edu/metadata/repo}location").attrib['href']
        return FileFetcher(repodata_url, gz=True).Fetch(statepath, update, logger)
