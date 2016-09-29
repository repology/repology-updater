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
import json
import sys
import shutil

USER_AGENT = "Repology/0"

def GetJson(url):
    r = requests.get(url, headers = { 'user-agent': USER_AGENT })
    r.raise_for_status()
    return json.loads(r.text)

def LoadSpec(package, statepath, verbose):
    url = "http://pkgs.fedoraproject.org/cgit/rpms/%s.git/plain/%s.spec" % (package, package)

    r = requests.get(url, headers = { 'user-agent': USER_AGENT } )
    if r.status_code != 200:
        print("        failed", file=sys.stderr)
        return

    with open(os.path.join(statepath, package + ".spec"), "wb") as file:
        file.write(r.content)

def ParsePackages(statepath, verbose):
    page = 1

    while True:
        if verbose:
            print("Page %d" % page, file=sys.stderr)
        json = GetJson("https://admin.fedoraproject.org/pkgdb/api/packages/?page=%d" % page)

        for package in json['packages']:
            if verbose:
                print("    Package %s" % package['name'], file=sys.stderr)
            LoadSpec(package['name'], statepath, verbose)

        page += 1

        if page > json['page_total']:
            break

class FedoraFetcher():
    def __init__(self):
        pass

    def Fetch(self, statepath, update = True, verbose = False):
        if os.path.isdir(statepath) and not update:
            return

        if os.path.isdir(statepath):
            shutil.rmtree(statepath)

        os.mkdir(statepath)

        try:
            ParsePackages(statepath, verbose)
        except:
            # don't leave partial state
            shutil.rmtree(statepath)
            raise
