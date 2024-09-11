# Copyright (C) 2024 Gavin John <gavinnjohn@gmail.com>
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

from repology.atomic_fs import AtomicFile
from repology.fetchers import PersistentData, ScratchFileFetcher
from repology.fetchers.http import PoliteHTTP
from repology.logger import Logger


class VSCMarketplaceFetcher(ScratchFileFetcher):
    def __init__(self, page_size: int = 100, fetch_timeout: int = 5, fetch_delay: int | None = None) -> None:
        self.do_http = PoliteHTTP(timeout=fetch_timeout, delay=fetch_delay)

        self.page_size = page_size

        # Constants
        self.include_versions = True
        self.include_files = True
        self.include_category_and_tags = False
        self.include_shared_accounts = True
        self.include_version_properties = True
        self.exclude_non_validated = False
        self.include_installation_targets = False
        self.include_asset_uri = True
        self.include_statistics = False
        self.include_latest_version_only = True
        self.unpublished = False
        self.include_name_conflict_info = True
        self.api_version = '7.2-preview.1',

    def _do_fetch(self, statefile: AtomicFile, persdata: PersistentData, logger: Logger) -> bool:
        extensions = []

        flags = 0
        if self.include_versions:
            flags |= 0x1

        if self.include_files:
            flags |= 0x2

        if self.include_category_and_tags:
            flags |= 0x4

        if self.include_shared_accounts:
            flags |= 0x8

        if self.include_version_properties:
            flags |= 0x10

        if self.exclude_non_validated:
            flags |= 0x20

        if self.include_installation_targets:
            flags |= 0x40

        if self.include_asset_uri:
            flags |= 0x80

        if self.include_statistics:
            flags |= 0x100

        if self.include_latest_version_only:
            flags |= 0x200

        if self.unpublished:
            flags |= 0x1000

        if self.include_name_conflict_info:
            flags |= 0x8000

        page = 1
        while True:
            body = {
                'filters': [
                    {
                        'criteria': [
                            {
                                'filterType': 8,
                                'value': 'Microsoft.VisualStudio.Code'
                            }
                        ],
                        'pageNumber': page,
                        'pageSize': self.page_size,
                        'sortBy': 0,
                        'sortOrder': 0
                    }
                ],
                'assetTypes': [],
                'flags': flags
            }

            r = self.do_http('https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery?api-version={version}'.format(version=self.api_version), 'POST', json=body)
            response = r.json()

            for extension in response['results'][0]['extensions']:
                extensions.append(extension)

            page += 1

            if len(response['results'][0]['extensions']) < self.page_size:
                break

        with open(statefile.get_path(), 'w', encoding='utf-8') as extdata:
            json.dump(extensions, extdata)

        return True
