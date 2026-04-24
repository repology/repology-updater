# Copyright (C) 2024 Repology contributors
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
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from repology.atomic_fs import AtomicFile
from repology.fetchers import PersistentData, ScratchFileFetcher
from repology.fetchers.http import do_http
from repology.logger import Logger

_BASE_URL = 'https://xmake.microblock.cc'

_HOMEPAGE_RE = re.compile(r'set_homepage\s*\(\s*["\']([^"\']+)["\']\s*\)')
_ARCHIVE_EXTS = ('.tar.gz', '.tar.bz2', '.tar.xz', '.tgz', '.zip', '.tar.lz', '.tar.zst', '.7z')


def _extract_urls_from_block(block: str) -> list[str]:
    return re.findall(r'"(https?://[^"]+)"', block)


def _extract_url_call_blocks(content: str) -> list[str]:
    """Return the argument-list text of every set_urls/add_urls call."""
    blocks = []
    for m in re.finditer(r'(?:set|add)_urls\s*\(', content):
        start = m.end()
        depth = 1
        i = start
        while i < len(content) and depth > 0:
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
            i += 1
        blocks.append(content[start:i - 1])
    return blocks


def _parse_xmake_lua(content: str) -> dict[str, Any]:
    result: dict[str, Any] = {}

    m = _HOMEPAGE_RE.search(content)
    if m:
        result['homepage'] = m.group(1)

    download_templates: list[str] = []
    download_direct: list[str] = []
    repo_urls: list[str] = []

    for block in _extract_url_call_blocks(content):
        for url in _extract_urls_from_block(block):
            if url.endswith('.git'):
                repo_urls.append(url)
            elif '$(version)' in url:
                download_templates.append(url)
            elif any(url.endswith(ext) or ('.' + ext.lstrip('.')) in url for ext in _ARCHIVE_EXTS):
                download_direct.append(url)
            # else: bare repo-like URL without .git — skip; not a reliable download URL

    if download_templates:
        result['download_templates'] = download_templates
    if download_direct:
        result['download_direct'] = download_direct
    if repo_urls:
        result['repo_urls'] = repo_urls

    return result


def _fetch_lua_data(packagefile: str) -> dict[str, Any]:
    try:
        response = do_http(f'{_BASE_URL}/xmake-repo-raw/{packagefile}', timeout=30)
        return _parse_xmake_lua(response.text)
    except Exception:
        return {}


class XrepoFetcher(ScratchFileFetcher):
    def __init__(self, max_workers: int = 20) -> None:
        super().__init__(binary=False)
        self.max_workers = max_workers

    def _do_fetch(self, statefile: AtomicFile, persdata: PersistentData, logger: Logger) -> bool:
        logger.log(f'fetching {_BASE_URL}/api/packages')
        response = do_http(f'{_BASE_URL}/api/packages', timeout=60)
        data: dict[str, Any] = response.json()

        packages_with_file = [(name, pkg['packagefile']) for name, pkg in data.items() if pkg.get('packagefile')]
        logger.log(f'fetching xmake.lua data for {len(packages_with_file)} packages')

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(_fetch_lua_data, packagefile): name for name, packagefile in packages_with_file}
            for future in as_completed(futures):
                name = futures[future]
                lua_data = future.result()
                data[name].update(lua_data)

        statefile.get_file().write(json.dumps(data))
        return True
