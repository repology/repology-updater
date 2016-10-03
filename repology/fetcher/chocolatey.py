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
import requests
import xml.etree.ElementTree
import shutil

from repology.logger import NoopLogger

USER_AGENT = "Repology/0"

class ChocolateyFetcher():
    def __init__(self, apiurl):
        self.apiurl = apiurl

    def Fetch(self, statepath, update = True, logger = NoopLogger()):
        if os.path.isdir(statepath) and not update:
            return

        if os.path.isdir(statepath):
            shutil.rmtree(statepath)

        os.mkdir(statepath)

        numpage = 0
        nextpageurl = self.apiurl + "Packages()?$filter=IsLatestVersion"
        while True:
            logger.Log("getting " + nextpageurl);
            r = requests.get(nextpageurl, headers = { 'user-agent': USER_AGENT })
            r.raise_for_status()

            with open(os.path.join(statepath, "{}.xml".format(numpage)), "w") as pagefile:
                pagefile.write(r.text)

            # parse next page
            logger.Log("parsing " + nextpageurl);
            root = xml.etree.ElementTree.fromstring(r.text)

            for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                title = entry.find("{http://www.w3.org/2005/Atom}title")

            next_link = root.find("{http://www.w3.org/2005/Atom}link[@rel='next']")
            if next_link is None:
                break

            nextpageurl = next_link.attrib['href']
            numpage += 1
